# Error review material (11 October 2026)

- `stock-heldout-errors.csv` / `.jpg`: the 25 stock mistakes of the submitted stock decision (YOLO11n + LoRA v2 averaged, half ≥ 0.4, empty check) on our 344 labels, each predicted by models that never saw that label (5-fold, `ml/lora_cv.py` folds). `points` = Sensei stock points for that answer (−2 too low, −3 too high). Columns `yolo_*` / `lora_*`: the two models' empty (A) / half (B) / full (C) probabilities; `empty_check_A`: the base model's "empty" score from the second question (overrides to empty at ≥ 0.70).
- `product-check-errors.csv` / `.jpg`: the trained product check (B ≥ 0.6 → non-compliant, never on empty areas) against our strict review of 34 suspicious shelves (435 images): 77 missed wrong products, 27 false alarms. The check was never trained on these shelves.
- Crops: `data/prepared-v1/assets/<id>.png` locally (id = `<camera>_<timestamp>_<area>`); the sheets show the same crops with labels.
