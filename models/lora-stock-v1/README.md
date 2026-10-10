# lora-stock-v1

LoRA adapter for Qwen/Qwen3.8-27B that answers our stock question (prompt v1: A empty, B half, C full, D can't tell).

- Trained with `ml/finetune.py` on all 344 of our labelled shelf observations: rank 8 on the language model's attention projections, 2 epochs, lr 1e-4, 8 minutes on one RTX PRO 6000.
- Use: `python -m ml.run <images> --output <dir> --model <qwen3.8-27b> --adapter models/lora-stock-v1` (needs `peft`). Half if the half score is ≥ 0.4 (`ml/lora_thresholds.json`); the empty check runs on the base model with the adapter disabled.
- Held-out (2 folds, 138 labels): 78 stock points vs 68 for the hidden-state probe. Details in `docs/RESULTS.md`.
