"""Bounded Linux serving-load measurements; no training or quality qualification.

Run on the serving host. Raw evidence stays in a fresh operator-selected directory.
Unified host, RSS, cgroup and GPU counters overlap and are never added together.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import threading
import time
from urllib import error, parse, request


def encode(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def command(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, timeout=10, stderr=subprocess.DEVNULL)


def validate_config(config: dict) -> None:
    required = {'baseUrl', 'model', 'credentialFile', 'credentialVariable', 'container',
                'workloadFile', 'artifactManifest', 'concurrency', 'rounds', 'maxTokens',
                'temperature', 'requestTimeoutSeconds', 'maximumDurationSeconds',
                'sampleIntervalSeconds', 'minimumAvailableBytes', 'maximumTemperatureC'}
    if set(config) != required:
        raise ValueError('Explicit serving binding, workload and resource bounds required')
    url = parse.urlsplit(config['baseUrl'])
    if (url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost', '::1')
            or url.username or url.password or url.query or url.fragment or url.path.rstrip('/') not in ('', '/v1')):
        raise ValueError('Host-local HTTP endpoint required; do not send credentials remotely')
    for key in ('model', 'credentialFile', 'credentialVariable', 'container', 'workloadFile', 'artifactManifest'):
        if not isinstance(config[key], str) or not config[key].strip():
            raise ValueError('Nonempty explicit configuration required')
    for key in ('rounds', 'maxTokens', 'minimumAvailableBytes'):
        if type(config[key]) is not int or config[key] <= 0:
            raise ValueError('Positive integer bound required')
    if (not isinstance(config['concurrency'], list) or not config['concurrency']
            or len(set(config['concurrency'])) != len(config['concurrency'])
            or any(type(value) is not int or not 1 <= value <= 64 for value in config['concurrency'])):
        raise ValueError('Concurrency must contain distinct integers in [1,64]')
    for key in ('temperature', 'requestTimeoutSeconds', 'maximumDurationSeconds',
                'sampleIntervalSeconds', 'maximumTemperatureC'):
        if type(config[key]) not in (int, float) or not math.isfinite(config[key]):
            raise ValueError('Finite resource bound required')
    if (not 0 <= config['temperature'] <= 2 or min(config[key] for key in
            ('requestTimeoutSeconds', 'maximumDurationSeconds', 'sampleIntervalSeconds', 'maximumTemperatureC')) <= 0):
        raise ValueError('Invalid resource bound')


def read_workload(path: Path) -> tuple[list[dict], bytes]:
    content = path.read_bytes()
    rows = [json.loads(line) for line in content.splitlines() if line.strip()]
    if not rows or not content.endswith(b'\n'):
        raise ValueError('Complete, nonempty workload JSONL required')
    ids = set()
    for row in rows:
        if set(row) != {'id', 'sourceReference', 'sourceSha256', 'messages'}:
            raise ValueError('Workload must contain source-bound inputs only, never outcome labels')
        if any(not isinstance(row[key], str) or not row[key].strip() for key in ('id', 'sourceReference', 'sourceSha256')):
            raise ValueError('Workload provenance missing')
        if len(row['sourceSha256']) != 64 or any(char not in '0123456789abcdef' for char in row['sourceSha256']):
            raise ValueError('Invalid source digest')
        if row['id'] in ids:
            raise ValueError('Duplicate workload identity')
        ids.add(row['id'])
        messages = row['messages']
        if (not isinstance(messages, list) or not messages or not any(item.get('role') == 'user' for item in messages)
                or any(set(item) != {'role', 'content'} or item['role'] not in ('system', 'user')
                       or not isinstance(item['content'], str) or not item['content'].strip() for item in messages)):
            raise ValueError('Workload permits system/user inputs only')
    return rows, content


def proc_memory(text: str) -> dict:
    result = {}
    for line in text.splitlines():
        key, _, value = line.partition(':')
        if key in {'MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree', 'VmRSS', 'VmSwap'}:
            parts = value.split()
            result[key + 'Bytes'] = int(parts[0]) * (1024 if len(parts) > 1 and parts[1] == 'kB' else 1)
    return result


def snapshot(container: str) -> dict:
    info = json.loads(command(['docker', 'inspect', container]))[0]
    if not info['State']['Running']:
        raise ValueError('Serving container stopped')
    pids = [int(line.strip()) for line in command(['docker', 'top', container, '-eo', 'pid']).splitlines()[1:]]
    processes = []
    for pid in pids:
        try:
            processes.append({'pid': pid, **proc_memory(Path(f'/proc/{pid}/status').read_text())})
        except OSError:
            processes.append({'pid': pid, 'unavailable': True})
    gpu_text = command(['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu,power.draw', '--format=csv,noheader,nounits'])
    gpus = []
    for line in gpu_text.splitlines():
        values = line.split(',')
        gpus.append({key: float(value.strip()) if value.strip().replace('.', '', 1).isdigit() else None
                     for key, value in zip(('utilizationPercent', 'temperatureC', 'powerW'), values)})
    gpu_processes = []
    for line in command(['nvidia-smi', '--query-compute-apps=pid,used_gpu_memory', '--format=csv,noheader,nounits']).splitlines():
        pid, memory = [value.strip() for value in line.split(',', 1)]
        gpu_processes.append({'pid': int(pid), 'owned': int(pid) in pids,
                              'reportedBytes': int(memory) * 1024 * 1024 if memory.isdigit() else None})
    cgroup_memory = None
    try:
        cgroup = next(line.split(':', 2)[2] for line in Path(f"/proc/{info['State']['Pid']}/cgroup").read_text().splitlines()
                      if line.startswith('0::'))
        cgroup_memory = int((Path('/sys/fs/cgroup') / cgroup.lstrip('/') / 'memory.current').read_text())
    except (OSError, ValueError, StopIteration):
        pass
    arguments = info['Config'].get('Cmd') or []
    runtime = {}
    for index, value in enumerate(arguments):
        if value in ('--max-model-len', '--max-num-seqs', '--kv-cache-memory-bytes', '--dtype', '--gpu-memory-utilization') and index + 1 < len(arguments):
            runtime[value.removeprefix('--')] = arguments[index + 1]
    runtime['enforce-eager'] = '--enforce-eager' in arguments
    return {'observedAt': datetime.now(timezone.utc).isoformat(), 'monotonicSeconds': time.monotonic(),
            'containerId': info['Id'], 'imageId': info['Image'], 'processes': processes,
            'containerStartedAt': info['State']['StartedAt'], 'runtimeConfiguration': runtime,
            'host': proc_memory(Path('/proc/meminfo').read_text()), 'gpu': gpus,
            'gpuProcesses': gpu_processes, 'cgroupMemoryBytes': cgroup_memory,
            'totalServingBytes': None, 'totalServingMemoryVerified': False}


def stop_reason(sample: dict, config: dict) -> str | None:
    available = sample['host'].get('MemAvailableBytes')
    if available is None or available < config['minimumAvailableBytes']:
        return 'available_memory_limit'
    if not sample['gpu'] or any(row['temperatureC'] is None for row in sample['gpu']):
        return 'temperature_unavailable'
    if any(row['temperatureC'] >= config['maximumTemperatureC'] for row in sample['gpu']):
        return 'temperature_limit'
    return None


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def percentile(values: list[float], fraction: float) -> float | None:
    return sorted(values)[math.ceil(len(values) * fraction) - 1] if values else None


def phase_summary(rows: list[dict], concurrency: int, elapsed: float) -> dict:
    completed = [row for row in rows if row.get('httpStatus') == 200 and not row.get('errorClass')]
    durations = [row['elapsedSeconds'] for row in rows if 'elapsedSeconds' in row]
    return {'clientConcurrency': concurrency, 'attempted': len(durations), 'completed': len(completed),
            'notDispatched': sum('elapsedSeconds' not in row for row in rows),
            'errors': sum(bool(row.get('errorClass')) for row in rows), 'elapsedSeconds': elapsed,
            'completedRequestsPerSecond': len(completed) / elapsed if elapsed else None,
            'p50Seconds': percentile(durations, .5), 'p95Seconds': percentile(durations, .95),
            'p99Seconds': percentile(durations, .99),
            'qualityEvaluated': False}


def run(config_path: Path, output: Path) -> dict:
    raw_config = config_path.read_bytes()
    config = json.loads(raw_config)
    validate_config(config)
    def selected(key):
        value = Path(config[key])
        return value if value.is_absolute() else config_path.resolve().parent / value
    workload, workload_bytes = read_workload(selected('workloadFile'))
    manifest_bytes = selected('artifactManifest').read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get('model') != config['model']:
        raise ValueError('Model alias must match the declared artifact manifest')
    keys = [line.split('=', 1)[1].strip() for line in selected('credentialFile').read_text().splitlines()
            if line.startswith(config['credentialVariable'] + '=')]
    if len(keys) != 1 or not keys[0]:
        raise ValueError('Explicit credential missing or ambiguous')
    initial = snapshot(config['container'])
    reason = stop_reason(initial, config)
    if reason:
        raise ValueError(reason)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'workload.jsonl').write_bytes(workload_bytes)
    (output / 'artifact-manifest.json').write_bytes(manifest_bytes)
    safe_config = {key: value for key, value in config.items() if key not in
                   ('baseUrl', 'credentialFile', 'credentialVariable', 'container', 'workloadFile', 'artifactManifest')}
    protocol = {'kind': 'swag.serving_load', 'schemaVersion': 1, 'configuration': safe_config,
                'configurationSha256': sha(raw_config), 'workloadSha256': sha(workload_bytes),
                'artifactManifestSha256': sha(manifest_bytes), 'implementationSha256': sha(Path(__file__).read_bytes()),
                'qualityEvaluated': False, 'trainingPerformed': False, 'deploymentQualified': False}
    (output / 'protocol.json').write_bytes(encode(protocol) + b'\n')
    stopped, sampling_done = threading.Event(), threading.Event()
    reasons = []
    start = time.monotonic()
    def monitor():
        with (output / 'samples.jsonl').open('xb') as stream:
            sample = initial
            while True:
                stream.write(encode(sample) + b'\n')
                stream.flush()
                reason = stop_reason(sample, config)
                if reason or (sample['containerId'], sample['containerStartedAt']) != (initial['containerId'], initial['containerStartedAt']):
                    reasons.append(reason or 'container_changed')
                    stopped.set()
                if sampling_done.wait(config['sampleIntervalSeconds']):
                    break
                try:
                    sample = snapshot(config['container'])
                except Exception as exc:
                    reasons.append(type(exc).__name__)
                    stopped.set()
                    break
    sampling = threading.Thread(target=monitor, daemon=True)
    sampling.start()
    url = config['baseUrl'].rstrip('/') + ('/chat/completions' if config['baseUrl'].rstrip('/').endswith('/v1') else '/v1/chat/completions')
    def invoke(item):
        case, repeat = item
        row = {'caseId': case['id'], 'repeat': repeat, 'requestSha256': sha(encode(case['messages']))}
        if stopped.is_set() or time.monotonic() - start >= config['maximumDurationSeconds']:
            stopped.set()
            return {**row, 'notDispatched': True}
        began = time.monotonic()
        payload = {'model': config['model'], 'messages': case['messages'],
                   'temperature': config['temperature'], 'max_tokens': config['maxTokens']}
        req = request.Request(url, data=encode(payload), headers={'Authorization': 'Bearer ' + keys[0], 'Content-Type': 'application/json'})
        try:
            opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
            with opener.open(req, timeout=config['requestTimeoutSeconds']) as response:
                raw = response.read(1_000_001)
                row['httpStatus'] = response.status
            if len(raw) > 1_000_000:
                raise ValueError('Oversized response')
            body = json.loads(raw)
            row.update(responseSha256=sha(raw), servedModel=body.get('model'), usage=body.get('usage'),
                       rawOutput=body['choices'][0]['message']['content'])
            if row['servedModel'] != config['model'] or not isinstance(row['rawOutput'], str):
                raise ValueError('Served model or output mismatch')
        except error.HTTPError as exc:
            row.update(errorClass='HTTPError', httpStatus=exc.code)
            exc.close()
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            row['errorClass'] = type(exc).__name__
        row['elapsedSeconds'] = time.monotonic() - began
        return row
    phases = []
    try:
        with (output / 'requests.jsonl').open('xb') as stream:
            for concurrency in config['concurrency']:
                if stopped.is_set():
                    break
                began = time.monotonic()
                rows = []
                items = [(case, repeat) for repeat in range(config['rounds']) for case in workload]
                with ThreadPoolExecutor(max_workers=concurrency) as pool:
                    for row in pool.map(invoke, items):
                        rows.append(row)
                        stream.write(encode({**row, 'clientConcurrency': concurrency}) + b'\n')
                        stream.flush()
                phases.append(phase_summary(rows, concurrency, time.monotonic() - began))
                print(json.dumps(phases[-1]), flush=True)
    finally:
        sampling_done.set()
        sampling.join(timeout=60)
        if sampling.is_alive():
            raise RuntimeError('Sampler did not stop; no completed summary')
    summary = {**protocol, 'phases': phases, 'stoppedEarly': stopped.is_set(), 'stopReasons': reasons,
               'totalServingBytes': None, 'totalServingMemoryVerified': False,
               'samplesSha256': sha((output / 'samples.jsonl').read_bytes()),
               'requestsSha256': sha((output / 'requests.jsonl').read_bytes()),
               'samplingNote': 'Overlapping unified-memory counters; no total computed.'}
    (output / 'summary.json').write_bytes(encode(summary) + b'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    arguments = parser.parse_args()
    result = run(arguments.config, arguments.output_dir)
    raise SystemExit(1 if result['stoppedEarly'] or any(phase['errors'] for phase in result['phases']) else 0)
