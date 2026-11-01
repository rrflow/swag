"""Explain retirement of training paths without reviewed-data admission."""

LEGACY_TRAINING_RETIRED = (
    "Legacy training generation and execution are retired: these paths do not "
    "verify independently reviewed real observations. Preserve historical artifacts; "
    "admit new data with tools/swag_routing_dataset.py, then explicitly invoke "
    "tools/swag_unsloth_train.py with --admitted-dataset-dir and --seed. "
    "See docs/routing-data-and-evaluation.md. No data was generated or job launched."
)
