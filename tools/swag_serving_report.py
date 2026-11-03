"""Recompute a content-free serving report from retained load observations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from swag_serving_load import encode, phase_summary, read_workload, sha


def report(directory: Path) -> tuple[dict, dict]:
    summary = json.loads((directory / 'summary.json').read_bytes())
    protocol = json.loads((directory / 'protocol.json').read_bytes())
    if (protocol.get('kind') != 'swag.serving_load' or summary.get('qualityEvaluated') is not False
            or summary.get('trainingPerformed') is not False or summary.get('deploymentQualified') is not False
            or summary.get('totalServingMemoryVerified') is not False or summary.get('totalServingBytes') is not None):
        raise ValueError('Load observations cannot claim quality, training, total memory or deployment')
    if any(summary.get(key) != value for key, value in protocol.items()):
        raise ValueError('Summary and protocol disagree')
    rows = {}
    for filename, key in [('samples.jsonl', 'samplesSha256'), ('requests.jsonl', 'requestsSha256')]:
        data = (directory / filename).read_bytes()
        if sha(data) != summary[key] or not data.endswith(b'\n'):
            raise ValueError('Observation stream changed or is incomplete')
        rows[filename] = [json.loads(line) for line in data.splitlines()]
    samples, requests = rows['samples.jsonl'], rows['requests.jsonl']
    if not samples or not requests:
        raise ValueError('Nonempty retained observation streams required')
    if sha((directory / 'workload.jsonl').read_bytes()) != summary['workloadSha256']:
        raise ValueError('Workload changed')
    if sha((directory / 'artifact-manifest.json').read_bytes()) != summary['artifactManifestSha256']:
        raise ValueError('Declared artifact changed')
    if len({(sample['containerId'], sample['containerStartedAt'], sample['imageId']) for sample in samples}) != 1:
        raise ValueError('Serving process identity changed during run')
    if any(sample['runtimeConfiguration'] != samples[0]['runtimeConfiguration'] for sample in samples):
        raise ValueError('Runtime configuration changed during run')
    request_map = {(row['caseId'], row['repeat'], row['clientConcurrency']): row for row in requests}
    if len(request_map) != len(requests):
        raise ValueError('Duplicate request identity')
    workload, _ = read_workload(directory / 'workload.jsonl')
    input_hashes = {row['id']: sha(encode(row['messages'])) for row in workload}
    configuration = protocol['configuration']
    for row in requests:
        if (row['caseId'] not in input_hashes or row['requestSha256'] != input_hashes[row['caseId']]
                or type(row['repeat']) is not int or not 0 <= row['repeat'] < configuration['rounds']
                or row['clientConcurrency'] not in configuration['concurrency']):
            raise ValueError('Request does not match the frozen workload')
    if not summary['stoppedEarly']:
        expected = {(case_id, repeat, concurrency) for case_id in input_hashes
                    for repeat in range(configuration['rounds']) for concurrency in configuration['concurrency']}
        if set(request_map) != expected:
            raise ValueError('Completed run omitted planned requests')
    for phase in summary['phases']:
        selected = [row for row in requests if row['clientConcurrency'] == phase['clientConcurrency']]
        if phase_summary(selected, phase['clientConcurrency'], phase['elapsedSeconds']) != phase:
            raise ValueError('Phase metrics do not match original request observations')
    if {row['clientConcurrency'] for row in requests} != {phase['clientConcurrency'] for phase in summary['phases']}:
        raise ValueError('Requests omitted from phases')
    gpu = [row for sample in samples for row in sample['gpu']]
    memory = [row['reportedBytes'] for sample in samples for row in sample['gpuProcesses']
              if row['owned'] and row['reportedBytes'] is not None]
    cgroups = [sample['cgroupMemoryBytes'] for sample in samples if sample['cgroupMemoryBytes'] is not None]
    output = {
        'phases': summary['phases'], 'samples': len(samples), 'requests': len(requests),
        'protocolSha256': sha((directory / 'protocol.json').read_bytes()),
        'summarySha256': sha((directory / 'summary.json').read_bytes()),
        'workloadSha256': summary['workloadSha256'], 'implementationSha256': summary['implementationSha256'],
        'artifactManifestSha256': summary['artifactManifestSha256'], 'runtimeImageId': samples[0]['imageId'],
        'generation': {key: configuration[key] for key in ('model', 'temperature', 'maxTokens')},
        'runtimeConfiguration': samples[0]['runtimeConfiguration'], 'stoppedEarly': summary['stoppedEarly'],
        'maximumGpuUtilizationPercent': max((row['utilizationPercent'] for row in gpu if row['utilizationPercent'] is not None), default=None),
        'maximumTemperatureC': max((row['temperatureC'] for row in gpu if row['temperatureC'] is not None), default=None),
        'minimumHostAvailableBytes': min(sample['host']['MemAvailableBytes'] for sample in samples),
        'largestOwnedProcessGpuReportedBytes': max(memory, default=None),
        'maximumCgroupMemoryBytes': max(cgroups, default=None),
        'qualityEvaluated': False, 'totalServingBytes': None, 'totalServingMemoryVerified': False,
    }
    return output, request_map


def compare(baseline: Path, candidate: Path | None = None) -> dict:
    first, first_requests = report(baseline)
    result = {'schemaVersion': 1, 'scope': 'observed_serving_load_only',
              'profiles': {'baseline': first}, 'comparison': None,
              'deploymentQualified': False, 'trainingPerformed': False}
    if candidate is not None:
        second, second_requests = report(candidate)
        if (set(first_requests) != set(second_requests) or any(first[key] != second[key] for key in
                ('workloadSha256', 'artifactManifestSha256', 'implementationSha256', 'runtimeImageId', 'generation'))):
            raise ValueError('Profiles do not share request, artifact, implementation and runtime identities')
        agreed, comparable = 0, 0
        for key, row in first_requests.items():
            other = second_requests[key]
            if row['requestSha256'] != other['requestSha256']:
                raise ValueError('Paired request content differs')
            try:
                a, b = json.loads(row['rawOutput']), json.loads(other['rawOutput'])
                comparable += 1
                agreed += a == b
            except (KeyError, TypeError, ValueError):
                pass
        result['profiles']['candidate'] = second
        result['comparison'] = {'matchedAttempts': len(first_requests), 'jsonComparableAttempts': comparable,
                                'sameParsedOutput': agreed, 'outputAgreement': agreed / len(first_requests),
                                'qualityEquivalenceEstablished': False}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.baseline, args.candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(encode(result) + b'\n')
    print(json.dumps({'profiles': list(result['profiles']), 'deploymentQualified': False}))
