"""Versioned read model shared by the local developer UI and MCP clients."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path

from swag_observability import HASH, observed, summarize, trace_directory
from swag_training_artifacts import describe, read_object
from swag_training_observations import progress


def read_json(path: Path) -> dict:
    return read_object(path)[0]


def dataset_status() -> dict:
    configured = os.environ.get('SWAG_ADMITTED_DATASET_DIR')
    if not configured:
        return {'state': 'not_configured', 'counts': None, 'manifestSha256': None}
    try:
        from swag_routing_eval import verify_dataset
        directory = Path(configured)
        manifest = verify_dataset(directory)
        return {'state': 'verified_export' if all(manifest['counts'].values()) else 'empty_export', 'counts': manifest['counts'],
                'manifestSha256': hashlib.sha256((directory / 'manifest.json').read_bytes()).hexdigest()}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {'state': 'invalid_export', 'counts': None, 'manifestSha256': None}


def training_runs() -> list[dict]:
    configured = os.environ.get('SWAG_TRAINING_RUNS_FILE')
    if not configured:
        return []
    config = read_json(Path(configured))
    runs = config.get('runs')
    if config.get('schemaVersion') != 1 or not isinstance(runs, list) or len(runs) > 100:
        raise ValueError('Invalid training-run registry')
    result = []
    for entry in runs:
        if (not isinstance(entry, dict) or not {'id', 'directory'} <= set(entry)
                or set(entry) - {'id', 'directory', 'artifactManifest', 'artifactVerification'}
                or not isinstance(entry['id'], str) or not entry['id'] or len(entry['id']) > 96):
            raise ValueError('Invalid training-run entry')
        directory = Path(entry['directory'])
        if not directory.is_absolute():
            directory = Path(configured).resolve().parent / directory
        def selected_path(key: str, default: Path | None):
            if key not in entry:
                return default
            value = Path(entry[key])
            return value if value.is_absolute() else Path(configured).resolve().parent / value
        row = {'id': entry['id'], 'state': 'unavailable', 'metrics': {}, 'metadataSha256': None,
               'trainingAuthorized': False, 'promotionAuthorized': False,
               'progress': progress(directory),
               'artifact': describe(selected_path('artifactManifest', directory / 'artifact-manifest.json'),
                                    selected_path('artifactVerification', None))}
        try:
            metadata_file = directory / 'training_metadata.json'
            if metadata_file.is_file():
                data, metadata_bytes = read_object(metadata_file)
                row['state'] = 'completion_record_present'
                row['metadataSha256'] = hashlib.sha256(metadata_bytes).hexdigest()
                for key in ('gpu_peak_allocated_bytes', 'gpu_peak_reserved_bytes', 'train_runtime', 'train_loss'):
                    value = data.get(key, data.get('metrics', {}).get(key))
                    if type(value) in {int, float} and math.isfinite(value) and value >= 0:
                        row['metrics'][key] = value
                row['precision'] = data.get('precision') if data.get('precision') in {'bf16', 'fp16'} else None
                digest = data.get('admission_manifest_sha256')
                row['admissionManifestSha256'] = digest if isinstance(digest, str) and HASH.fullmatch(digest) else None
                provisional = data.get('provisional_task_corpus_sha256')
                row['datasetBasis'] = ('reviewed_export_recorded' if row['admissionManifestSha256'] else
                    'provisional_task_corpus' if isinstance(provisional, str) and HASH.fullmatch(provisional) else 'unknown')
                for source, target in (('model', 'model'), ('model_revision', 'modelRevision'),
                                       ('artifact_kind', 'artifactKind')):
                    value = data.get(source)
                    row[target] = value if isinstance(value, str) and len(value) <= 256 else None
                row['baseQuantized'] = data.get('base_quantized') if type(data.get('base_quantized')) is bool else None
            elif (directory / 'training_interrupted.json').is_file():
                row['state'] = 'interruption_record_present'
            elif (directory / 'run_config.json').is_file():
                row['state'] = 'configured_outcome_unknown'
        except (OSError, ValueError, TypeError, AttributeError):
            row['state'] = 'invalid_artifact'
        result.append(row)
    return result


@observed('swag.dev_status')
def status() -> dict:
    engine = {'state': 'not_configured', 'authenticated': False}
    if os.environ.get('SWAG_RRFLOW_CONNECTION_FILE'):
        from swag_rrflow import status as engine_status
        try:
            engine = {'state': 'connected', **engine_status()}
        except Exception:
            engine = {'state': 'unavailable', 'authenticated': False, 'detail': 'Inspect rrflow.status traces.'}
    try:
        runs = training_runs()
        registry_state = 'read' if os.environ.get('SWAG_TRAINING_RUNS_FILE') else 'not_configured'
    except (OSError, ValueError, TypeError, KeyError):
        runs, registry_state = [], 'invalid_registry'
    return {'schema': 'swag.dev-status/v1', 'observedAt': datetime.now(timezone.utc).isoformat(),
            'engine': engine, 'observability': summarize(trace_directory()),
            'training': {'dataset': dataset_status(), 'runs': runs, 'registryState': registry_state,
                         'launchAvailable': False, 'launchBlocker': 'engine_training_job_admission_not_integrated',
                         'trainer': 'swag_unsloth_train', 'gpuExecutionVerified': False},
            'optimization': {'basis': 'observed_timings_and_registered_artifacts',
                             'qualificationRequired': ['original_baseline', 'custom_bf16', 'same_checkpoint_quantized'],
                             'automaticPromotionAvailable': False},
            'integration': {'connectomeIntegrated': False, 'subscriptionUsageObserved': False,
                            'rroflowTraceExportAvailable': False}}


if __name__ == '__main__':
    print(json.dumps(status(), separators=(',', ':')))
