"""YOLO classification baselines on shelf crops (experiment, 11 October 2026; runs on a laptop, Apple MPS).

stock:   empty/half/full classifier, the same 5 folds as ml/lora_cv.py, out-of-fold scores written in lora_cv's format
         (A empty / B half / C full) so `python -m ml.lora_cv --score` compares it directly with the LoRA settings.
final:   the stock classifier trained on all labelled crops -> models/yolo-stock-v1.pt (used with the LoRA, 50/50).
predict: stock scores (A/B/C) for every crop of a manifest (validation run), for ml.export --yolo-results.
product: which planogram product a crop shows (one class per product name), trained on unlabelled crops; scores the
         labelled observations with P(own planogram product) for the wrong-product check.
"""
import argparse
import json
import shutil
from pathlib import Path

ASSETS = Path("data/prepared-v1/assets")
CURTAIN = ("6383_1751001156", "6386_1751001156")


PAD = False  # --pad: square-pad crops (black, like out-of-view pixels) so ultralytics' Resize + CenterCrop keeps the whole tray


def square(image):
    from PIL import Image
    image = image.convert("RGB")
    side = max(image.size)
    canvas = Image.new("RGB", (side, side))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def source(path):
    """What the classifier sees: the crop path, or the square-padded crop."""
    from PIL import Image
    return square(Image.open(path)) if PAD else str(path)


def link(paths_by_class, root):
    from PIL import Image
    for cls, ids in paths_by_class.items():
        (root / cls).mkdir(parents=True, exist_ok=True)
        for i in ids:
            if PAD:
                square(Image.open(ASSETS / f"{i}.png")).save(root / cls / f"{i}.png")
            else:
                (root / cls / f"{i}.png").symlink_to((ASSETS / f"{i}.png").resolve())


def train(data, out, args):
    from ultralytics import YOLO
    model = YOLO(args.weights)
    model.train(data=str(data), epochs=args.epochs, imgsz=args.imgsz, batch=32, device=args.device, project=str(out),
                name="run", exist_ok=True, verbose=False, plots=False, seed=0, val=False)  # ultralytics val crashes on MPS; we score held-out crops ourselves
    return model


def stock(args):
    from ml.lora_cv import folds
    labels = json.loads(Path("data/finetune-v1/labels.json").read_text())
    manifest = {s["sample_id"] for s in json.loads(Path("data/labelled-v3/sample.json").read_text())}
    ids = [i for i in labels if i in manifest]
    out, oof = args.work / "stock", {}
    for f, test in enumerate(folds(ids, 5)):
        root = out / f"fold{f}"
        shutil.rmtree(root, ignore_errors=True)
        rest = [i for i in ids if i not in set(test)]
        link({c: [i for i in rest if labels[i] == c] for c in ("empty", "half", "full")}, root / "train")
        link({c: [i for i in test if labels[i] == c] for c in ("empty", "half", "full")}, root / "val")
        model = train(root, root, args)
        for i in test:
            probs = model.predict(source(ASSETS / f"{i}.png"), imgsz=args.imgsz, device=args.device, verbose=False)[0].probs.data.tolist()
            p = dict(zip(model.names.values(), probs))
            oof[i] = dict(A=p["empty"], B=p["half"], C=p["full"], D=0.0)
        print(f"fold {f + 1}/5 done", flush=True)
    target = Path("data/lora-cv") / f"yolo-{Path(args.weights).stem}-e{args.epochs}{'' if args.imgsz == 224 else f'-i{args.imgsz}'}{'-pad' if PAD else ''}.json"
    target.write_text(json.dumps(oof) + "\n")
    print(f"STOCK_DONE {target}", flush=True)


def product(args):
    snapshots = json.loads(Path("results/qwen3.8-27b-ctx640-lora-emptycheck-alwayscompliant-full-v1/snapshots.json").read_text())
    rows = [(f"{s['snapshot_id']}_{a['area_id']}", a["product_name"], a["stock_level"]) for s in snapshots
            if s["snapshot_id"] not in CURTAIN for a in s["areas"]]
    held = set(json.loads(Path(args.eval_ids).read_text()))
    names = sorted({n for _, n, _ in rows})
    cls = {n: f"p{k:03d}" for k, n in enumerate(names)}
    train_rows = [(i, n) for i, n, st in rows if i not in held and st != "empty"]
    root = args.work / "product"
    shutil.rmtree(root, ignore_errors=True)
    by = {}
    for i, n in train_rows:
        by.setdefault(cls[n], []).append(i)
    link(by, root / "train")
    link({c: v[:1] for c, v in by.items()}, root / "val")  # ultralytics needs a val split; real evaluation is below
    model = train(root, root, args)
    index = {v: k for k, v in model.names.items()}
    scores = {}
    for i, n, st in rows:
        if i in held:
            probs = model.predict(source(ASSETS / f"{i}.png"), imgsz=args.imgsz, device=args.device, verbose=False)[0].probs.data.tolist()
            own = probs[index[cls[n]]] if cls[n] in index else 0.0
            scores[i] = dict(own=own, top=max(probs), stock=st)
    target = Path("data/compliance-review") / f"yolo-product-{Path(args.weights).stem}-e{args.epochs}.json"
    target.write_text(json.dumps(scores) + "\n")
    print(f"PRODUCT_DONE {target} ({len(train_rows)} training crops, {len(by)} products)", flush=True)


def final(args):
    labels = json.loads(Path("data/finetune-v1/labels.json").read_text())
    manifest = {s["sample_id"] for s in json.loads(Path("data/labelled-v3/sample.json").read_text())}
    ids = [i for i in labels if i in manifest]
    root = args.work / "final"
    shutil.rmtree(root, ignore_errors=True)
    link({c: [i for i in ids if labels[i] == c] for c in ("empty", "half", "full")}, root / "train")
    link({c: [i for i in ids if labels[i] == c][:1] for c in ("empty", "half", "full")}, root / "val")
    model = train(root, root, args)
    Path("models").mkdir(exist_ok=True)
    target = f"models/yolo-stock-v1{'-pad' if PAD else ''}.pt"
    shutil.copy(model.trainer.last, target)  # ultralytics 8.4 nests relative projects under runs/classify/
    print(f"FINAL_DONE {target} ({len(ids)} labels)", flush=True)


def predict(args):
    from ultralytics import YOLO
    model = YOLO(args.weights)
    manifest = Path(args.manifest)
    out = {}
    for sample in json.loads(manifest.read_text()):
        probs = model.predict(source(manifest.parent / sample["crop"]), imgsz=args.imgsz, device=args.device, verbose=False)[0].probs.data.tolist()
        p = dict(zip(model.names.values(), probs))
        out[sample["sample_id"]] = dict(A=p["empty"], B=p["half"], C=p["full"])
    Path(args.output).write_text(json.dumps(out) + "\n")
    print(f"scored {len(out)} crops -> {args.output}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=["stock", "product", "final", "predict"])
    parser.add_argument("--manifest", help="predict: sample.json of a prepared run")
    parser.add_argument("--output", help="predict: output JSON")
    parser.add_argument("--weights", default="yolo11s-cls.pt")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=224)
    parser.add_argument("--device", default="mps")
    parser.add_argument("--work", type=Path, default=Path("data/yolo"))
    parser.add_argument("--eval-ids", default="data/compliance-review/eval-ids.json")
    parser.add_argument("--pad", action="store_true", help="Square-pad crops for training and prediction (whole tray visible)")
    args = parser.parse_args()
    PAD = args.pad
    dict(stock=stock, product=product, final=final, predict=predict)[args.task](args)
