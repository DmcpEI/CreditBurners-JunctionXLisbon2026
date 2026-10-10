"""Read a Sensei image ZIP without extracting arbitrary paths; prepare crops and baselines."""
import argparse
import io
import json
import math
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from PIL import Image, ImageStat

from ml.scoring import LEVELS, validate_submission

CORNERS = ("top_left", "top_right", "bottom_right", "bottom_left")


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n")
    temporary.replace(path)


def load_planogram(path):
    cameras = json.loads(path.read_text())["Frutas e Legumes"]["cameras"]
    seen = set()
    if not cameras:
        raise ValueError("Planogram has no cameras")
    for camera, data in cameras.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]+", camera) or not data["products"]:
            raise ValueError(f"Invalid/empty camera: {camera}")
        for area in data["products"]:
            name = area["area_id"]
            if not re.fullmatch(r"[A-Za-z0-9_-]+", name) or name in seen:
                raise ValueError(f"Invalid/duplicate area: {name}")
            seen.add(name)
            points = [area["image_coordinates"][key] for key in CORNERS]
            if any(len(p) != 2 or any(type(v) not in (int, float)
                   or not math.isfinite(v) or abs(v) > 10000 for v in p) for p in points):
                raise ValueError(f"Invalid coordinates: {name}")
            cross = []
            for i in range(4):
                a, b, c = (points[j % 4] for j in (i, i+1, i+2))
                cross.append((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))
            if not (all(v > 0 for v in cross) or all(v < 0 for v in cross)):
                raise ValueError(f"Non-convex/degenerate quadrilateral: {name}")
    return cameras


def crop_area(image, coordinates):
    tl, tr, br, bl = [coordinates[k] for k in CORNERS]
    width = math.ceil(max(math.dist(tl, tr), math.dist(bl, br)))
    height = math.ceil(max(math.dist(tl, bl), math.dist(tr, br)))
    if not (0 < width <= 4096 and 0 < height <= 4096):
        raise ValueError("Invalid crop dimensions")
    # Pillow QUAD maps TL, BL, BR, TR into a rectangle; sample the validity mask identically.
    quad = tuple(v for p in (tl, bl, br, tr) for v in p)
    crop = image.transform((width, height), Image.Transform.QUAD, quad,
                           resample=Image.Resampling.BICUBIC, fillcolor=(0, 0, 0))
    valid = Image.new("L", image.size, 255).transform(
        (width, height), Image.Transform.QUAD, quad,
        resample=Image.Resampling.NEAREST, fillcolor=0)
    return crop, valid


def prepare(dataset, output):
    cameras = load_planogram(dataset/"planogram.json")
    archives = list(dataset.glob("*.zip"))
    if len(archives) != 1:
        raise ValueError("Expected exactly one image ZIP in the dataset directory")
    if output.exists():
        raise ValueError("Output already exists; choose a new directory to preserve prior runs")
    baselines = {level: {} for level in LEVELS}
    snapshots, expected, index = [], [], []
    sizes, camera_counts, clipped = Counter(), Counter(), set()
    processed = datetime.now(timezone.utc).isoformat()
    with zipfile.ZipFile(archives[0]) as archive:
        members = []
        seen = set()
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if (info.is_dir() or "__MACOSX" in path.parts or path.name.startswith(".")
                    or path.suffix.lower() not in (".jpg", ".jpeg", ".png")):
                continue
            camera = path.parent.name
            key = camera, path.stem
            if camera not in cameras or not path.stem.isdecimal() or key in seen:
                raise ValueError(f"Unknown camera, invalid timestamp or duplicate image: {path}")
            if info.file_size > 30_000_000:
                raise ValueError(f"Image too large: {path}")
            datetime.fromtimestamp(int(path.stem), timezone.utc)
            seen.add(key)
            members.append((camera, path, info))
        if not members:
            raise ValueError("No camera images in archive")
        output.mkdir(parents=True)
        assets = output/"assets"
        assets.mkdir()
        for camera, path, info in sorted(members, key=lambda x: (x[0], int(x[1].stem))):
            raw = archive.read(info)
            with Image.open(io.BytesIO(raw)) as source:
                if source.width*source.height > 20_000_000:
                    raise ValueError(f"Image dimensions too large: {path}")
                image = source.convert("RGB")
            sizes[f"{image.width}x{image.height}"] += 1
            camera_counts[camera] += 1
            snapshot_id = f"{camera}_{path.stem}"
            image_file = f"{snapshot_id}{path.suffix.lower()}"
            (assets/image_file).write_bytes(raw)
            areas = []
            for level in LEVELS:
                baselines[level].setdefault(camera, {})[path.name] = {}
            for area in cameras[camera]["products"]:
                area_id = area["area_id"]
                expected.append([camera, path.name, area_id])
                crop, valid = crop_area(image, area["image_coordinates"])
                crop_file = f"{snapshot_id}_{area_id}.png"
                mask_file = f"{snapshot_id}_{area_id}_valid.png"
                crop.save(assets/crop_file)
                valid.save(assets/mask_file)
                fraction = ImageStat.Stat(valid).mean[0]/255
                if fraction < 1:
                    clipped.add(area_id)
                index.append(dict(camera_id=camera, image_file=path.name, area_id=area_id,
                                  product_name=area["product_name"],
                                  crop_file=f"assets/{crop_file}", valid_mask_file=f"assets/{mask_file}",
                                  width=crop.width, height=crop.height, valid_fraction=fraction))
                for level, value in LEVELS.items():
                    baselines[level][camera][path.name][area_id] = dict(
                        planogram_compliant=True, stock_level=level, stock_value=value)
                areas.append(dict(area_id=area_id, product_name=area["product_name"],
                                  **baselines["half"][camera][path.name][area_id],
                                  visibility="unknown", fallback_used=True,
                                  crop_url=f"/assets/{crop_file}", reference=None,
                                  reason="Constant baseline: assumes compliant/half; image not classified."))
            snapshots.append(dict(snapshot_id=snapshot_id, run_id="constant-half-v1",
                                  camera_id=camera, image_file=path.name,
                                  captured_at=datetime.fromtimestamp(int(path.stem), timezone.utc).isoformat(),
                                  processed_at=processed, prediction_source="saved",
                                  context_mode="current_image_only", image_url=f"/assets/{image_file}", areas=areas))
    for level, submission in baselines.items():
        validate_submission(submission, expected)
        write_json(output/f"baseline-{level}.json", submission)
    report = dict(images=len(snapshots), cameras=len(camera_counts),
                  planogram_areas=sum(len(c["products"]) for c in cameras.values()),
                  area_observations=len(expected), image_sizes=dict(sizes),
                  images_per_camera=dict(camera_counts), clipped_areas=sorted(clipped),
                  cameras_without_images=sorted(set(cameras)-set(camera_counts)),
                  ground_truth_loaded=False,
                  note="Unscored constant baselines. No model inference or visibility detection performed.")
    write_json(output/"expected.json", expected)
    write_json(output/"index.json", index)
    write_json(output/"snapshots.json", snapshots)
    write_json(output/"report.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.dataset, args.output), indent=2))
