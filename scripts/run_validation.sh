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
STOCK_ADAPTER=/workspace/models/lora-stock-v2; CHECK_ADAPTER=/workspace/models/lora-compliance-v1; CT=${COMPLIANCE_THRESHOLD:-0.6}
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
  [ "${PIPESTATUS[0]}" = 0 ] || { step "!!! preparation failed on $HOST (see $OUT-prepare.log); fix the input or VALIDATE_FLAGS and rerun with a new name"; exit 1; }
  ssh "$HOST" "cat $REMOTE/$OUT/crops-sheet.jpg" > "$OUT-crops-sheet.jpg" 2>/dev/null && { step "CHECK $OUT-crops-sheet.jpg now (opening it): wrong crops = Ctrl-C"; open "$OUT-crops-sheet.jpg" 2>/dev/null || true; }
  ssh "$HOST" 'for i in $(seq 1 120); do f=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1); [ "$f" -ge 60000 ] && exit 0; [ $i = 1 ] && echo "!!! GPU busy (${f} MiB free; the models need ~60 GB): waiting up to 30 min, stop the other job if it is ours"; sleep 15; done; exit 1' || step "!!! GPU still busy: continuing; failed areas fall back to YOLO"
  step "inference on $HOST (Qwen3.8-27B + LoRA stock question; empty check on the base model when needed)"
  ssh "$HOST" "cd $REMOTE && $RPY -B -u -m ml.infer_sample $OUT/sample.json --model /workspace/models/qwen3.8-27b --stock-prompt v1 --paired-prompt v4 --paired-output $OUT/results-empty.json --paired-only-if-full-below 0.5 --questions stock --context-max-side 640 --adapter $STOCK_ADAPTER --output $OUT/results.json" > "$OUT/inference.log" 2>&1 || ok=0
  step "product check on $HOST (trained crop/name LoRA)"
  ssh "$HOST" "cd $REMOTE && $RPY -B -u -m ml.compliance_lora $OUT/sample.json --adapter-in $CHECK_ADAPTER --model /workspace/models/qwen3.8-27b --output $OUT/results-compliance.json" > "$OUT/compliance.log" 2>&1 || echo "!!! product check failed: answering compliant everywhere"
  step "fetch results"
  for f in expected sample report results results-empty results-compliance; do ssh "$HOST" "cat $REMOTE/$OUT/$f.json" > "$OUT/$f.json" || ok=0; done
  ssh "$HOST" "tar -C $REMOTE/$OUT -cf - assets" | tar -C "$OUT" -xf - || echo "!!! crops/photos not fetched (app only; submission unaffected)"
else
  ok=0
  step "!!! $HOST unreachable: preparing locally for a fallback submission"
  rmdir "$OUT"; $PY -m ml.validate "$SRC" --output "$OUT" ${VALIDATE_FLAGS:-} || exit 1
fi
[ -s "$OUT/expected.json" ] || { step "!!! no expected keys from $HOST: preparing locally"; ok=0; mv "$OUT" "$OUT-partial"; $PY -m ml.validate "$SRC" --output "$OUT" ${VALIDATE_FLAGS:-} || exit 1; }
[ -s "$OUT/results.json" ] && $PY -c "import json,sys; json.load(open(sys.argv[1]))" "$OUT/results.json" 2>/dev/null || { echo '{}' > "$OUT/results.json"; ok=0; }
[ $ok = 1 ] || echo "!!! INFERENCE INCOMPLETE (see $OUT/inference.log): missing areas use the fallback (half, compliant)"

step "YOLO stock scores on this laptop (models/yolo-stock-v1-pad.pt, square-padded crops), averaged with the VLM's"
YOLO=(); if [ -d "$OUT/assets" ] && $PY -B -m ml.yolo_cls predict --pad --weights models/yolo-stock-v1-pad.pt --manifest "$OUT/sample.json" --output "$OUT/results-yolo.json" --device cpu > "$OUT/yolo.log" 2>&1; then YOLO=(--yolo-results "$OUT/results-yolo.json"); else echo "!!! YOLO step failed (see $OUT/yolo.log): VLM stock only"; fi
step "export (YOLO+VLM stock, half if >= 0.4, empty check, product check B >= $CT) + coverage check"
CHECK=(); [ -s "$OUT/results-compliance.json" ] && $PY -c "import json,sys; json.load(open(sys.argv[1]))" "$OUT/results-compliance.json" 2>/dev/null && CHECK=(--compliance-results "$OUT/results-compliance.json" --compliance-threshold "$CT")
EMPTY=(); [ -s "$OUT/results-empty.json" ] && $PY -c "import json,sys; json.load(open(sys.argv[1]))" "$OUT/results-empty.json" 2>/dev/null && EMPTY=(--empty-results "$OUT/results-empty.json")
$PY -m ml.export outputs "$OUT/results.json" --prepared "$OUT" --output "$OUT/export" --run-id "val-$NAME" --always-compliant --area-thresholds ml/lora_thresholds.json ${EMPTY[@]+"${EMPTY[@]}"} ${CHECK[@]+"${CHECK[@]}"} ${YOLO[@]+"${YOLO[@]}"} || exit 1
$PY - "$OUT/export/submission.json" "${EXPECT_IMAGES:-26}" "${EXPECT_AREAS:-289}" <<'PYEOF'
import json, sys
sub = json.load(open(sys.argv[1])); images = sum(len(v) for v in sub.values()); areas = sum(len(a) for v in sub.values() for a in v.values())
ok = (images, areas) == (int(sys.argv[2]), int(sys.argv[3]))
print(f"{'OK' if ok else '!!! CHECK'}: {len(sub)} cameras, {images} images, {areas} areas (organiser: {sys.argv[2]} images, {sys.argv[3]} areas)")
PYEOF
step "DONE: $OUT/export/submission.json"
[ -d "$OUT/assets" ] && echo "App on this run: java -jar api/target/sensei-0.1.0.jar --sensei.data-dir=$OUT --sensei.snapshots-file=$OUT/export/snapshots.json"
