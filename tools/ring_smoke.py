#!/usr/bin/env python3
"""Minimal distributed smoke script for multi-node torchrun bring-up."""
from __future__ import annotations

import json
import os
import socket
import time

import torch
import torch.distributed as dist


def main() -> int:
    backend = "nccl" if torch.cuda.is_available() else "gloo"
    dist.init_process_group(backend=backend)

    rank = dist.get_rank()
    world_size = dist.get_world_size()
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    hostname = socket.gethostname()

    if torch.cuda.is_available():
        torch.cuda.set_device(local_rank)
        device_name = torch.cuda.get_device_name(local_rank)
    else:
        device_name = "cpu"

    value = torch.tensor([rank + 1], device=("cuda" if torch.cuda.is_available() else "cpu"), dtype=torch.float32)
    dist.all_reduce(value, op=dist.ReduceOp.SUM)

    payload = {
        "rank": rank,
        "world_size": world_size,
        "local_rank": local_rank,
        "hostname": hostname,
        "backend": backend,
        "device": device_name,
        "all_reduce_sum": float(value.item()),
        "ts": int(time.time()),
    }
    print(json.dumps(payload, sort_keys=True), flush=True)

    dist.barrier()
    dist.destroy_process_group()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
