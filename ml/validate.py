"""Prepare final-validation images (folder or ZIP, camera folders or flat) for inference + export.

Writes crops, masks, outlined contexts, sample.json and expected.json (every planogram area of every image).
Camera = parent folder name when it is a planogram camera id, else the camera whose reference view is closest.
"""
import argparse
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from PIL import Image, ImageDraw, ImageStat
from ml.label_set import outlined_context
from ml.prepare import crop_area, load_planogram, write_json

SUFFIXES = (".jpg", ".jpeg", ".png")


def read_images(source):
    """(relative path, bytes) for every image in a directory or ZIP, skipping macOS metadata."""
    if source.is_dir():
        files = [(p.relative_to(source).as_posix(), p.read_bytes()) for p in sorted(source.rglob("*")) if p.is_file()]
    else:
        with zipfile.ZipFile(source) as archive:
            files = [(i.filename, archive.read(i)) for i in archive.infolist()
                     if not i.is_dir() and i.file_size <= 30_000_000]
    return [(PurePosixPath(name), data) for name, data in files
            if "__MACOSX" not in PurePosixPath(name).parts and not PurePosixPath(name).name.startswith(".")
            and PurePosixPath(name).suffix.lower() in SUFFIXES]


def thumbnail(image):
    return image.convert("L").resize((64, 36))


def camera_references(reference_dir, cameras):
    """One grey thumbnail per camera from previously prepared images (any frame of the day)."""
    refs = {}
    for camera in cameras:
        frames = sorted(reference_dir.glob(f"{camera}_*.jpg"))
        if frames:
            with Image.open(frames[len(frames) // 2]) as image:
                refs[camera] = thumbnail(image)
    return refs


def distance(a, b):
    return sum(abs(x - y) for x, y in zip(a.getdata(), b.getdata())) / (64 * 36)


MIN_CAMERA_MARGIN = 1.3  # next-best / best distance; rehearsal minimum was 1.69


def contact_sheet(samples, output, per_row=16, size=(96, 64)):
    """All crops on one sheet, labelled camera/area, for a visual check before trusting the run."""
    rows = (len(samples) + per_row - 1) // per_row
    sheet = Image.new("RGB", (per_row * (size[0] + 4), rows * (size[1] + 16)), "white")
    draw = ImageDraw.Draw(sheet)
    for i, sample in enumerate(samples):
        x, y = (i % per_row) * (size[0] + 4), (i // per_row) * (size[1] + 16)
        with Image.open(output / sample["crop"]) as crop:
            crop = crop.convert("RGB")
            crop.thumbnail(size)
            sheet.paste(crop, (x, y))
        draw.text((x, y + size[1] + 2), sample["area_id"], fill="black")
    sheet.save(output / "crops-sheet.jpg", quality=80)


def prepare_validation(source, dataset, output, reference_dir, allow_other_size=False, trust_inferred_cameras=False):
    if output.exists():
        raise ValueError("Output exists; choose a new directory")
    cameras = load_planogram(dataset / "planogram.json")
    files = read_images(source)
    if not files:
        raise ValueError(f"No images found in {source}")
    refs = None
    (output / "assets").mkdir(parents=True)
    samples, expected, images = [], [], []
    for path, raw in files:
        with Image.open(io.BytesIO(raw)) as decoded:
            if decoded.width * decoded.height > 20_000_000:
                raise ValueError(f"Image too large: {path}")
            image = decoded.convert("RGB")
        camera, how = path.parent.name, "folder"
        if camera not in cameras:
            refs = refs or camera_references(reference_dir, cameras)
            if not refs:
                raise ValueError("Images are not in camera folders and no reference images exist; run ml.prepare first")
            ranked = sorted((distance(thumbnail(image), ref), cam) for cam, ref in refs.items())
            camera, how = ranked[0][1], f"inferred (distance {ranked[0][0]:.1f}, next {ranked[1][1]} {ranked[1][0]:.1f})"
            if ranked[1][0] < MIN_CAMERA_MARGIN * ranked[0][0] and not trust_inferred_cameras:
                raise ValueError(f"{path}: camera match unclear ({how}); put images in camera folders or pass --trust-inferred-cameras")
        stem = path.stem
        if any(x["camera_id"] == camera and x["image_file"] == path.name for x in images):
            raise ValueError(f"Duplicate image {camera}/{path.name}")
        if image.size != (1280, 720) and not allow_other_size:
            raise ValueError(f"{path}: size {image.size}; planogram coordinates assume 1280x720 (crops would be wrong). "
                             "Pass --allow-other-size only after checking the crops sheet")
        original = output / "assets" / f"{camera}_{stem}{path.suffix.lower()}"
        original.write_bytes(raw)
        images.append(dict(source=str(path), camera_id=camera, image_file=path.name, camera_source=how, size=list(image.size)))
        for area in cameras[camera]["products"]:
            area_id, key = area["area_id"], f"{camera}_{stem}_{area['area_id']}"
            crop, valid = crop_area(image, area["image_coordinates"])
            crop.save(output / "assets" / f"{key}.png")
            valid.save(output / "assets" / f"{key}_valid.png")
            outlined_context(original, area["image_coordinates"]).save(output / "assets" / f"{key}-context.jpg", quality=92)
            expected.append([camera, path.name, area_id])
            samples.append(dict(sample_id=key, camera_id=camera, image_file=path.name, area_id=area_id,
                                product_name=area["product_name"], context=f"assets/{key}-context.jpg",
                                crop=f"assets/{key}.png", mask=f"assets/{key}_valid.png",
                                valid_fraction=ImageStat.Stat(valid).mean[0] / 255))
    write_json(output / "sample.json", samples)
    contact_sheet(samples, output)
    write_json(output / "expected.json", expected)
    report = dict(source=str(source), prepared_at=datetime.now(timezone.utc).isoformat(), images=images,
                  image_count=len(images), area_count=len(expected),
                  cameras=sorted({x["camera_id"] for x in images}),
                  inferred_cameras=sum(x["camera_source"] != "folder" for x in images))
    write_json(output / "report.json", report)
    for x in images:
        print(f"{x['source']} -> camera {x['camera_id']} ({x['camera_source']})")
    print(f"{len(images)} images, {len(expected)} areas, {len(report['cameras'])} cameras -> {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Folder or ZIP of validation images")
    parser.add_argument("--dataset", type=Path, default=Path("new_dataset_hackathon_junctionx_10_oct_2026_v2"))
    parser.add_argument("--references", type=Path, default=Path("data/prepared-v1/assets"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-other-size", action="store_true")
    parser.add_argument("--trust-inferred-cameras", action="store_true")
    args = parser.parse_args()
    prepare_validation(args.source, args.dataset, args.output, args.references, args.allow_other_size, args.trust_inferred_cameras)
