"""Merge a completed BF16 LoRA experiment into hashed, independently loadable weights."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


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
    args = parser.parse_args()
    base = json.loads(args.base_manifest.read_text())
    metadata = json.loads((args.adapter_dir / 'training_metadata.json').read_text())
    if metadata.get('global_step', 0) < 1 or metadata.get('precision') != 'bf16' or metadata.get('base_quantized') is not False:
        raise ValueError('Require completed, nonquantized BF16 training evidence')
    if metadata.get('model_revision') != base['revision']:
        raise ValueError('Training base revision mismatch')
    if (base.get('precision') not in ('bf16', 'bfloat16') or base.get('custom_checkpoint') is not False
            or not any(name.endswith('.safetensors') for name in base.get('files', {}))):
        raise ValueError('Require original BF16 base artifact inventory')
    for name, expected in base['files'].items():
        if Path(name).name != name or file_sha(args.base_dir / name) != expected['sha256']:
            raise ValueError('Base artifact identity mismatch')
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
    manifest = {'model': 'swag-qwen3-coder-intent-20261028', 'precision': 'bfloat16',
                'custom_checkpoint': True, 'qualified': False, 'artifactKind': 'merged_bf16_checkpoint',
                'baseModel': base['model'], 'baseRevision': base['revision'],
                'baseManifestSha256': file_sha(args.base_manifest),
                'adapterFiles': adapter_files, 'trainingMetadataSha256': file_sha(args.adapter_dir / 'training_metadata.json'),
                'provisionalTaskCorpusSha256': metadata.get('provisional_task_corpus_sha256'),
                'trainingSteps': metadata['global_step'], 'files': files,
                'createdAt': datetime.now(timezone.utc).isoformat(),
                'reloadVerified': False, 'purpose': 'provisional_task_intent_specialization'}
    (args.output_dir / 'artifact-manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps({'phase': 'export_complete', 'weightBytes': sum(v['bytes'] for k, v in files.items()
                     if k.endswith('.safetensors')), 'manifestSha256': file_sha(args.output_dir / 'artifact-manifest.json'),
                     'qualified': False, 'reloadVerified': False}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
