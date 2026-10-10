#!/usr/bin/env bash
# Final validation in one command: images (folder or ZIP) -> data/val-<name>/export/submission.json
# Usage: scripts/run_validation.sh <images-folder-or-zip> <name>
# Prepares + infers on knuth (only raw images go up, small JSON comes back). If knuth fails, still writes a
# complete fallback submission (half, compliant) and says so.
set -uo pipefail
cd "$(dirname "$0")/.."
SRC=${1:?images folder or zip}; NAME=${2:?run name}
PY=${PYTHON:-python3}; HOST=${KNUTH:-knuth}
OUT=data/val-$NAME; REMOTE=/workspace/jx/val-$NAME
RPY=/workspace/miniconda/envs/jx-fast/bin/python; REFS=/workspace/jx/sensei-full-v1/data/prepared-v1/assets
DATASET=new_dataset_hackathon_junctionx_10_oct_2026_v2
[ -e "$OUT" ] && { echo "$OUT exists; choose a new name"; exit 1; }
mkdir -p "$OUT"; start=$(date +%s); ok=1
step(){ echo "[$(( $(date +%s) - start ))s] $*"; }

step "upload images + code to $HOST:$REMOTE"
if ssh -o ConnectTimeout=15 -o BatchMode=yes "$HOST" "test ! -e $REMOTE && mkdir -p $REMOTE/input" &&
   COPYFILE_DISABLE=1 tar czf - --exclude __pycache__ ml "$DATASET/planogram.json" 2>/dev/null | ssh "$HOST" "cd $REMOTE && tar xzf - 2>/dev/null" &&
   if [ -d "$SRC" ]; then COPYFILE_DISABLE=1 tar czf - -C "$SRC" . 2>/dev/null | ssh "$HOST" "cd $REMOTE/input && tar xzf - 2>/dev/null"
   else cat "$SRC" | ssh "$HOST" "cat > $REMOTE/input.zip"; fi; then
  INPUT=input; [ -d "$SRC" ] || INPUT=input.zip
  step "prepare on $HOST"
  ssh "$HOST" "cd $REMOTE && $RPY -B -m ml.validate $INPUT --references $REFS --output $OUT ${VALIDATE_FLAGS:-}" 2>&1 | tee "$OUT-prepare.log" | grep -v "^WARNING" | tail -40
  ssh "$HOST" "cat $REMOTE/$OUT/crops-sheet.jpg" > "$OUT-crops-sheet.jpg" 2>/dev/null && { step "CHECK $OUT-crops-sheet.jpg now (opening it): wrong crops = Ctrl-C"; open "$OUT-crops-sheet.jpg" 2>/dev/null || true; }
  step "inference on $HOST (Qwen3.8-27B + LoRA stock question; empty check on the base model when needed)"
  ssh "$HOST" "cd $REMOTE && $RPY -B -u -m ml.infer_sample $OUT/sample.json --model /workspace/models/qwen3.8-27b --stock-prompt v1 --paired-prompt v4 --paired-output $OUT/results-empty.json --paired-only-if-full-below 0.5 --questions stock --context-max-side 640 --adapter /workspace/models/lora-stock-v1 --output $OUT/results.json" > "$OUT/inference.log" 2>&1 || ok=0
  step "fetch results"
  for f in expected sample report results results-empty; do ssh "$HOST" "cat $REMOTE/$OUT/$f.json" > "$OUT/$f.json" || ok=0; done
else
  ok=0
  step "!!! $HOST unreachable: preparing locally for a fallback submission"
  rmdir "$OUT"; $PY -m ml.validate "$SRC" --output "$OUT" ${VALIDATE_FLAGS:-} || exit 1
fi
[ -s "$OUT/expected.json" ] || { step "!!! no expected keys from $HOST: preparing locally"; ok=0; mv "$OUT" "$OUT-partial"; $PY -m ml.validate "$SRC" --output "$OUT" ${VALIDATE_FLAGS:-} || exit 1; }
[ -s "$OUT/results.json" ] && $PY -c "import json,sys; json.load(open(sys.argv[1]))" "$OUT/results.json" 2>/dev/null || { echo '{}' > "$OUT/results.json"; ok=0; }
[ $ok = 1 ] || echo "!!! INFERENCE INCOMPLETE (see $OUT/inference.log): missing areas use the fallback (half, compliant)"

step "export (half threshold 0.4 on the fine-tuned answer, empty check, always compliant) + coverage check"
EMPTY=(); [ -s "$OUT/results-empty.json" ] && $PY -c "import json,sys; json.load(open(sys.argv[1]))" "$OUT/results-empty.json" 2>/dev/null && EMPTY=(--empty-results "$OUT/results-empty.json")
$PY -m ml.export outputs "$OUT/results.json" --prepared "$OUT" --output "$OUT/export" --run-id "val-$NAME" --always-compliant --area-thresholds ml/lora_thresholds.json ${EMPTY[@]+"${EMPTY[@]}"} || exit 1
step "DONE: $OUT/export/submission.json"
