"""Bounded, explicit verification of declared model artifacts; never loads tensors."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

SHA256 = re.compile(r'[0-9a-f]{64}\Z')


def read_object(path: Path, limit: int = 2_000_000) -> tuple[dict, bytes]:
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Artifact metadata exceeds its bound')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('Artifact metadata must be an object')
    return value, raw


def contained_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('Invalid artifact path')
    relative = PurePosixPath(name)
    if relative.is_absolute() or any(part in ('', '.', '..') for part in name.split('/')):
        raise ValueError('Invalid artifact path')
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Artifact symlinks are not admitted')
    if not path.resolve(strict=True).is_relative_to(root) or not path.is_file():
        raise ValueError('Artifact is not a contained regular file')
    return path


def verify(directory: Path, manifest_path: Path, *, max_bytes: int, max_files: int = 4096) -> dict:
    if type(max_bytes) is not int or max_bytes < 1 or type(max_files) is not int or not 1 <= max_files <= 100_000:
        raise ValueError('Explicit positive verification bounds are required')
    root = directory.resolve(strict=True)
    manifest, raw = read_object(manifest_path)
    files = manifest.get('files')
    if not isinstance(files, dict) or not files or len(files) > max_files:
        raise ValueError('Invalid or oversized artifact inventory')
    total = 0
    for name, entry in files.items():
        if (not isinstance(entry, dict) or type(entry.get('bytes')) is not int or entry['bytes'] < 0
                or not isinstance(entry.get('sha256'), str) or not SHA256.fullmatch(entry['sha256'])):
            raise ValueError('Invalid artifact size or digest')
        total += entry['bytes']
        if total > max_bytes:
            raise ValueError('Artifact inventory exceeds byte budget')
        contained_file(root, name)
    for name, entry in files.items():
        path = contained_file(root, name)
        before = path.stat()
        if before.st_size != entry['bytes']:
            raise ValueError('Artifact size changed')
        digest = hashlib.sha256()
        consumed = 0
        with path.open('rb') as stream:
            while block := stream.read(1024 * 1024):
                consumed += len(block)
                if consumed > entry['bytes']:
                    raise ValueError('Artifact grew during verification')
                digest.update(block)
        after = path.stat()
        if (consumed != entry['bytes'] or before.st_mtime_ns != after.st_mtime_ns
                or before.st_ino != after.st_ino or digest.hexdigest() != entry['sha256']):
            raise ValueError('Artifact content changed')
    # Re-read metadata so a concurrent manifest replacement cannot be acknowledged.
    if read_object(manifest_path)[1] != raw:
        raise ValueError('Manifest changed during verification')
    return {'schema': 'swag.artifact-verification/v1',
            'verifiedAt': datetime.now(timezone.utc).isoformat(),
            'manifestSha256': hashlib.sha256(raw).hexdigest(),
            'files': len(files), 'bytes': total,
            'weightBytes': sum(row['bytes'] for name, row in files.items() if name.endswith('.safetensors')),
            'scope': 'declared_files_only', 'maxBytes': max_bytes, 'maxFiles': max_files,
            'tensorContentsValidated': False, 'reloadVerified': False, 'qualified': False}


def describe(manifest_path: Path, receipt_path: Path | None = None) -> dict:
    """Read declared inventory and an optional past receipt without hashing weights."""
    if not manifest_path.exists():
        return {'state': 'not_recorded', 'verification': 'not_recorded'}
    try:
        manifest, raw = read_object(manifest_path)
        files = manifest.get('files')
        if not isinstance(files, dict) or not files or len(files) > 4096:
            raise ValueError('Invalid manifest files')
        for name, entry in files.items():
            if (not isinstance(name, str) or not isinstance(entry, dict) or type(entry.get('bytes')) is not int
                    or entry['bytes'] < 0 or not isinstance(entry.get('sha256'), str) or not SHA256.fullmatch(entry['sha256'])):
                raise ValueError('Invalid inventory entry')
        summary = {'state': 'manifest_recorded', 'manifestSha256': hashlib.sha256(raw).hexdigest(),
                   'files': len(files), 'declaredBytes': sum(row['bytes'] for row in files.values()),
                   'declaredWeightBytes': sum(row['bytes'] for name, row in files.items() if name.endswith('.safetensors')),
                   'model': manifest.get('model') if isinstance(manifest.get('model'), str) else None,
                   'verification': 'not_recorded', 'qualified': False}
        if receipt_path is not None:
            try:
                receipt, _ = read_object(receipt_path)
                if (receipt.get('schema') != 'swag.artifact-verification/v1'
                        or receipt.get('manifestSha256') != summary['manifestSha256']
                        or receipt.get('bytes') != summary['declaredBytes'] or receipt.get('files') != summary['files']
                        or receipt.get('weightBytes') != summary['declaredWeightBytes']
                        or receipt.get('scope') != 'declared_files_only' or receipt.get('qualified') is not False):
                    raise ValueError('Receipt identity mismatch')
                datetime.fromisoformat(receipt['verifiedAt'])
                summary.update(verification='past_receipt_matches_manifest', verifiedAt=receipt['verifiedAt'])
            except (OSError, ValueError, TypeError, KeyError):
                summary['verification'] = 'invalid_or_stale_receipt'
        return summary
    except (OSError, ValueError, TypeError, AttributeError):
        return {'state': 'invalid_manifest', 'verification': 'not_recorded'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--max-bytes', type=int, required=True)
    parser.add_argument('--max-files', type=int, default=4096)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    if args.receipt.exists():
        parser.error('Verification receipts must use a fresh path')
    result = verify(args.directory, args.manifest, max_bytes=args.max_bytes, max_files=args.max_files)
    with args.receipt.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2, allow_nan=False)
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
