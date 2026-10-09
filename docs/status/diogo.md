# Status — Diogo

## Doing
- Sat 12:00: look at the Sensei data (timestamps, frames per camera, validation same day?), then crops + scorer + baselines.

## Done
- Fri 9 Oct: knuth ready. Env `jx` (torch 2.11 cu128, transformers 5.19). Models in `/workspace/models/`: Qwen3.8-27B (54.7 GB VRAM, 0.27 s/question), SAM 3 (1.7 GB), DINOv3 ViT-L/16 (0.6 GB, 152 crops in 0.3 s). All three fit together (~57/96 GB). Smoke tests in `/workspace/jx/`. 37 GB disk free.

## Blocked
- Nothing.

## Decisions
- Sensei, plan in `docs/PLAN.md`. VLM probabilities are overconfident (0.999) → calibration required. SAM 3 generic prompts ("fruit") fail → prompt with product names + "produce" at 0.3.
- knuth: only `/workspace`, never delete pre-existing files, never use `/media`.
