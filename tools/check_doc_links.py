"""Fail when a Markdown file links to a repository path that does not exist.

    python tools/check_doc_links.py

Checks relative links only (not URLs or in-page anchors) in tracked Markdown, so moving or deleting a
document cannot silently leave readers at a dead link.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'\]\(([^)\s]+)\)')


def broken_links(root: Path = ROOT) -> list[str]:
    listed = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '*.md'],
                            cwd=root, capture_output=True, text=True, check=True).stdout.split('\n')
    problems = []
    for name in filter(None, listed):
        path = root / name
        if not path.is_file():
            continue
        in_code = False
        for number, line in enumerate(path.read_text(encoding='utf-8').split('\n'), 1):
            if line.lstrip().startswith('```'):
                in_code = not in_code
            if in_code:
                continue
            for target in LINK.findall(line):
                if re.match(r'^[a-z][a-z0-9+.-]*:', target) or target.startswith('#'):
                    continue
                relative = target.split('#', 1)[0]
                if relative and not (path.parent / relative).exists():
                    problems.append(f'{name}:{number}: {target}')
    return problems


if __name__ == '__main__':
    found = broken_links()
    for problem in found:
        print(problem)
    sys.exit(1 if found else 0)
