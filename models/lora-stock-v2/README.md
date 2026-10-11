# lora-stock-v2

LoRA adapter for Qwen/Qwen3.8-27B answering our stock question (prompt v1: A empty, B half, C full, D can't tell). Same as `lora-stock-v1` but learning rate 2e-4 (chosen by the 5-fold sweep in `ml/lora_cv.py`: 199 vs 163 held-out stock points of 344 at half threshold 0.4), trained on all 344 labels with `ml/finetune.py --lr 2e-4 --epochs 2 --rank 8` (8 min).

In the submission its stock scores are averaged 50/50 with `models/yolo-stock-v1.pt` (held out: 253 of 344), then half if ≥ 0.4 and the empty check. Use: `scripts/run_validation.sh` (or `ml.run --adapter models/lora-stock-v2`).
