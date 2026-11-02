#!/usr/bin/env python3
"""Run SWAG LoRA SFT training with Unsloth acceleration."""
from __future__ import annotations

import argparse
from contextlib import suppress
import faulthandler
import hashlib
import importlib.util
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
from typing import Any

def _training_rows(dataset_path: Path, contents: str | None = None) -> list[dict[str, Any]]:
    """Preserve chat structure so TRL applies the actual model chat template."""
    if contents is None:
        contents = dataset_path.read_text(encoding="utf-8-sig")
    rows = (json.loads(contents) if contents.lstrip().startswith("[") else
            [json.loads(line) for line in contents.splitlines() if line.strip()])
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"Dataset must contain nonempty JSON/JSONL rows: {dataset_path}")
    normalized = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} is not an object")
        if "messages" in row:
            messages = row["messages"]
            if not isinstance(messages, list) or not messages:
                raise ValueError(f"Row {index} has no messages")
            for message in messages:
                if (not isinstance(message, dict)
                        or message.get("role") not in {"system", "user", "assistant", "tool"}
                        or not isinstance(message.get("content"), str)
                        or not message["content"].strip()):
                    raise ValueError(f"Row {index} contains an invalid text message")
            if not any(message["role"] == "assistant" for message in messages):
                raise ValueError(f"Row {index} has no assistant training target")
            normalized.append({"messages": messages})
        elif isinstance(row.get("text"), str) and row["text"].strip():
            normalized.append({"text": row["text"]})
        else:
            raise ValueError(f"Row {index} requires messages or nonempty text")
    if len({next(iter(row)) for row in normalized}) != 1:
        raise ValueError("Do not mix text and conversational rows in one dataset")
    return normalized


def _preflight() -> dict[str, Any]:
    names = ("unsloth", "torch", "trl", "transformers", "datasets", "peft")
    missing = [name for name in names if importlib.util.find_spec(name) is None]
    result: dict[str, Any] = {"ready": False, "missing_packages": missing}
    if missing:
        return result
    try:
        import unsloth  # noqa: F401; must patch before torch/TRL imports
        import torch
        result["cuda_available"] = torch.cuda.is_available()
        if result["cuda_available"]:
            result["gpu"] = torch.cuda.get_device_name(0)
            result["device_memory_bytes"] = torch.cuda.get_device_properties(0).total_memory
            # Exercise a real GPU operation, not just CUDA discovery.
            sample = torch.ones((16, 16), device="cuda")
            result["cuda_probe_passed"] = (sample @ sample).sum().item() == 4096
            result["ready"] = result["cuda_probe_passed"]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def _validate_admitted_inputs(directory: Path, training_path: Path,
                              evaluation_path: Path | None) -> str:
    """Check exported bytes and split selection before GPU imports or model loading."""
    from swag_routing_eval import verify_dataset

    manifest = verify_dataset(directory)
    if manifest['counts']['train'] < 1:
        raise ValueError('Admitted dataset has no training rows')
    if training_path.resolve() != (directory / 'train.chat.jsonl').resolve():
        raise ValueError('Training must use the admitted train split')
    if evaluation_path is not None:
        if evaluation_path.resolve() != (directory / 'development.chat.jsonl').resolve():
            raise ValueError('Training-time evaluation must use development, never acceptance')
        if manifest['counts']['development'] < 1:
            raise ValueError('Admitted dataset has no development rows')
    return hashlib.sha256((directory / 'manifest.json').read_bytes()).hexdigest()


def _admitted_snapshot(directory: Path, training_path: Path, evaluation_path: Path | None,
                       admission_digest: str) -> tuple[bytes, bytes | None]:
    """Consume already validated split identities into immutable process inputs."""
    manifest_bytes = (directory / 'manifest.json').read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != admission_digest:
        raise ValueError('Admission manifest changed; prepare a fresh training input')
    manifest = json.loads(manifest_bytes)
    training = training_path.read_bytes()
    evaluation = evaluation_path.read_bytes() if evaluation_path else None
    for name, contents in (('train.chat.jsonl', training), ('development.chat.jsonl', evaluation)):
        if contents is not None and hashlib.sha256(contents).hexdigest() != manifest['files'][name]:
            raise ValueError('Admitted data changed; prepare a fresh training input')
    return training, evaluation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train SWAG LoRA adapter with Unsloth + TRL.")
    parser.add_argument("--preflight", action="store_true", help="Check imports and actual CUDA execution; no training or downloads.")
    parser.add_argument("--model", help="Base model name or local snapshot path.")
    parser.add_argument("--model-revision", help="Pinned model revision for a Hub model.")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--dataset-jsonl", type=Path, help="Path to JSON/JSONL training data.")
    parser.add_argument("--eval-dataset-jsonl", type=Path)
    parser.add_argument("--admitted-dataset-dir", type=Path,
                        help="Verify reviewed export and train/development split identities before GPU work.")
    parser.add_argument("--task-corpus-dir", type=Path,
                        help="Retired provisional input; rejected for new training. Retained for an explicit diagnostic.")
    parser.add_argument("--seed", type=int, help="Explicit experiment seed, recorded with the training arguments.")
    parser.add_argument("--instruction-start", help="Exact tokenizer instruction delimiter for response-only loss.")
    parser.add_argument("--response-start", help="Exact tokenizer response delimiter for response-only loss.")
    parser.add_argument("--output-dir", type=Path, help="Fresh output adapter directory.")
    parser.add_argument("--learning-rate", type=float, default=2.0e-4)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--save-steps", type=int, default=50)
    parser.add_argument("--eval-steps", type=int, default=0)
    parser.add_argument("--logging-steps", type=int, default=1)
    parser.add_argument("--observation-max-bytes", type=int, default=4_000_000,
                        help="Bound content-free trainer observations for UI/adapter inspection.")
    parser.add_argument("--max-steps", type=int, default=0)
    parser.add_argument("--torch-empty-cache-steps", type=int, default=1)
    parser.add_argument("--ddp-backend", default="nccl")
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--bf16", dest="bf16", action="store_true", default=True)
    parser.add_argument("--no-bf16", dest="bf16", action="store_false")
    parser.add_argument("--gradient-checkpointing", dest="gradient_checkpointing", action="store_true", default=True)
    parser.add_argument("--no-gradient-checkpointing", dest="gradient_checkpointing", action="store_false")
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument(
        "--lora-target-modules",
        nargs="+",
        default=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    args = parser.parse_args()
    if not args.preflight:
        if not args.model or not args.dataset_jsonl or not args.output_dir:
            parser.error("training requires --model, --dataset-jsonl and --output-dir")
        if args.eval_steps > 0 and args.eval_dataset_jsonl is None:
            parser.error("--eval-steps requires --eval-dataset-jsonl")
        if args.max_steps < 0 or args.max_length <= 0:
            parser.error("max-steps must be nonnegative and max-length positive")
        if bool(args.instruction_start) != bool(args.response_start):
            parser.error('Response-only loss requires both exact tokenizer delimiters')
        if args.task_corpus_dir is not None:
            parser.error("Provisional task labels are not approved for new training; provide independently reviewed real observations through --admitted-dataset-dir")
        if args.admitted_dataset_dir is None:
            parser.error("training requires --admitted-dataset-dir with reviewed real observations")
        if args.seed is None or not 0 <= args.seed <= 2**32 - 1:
            parser.error("training requires an explicit --seed in the unsigned 32-bit range")
        if not args.model_revision or not re.fullmatch(r'[0-9a-f]{40}', args.model_revision):
            parser.error('training requires an exact 40-character --model-revision')
        if not 1024 <= args.observation_max_bytes <= 4_000_000:
            parser.error('observation-max-bytes must be between 1024 and 4000000')
        if os.environ.get('WORLD_SIZE', '1') != '1':
            parser.error('The observed trainer currently supports one process; distributed training is unqualified')
    return args


def main() -> int:
    faulthandler.enable(all_threads=True)
    trainer_source = Path(__file__).read_bytes()
    args = parse_args()
    admission_digest = None
    task_corpus_digest = None
    if args.admitted_dataset_dir is not None and args.task_corpus_dir is not None:
        raise ValueError('Choose admitted routing or provisional intent, not both')
    if not args.preflight and args.admitted_dataset_dir is not None:
        admission_digest = _validate_admitted_inputs(args.admitted_dataset_dir,
                                                    args.dataset_jsonl, args.eval_dataset_jsonl)
        # Consume the exact admitted bytes. An ordinary edit cannot silently
        # replace training data between validation and a slow GPU/model import.
        dataset_bytes, eval_bytes = _admitted_snapshot(args.admitted_dataset_dir,
            args.dataset_jsonl, args.eval_dataset_jsonl, admission_digest)
    readiness = _preflight()
    print(json.dumps({"phase": "preflight", **readiness}), flush=True)
    if args.preflight:
        return 0 if readiness["ready"] else 2
    if not readiness["ready"]:
        return 2
    # Unsloth was imported first in preflight, before any training library.
    from datasets import Dataset
    import torch
    from trl import SFTConfig, SFTTrainer

    dataset_path = args.dataset_jsonl.resolve()
    dataset = Dataset.from_list(_training_rows(dataset_path, dataset_bytes.decode("utf-8-sig")))
    eval_dataset = None
    eval_digest = None
    if args.eval_dataset_jsonl is not None:
        if args.eval_dataset_jsonl.resolve() == dataset_path:
            raise SystemExit("Training and evaluation must use separate datasets")
        eval_path = args.eval_dataset_jsonl.resolve()
        eval_digest = hashlib.sha256(eval_bytes).hexdigest()
        if eval_digest == hashlib.sha256(dataset_bytes).hexdigest():
            raise SystemExit("Training and evaluation datasets have identical bytes")
        eval_dataset = Dataset.from_list(_training_rows(eval_path, eval_bytes.decode("utf-8-sig")))
    # Never overwrite a prior adapter or its evidence.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / 'trainer.py').write_bytes(trainer_source)
    observation_sources = {}
    for name in ('swag_training_observations.py', 'swag_training_artifacts.py'):
        source = Path(__file__).with_name(name).read_bytes()
        (args.output_dir / name).write_bytes(source)
        observation_sources[name] = hashlib.sha256(source).hexdigest()
    run_config = {
        "arguments": vars(args),
        "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "eval_dataset_sha256": eval_digest,
        "admission_manifest_sha256": admission_digest,
        "provisional_task_corpus_sha256": task_corpus_digest,
        "packages": {name: version(name) for name in ("unsloth", "torch", "trl", "transformers", "datasets", "peft")},
        "trainer_source_sha256": hashlib.sha256(trainer_source).hexdigest(),
        "observation_source_sha256": observation_sources,
        "preflight": readiness,
    }
    (args.output_dir / "run_config.json").write_text(
        json.dumps(run_config, indent=2, default=str), encoding="utf-8")
    warmup_steps = max(0, int(args.max_steps * args.warmup_ratio)) if args.max_steps > 0 else 0
    world_size = int(os.environ.get("WORLD_SIZE", "1"))

    try:
        from unsloth import FastLanguageModel  # type: ignore
    except Exception as exc:
        raise SystemExit(
            "Unsloth initialization failed. Ensure package install and a CUDA-enabled PyTorch build for this GPU. "
            f"Original error: {exc}"
        ) from exc

    dtype = torch.bfloat16 if args.bf16 else torch.float16
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_length,
        dtype=dtype,
        load_in_4bit=args.load_in_4bit,
        revision=args.model_revision,
        local_files_only=args.local_files_only,
        device_map={"": int(os.environ.get("LOCAL_RANK", "0"))},
    )
    if "messages" in dataset.column_names and not tokenizer.chat_template:
        raise SystemExit("Conversational training requires the model's chat template")
    # Some pinned Unsloth/TRL combinations require an explicit text column.
    # Render through the actual tokenizer, never concatenate or invent chat markers.
    def render_chat(row):
        return {'text': tokenizer.apply_chat_template(row['messages'], tokenize=False,
                                                      add_generation_prompt=False)}
    if 'messages' in dataset.column_names:
        dataset = dataset.map(render_chat, remove_columns=dataset.column_names)
    if eval_dataset is not None and 'messages' in eval_dataset.column_names:
        eval_dataset = eval_dataset.map(render_chat, remove_columns=eval_dataset.column_names)
    tokenizer.save_pretrained(str(args.output_dir.resolve()))
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=args.lora_target_modules,
        bias="none",
        use_gradient_checkpointing="unsloth" if args.gradient_checkpointing else False,
        random_state=args.seed,
    )
    print(json.dumps({'phase': 'model_devices', 'device_map': getattr(model, 'hf_device_map', {}),
                      'parameter_devices': sorted({str(parameter.device) for parameter in model.parameters()})}), flush=True)

    eval_strategy = "no"
    if args.eval_steps > 0:
        eval_strategy = "steps"

    sft_kwargs: dict[str, Any] = dict(
        output_dir=str(args.output_dir.resolve()),
        seed=args.seed,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        warmup_steps=warmup_steps,
        warmup_ratio=args.warmup_ratio,
        num_train_epochs=args.num_train_epochs,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        per_device_train_batch_size=args.per_device_train_batch_size,
        max_length=args.max_length,
        dataset_text_field="text",
        save_strategy="steps",
        save_steps=args.save_steps,
        eval_strategy=eval_strategy,
        eval_steps=args.eval_steps if args.eval_steps > 0 else None,
        logging_steps=args.logging_steps,
        logging_first_step=True,
        report_to=[],
        bf16=args.bf16,
        gradient_checkpointing=args.gradient_checkpointing,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        dataloader_num_workers=0,
        torch_empty_cache_steps=args.torch_empty_cache_steps,
        save_only_model=False,
        ddp_timeout=7200,
        remove_unused_columns=True,
        max_steps=args.max_steps if args.max_steps > 0 else -1,
    )
    if world_size > 1:
        sft_kwargs["ddp_backend"] = args.ddp_backend

    train_cfg = SFTConfig(**sft_kwargs)
    (args.output_dir / 'effective_training_config.json').write_text(train_cfg.to_json_string(), encoding='utf-8')
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        args=train_cfg,
        train_dataset=dataset,
        eval_dataset=eval_dataset,
    )
    if args.response_start:
        from unsloth.chat_templates import train_on_responses_only
        trainer = train_on_responses_only(trainer, instruction_part=args.instruction_start,
                                          response_part=args.response_start)
        # The response-mask helper selects a seq2seq collator. Raw strings must
        # never be forwarded into its tensor padding operation.
        for attribute in ('train_dataset', 'eval_dataset'):
            prepared = getattr(trainer, attribute, None)
            if prepared is not None:
                if 'text' in prepared.column_names:
                    prepared = prepared.remove_columns('text')
                    setattr(trainer, attribute, prepared)
                counts = [sum(label != -100 for label in row['labels']) for row in prepared]
                if not counts or min(counts) < 1:
                    raise ValueError('Response-only masking removed every target in an example')
                print(json.dumps({'phase': 'loss_mask_verified', 'split': attribute,
                                  'examples': len(counts), 'target_tokens': sum(counts)}), flush=True)
    print(json.dumps({"phase": "training", "rows": len(dataset), "max_steps": args.max_steps,
                      "output_dir": str(args.output_dir.resolve())}), flush=True)
    torch.cuda.reset_peak_memory_stats()
    from swag_training_observations import TrainingObserver
    observer = TrainingObserver(args.output_dir, limit_bytes=args.observation_max_bytes)
    trainer.add_callback(observer.callback())
    try:
        observer.install_signals()
        result = trainer.train()
        trainer.save_state()
        if observer.stop_requested or trainer.state.global_step < trainer.state.max_steps:
            # A cooperative stop may save a real checkpoint, but cannot create
            # the completion metadata consumed by the BF16 exporter.
            interrupted = {'schema': 'swag.training-interruption/v1',
                           'attemptId': observer.attempt_id, 'globalStep': trainer.state.global_step,
                           'maxSteps': trainer.state.max_steps, 'stopRequested': observer.stop_requested,
                           'completed': False, 'qualified': False}
            (args.output_dir / 'training_interrupted.json').write_text(json.dumps(interrupted), encoding='utf-8')
            return 130 if observer.stop_requested else 2
        trainer.save_model(str(args.output_dir.resolve()))
        trainer.save_metrics("train", result.metrics)
        observer.emit('artifacts_saved', trainer.state, result.metrics)
    except BaseException as exc:
        with suppress(Exception):
            observer.emit('failed', trainer.state, error_type=type(exc).__name__)
        raise
    finally:
        observer.close()
    metadata = {
        "trainer_backend": "unsloth",
        "model": args.model,
        "model_revision": args.model_revision,
        "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "admission_manifest_sha256": admission_digest,
        "provisional_task_corpus_sha256": task_corpus_digest,
        "precision": "bf16" if args.bf16 else "fp16",
        "base_quantized": args.load_in_4bit,
        "artifact_kind": "lora_adapter_requires_pinned_base",
        "trainer_source_sha256": hashlib.sha256(trainer_source).hexdigest(),
        "observation_source_sha256": observation_sources,
        "training_attempt_id": observer.attempt_id,
        "global_step": trainer.state.global_step,
        "metrics": result.metrics,
        "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated(),
        "gpu_peak_reserved_bytes": torch.cuda.max_memory_reserved(),
        "qualified_for_deployment": False,
        "dataset_jsonl": str(args.dataset_jsonl.resolve()),
        "output_dir": str(args.output_dir.resolve()),
    }
    (args.output_dir / "training_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps({"phase": "training_completed", **metadata}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
