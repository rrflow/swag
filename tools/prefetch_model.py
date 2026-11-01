#!/usr/bin/env python3
from __future__ import annotations

import argparse

from huggingface_hub import snapshot_download


def main() -> int:
    parser = argparse.ArgumentParser(description="Prefetch model files into local Hugging Face cache.")
    parser.add_argument("--model", required=True, help="Model ID to prefetch.")
    args = parser.parse_args()
    path = snapshot_download(args.model)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
