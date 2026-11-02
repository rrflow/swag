"""Merge a completed BF16 LoRA experiment into hashed, independently loadable weights."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from swag_training_artifacts import read_object, verify


def file_sha(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base-dir', 'base-manifest', 'adapter-dir', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--model-id', required=True, help='Explicit identity for this exported checkpoint.')
    parser.add_argument('--max-base-bytes', type=int, required=True, help='Explicit byte budget for base verification.')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,127}', args.model_id):
        parser.error('model-id must be a bounded model identifier')
    base = json.loads(args.base_manifest.read_text())
    metadata = json.loads((args.adapter_dir / 'training_metadata.json').read_text())
    if metadata.get('global_step', 0) < 1 or metadata.get('precision') != 'bf16' or metadata.get('base_quantized') is not False:
        raise ValueError('Require completed, nonquantized BF16 training evidence')
    if metadata.get('model_revision') != base['revision']:
        raise ValueError('Training base revision mismatch')
    if (base.get('precision') not in ('bf16', 'bfloat16') or base.get('custom_checkpoint') is not False
            or not any(name.endswith('.safetensors') for name in base.get('files', {}))):
        raise ValueError('Require original BF16 base artifact inventory')
    if (args.adapter_dir / 'training_interrupted.json').exists():
        raise ValueError('Interrupted training cannot be exported as completed')
    state, _ = read_object(args.adapter_dir / 'trainer_state.json')
    if (type(state.get('global_step')) is not int or type(state.get('max_steps')) is not int
            or state['max_steps'] < 1 or state['global_step'] != state['max_steps']
            or state['global_step'] != metadata['global_step']):
        raise ValueError('Trainer completion state does not match metadata')
    verify(args.base_dir, args.base_manifest, max_bytes=args.max_base_bytes)
    adapter_files = {path.name: file_sha(path) for path in args.adapter_dir.iterdir()
                     if path.is_file() and path.suffix in ('.json', '.safetensors', '.jinja')}
    if 'adapter_model.safetensors' not in adapter_files or 'adapter_config.json' not in adapter_files:
        raise ValueError('Missing adapter artifacts')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print(json.dumps({'phase': 'merge_load', 'device': 'cpu', 'precision': 'bfloat16'}), flush=True)
    model = AutoModelForCausalLM.from_pretrained(str(args.base_dir), torch_dtype=torch.bfloat16,
            device_map='cpu', low_cpu_mem_usage=True, local_files_only=True, trust_remote_code=False)
    model = PeftModel.from_pretrained(model, str(args.adapter_dir), local_files_only=True)
    model = model.merge_and_unload(safe_merge=True)
    if any(parameter.dtype != torch.bfloat16 for parameter in model.parameters()):
        raise ValueError('Merged model contains non-BF16 parameters')
    model.save_pretrained(args.output_dir, safe_serialization=True, max_shard_size='4GB')
    AutoTokenizer.from_pretrained(str(args.adapter_dir), local_files_only=True).save_pretrained(args.output_dir)
    files = {path.name: {'bytes': path.stat().st_size, 'sha256': file_sha(path)}
             for path in sorted(args.output_dir.iterdir()) if path.is_file()}
    manifest = {'model': args.model_id, 'precision': 'bfloat16',
                'custom_checkpoint': True, 'qualified': False, 'artifactKind': 'merged_bf16_checkpoint',
                'baseModel': base['model'], 'baseRevision': base['revision'],
                'baseManifestSha256': file_sha(args.base_manifest),
                'adapterFiles': adapter_files, 'trainingMetadataSha256': file_sha(args.adapter_dir / 'training_metadata.json'),
                'provisionalTaskCorpusSha256': metadata.get('provisional_task_corpus_sha256'),
                'admissionManifestSha256': metadata.get('admission_manifest_sha256'),
                'trainingSteps': metadata['global_step'], 'files': files,
                'createdAt': datetime.now(timezone.utc).isoformat(),
                'reloadVerified': False, 'purpose': 'candidate_checkpoint_evaluation'}
    (args.output_dir / 'artifact-manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps({'phase': 'export_complete', 'weightBytes': sum(v['bytes'] for k, v in files.items()
                     if k.endswith('.safetensors')), 'manifestSha256': file_sha(args.output_dir / 'artifact-manifest.json'),
                     'qualified': False, 'reloadVerified': False}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
