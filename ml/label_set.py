"""Build a prediction-blind, area-disjoint local review set from prepared images."""
import argparse
import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw
from ml.prepare import load_planogram, CORNERS


def select_samples(index, exposed):
    groups = defaultdict(lambda: defaultdict(list))
    for row in index:
        groups[row['camera_id']][row['area_id']].append(row)
    result = []
    development = {}
    for camera, areas in sorted(groups.items()):
        names = sorted(areas)
        known = [a for a in names if a in exposed]
        dev = known[0] if known else names[0]
        candidates = [a for a in names if a != dev and a not in exposed]
        if not candidates:
            raise ValueError(f'No unexposed holdout area for camera {camera}')
        holdout = sorted(candidates, key=lambda a: hashlib.sha256(a.encode()).hexdigest())[0]
        development[camera] = sorted(areas[dev], key=lambda r: int(Path(r['image_file']).stem))
        for area, split in ((dev, 'development'), (holdout, 'holdout')):
            rows = sorted(areas[area], key=lambda r: int(Path(r['image_file']).stem))
            if len(rows) < 2:
                raise ValueError('Need at least two frames per area')
            for row in (rows[0], rows[-1]):
                result.append(dict(row, split=split))
    # Extra middle frames capture opening curtains and sparse/packaged produce.
    for camera in ('6383', '6386', '6215', '6462'):
        if camera in development and len(development[camera]) > 2:
            rows = development[camera]
            result.append(dict(rows[len(rows)//2], split='development'))
    return result


def build(prepared, dataset, output):
    if output.exists():
        raise ValueError('Output already exists; preserve this fixed set and choose a new directory')
    index = json.loads((prepared/'index.json').read_text())
    exposed = set()
    for manifest in prepared.parent.glob('qwen*/sample.json'):
        exposed.update(s['area_id'] for s in json.loads(manifest.read_text()))
    samples = select_samples(index, exposed)
    cameras = load_planogram(dataset/'planogram.json')
    assets = output/'assets'
    assets.mkdir(parents=True)
    items = []
    for row in samples:
        camera, filename, area = row['camera_id'], row['image_file'], row['area_id']
        key = f'{camera}_{Path(filename).stem}_{area}'
        crop = prepared/row['crop_file']
        original = prepared/'assets'/f'{camera}_{filename}'
        target = next(a for a in cameras[camera]['products'] if a['area_id'] == area)
        with Image.open(original) as source:
            context = source.convert('RGB')
        points = [tuple(target['image_coordinates'][k]) for k in CORNERS]
        ImageDraw.Draw(context).line(points+[points[0]], fill='red', width=4)
        context.save(assets/f'{key}-context.jpg', quality=92)
        shutil.copyfile(crop, assets/f'{key}-crop.png')
        items.append(dict(id=key, camera_id=camera, image_file=filename, area_id=area,
                          product_name=row['product_name'], split=row['split'],
                          captured_at=datetime.fromtimestamp(int(Path(filename).stem), timezone.utc).isoformat(),
                          valid_fraction=row['valid_fraction'], crop=f'assets/{key}-crop.png',
                          context=f'assets/{key}-context.jpg',
                          image_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                          crop_sha256=hashlib.sha256(crop.read_bytes()).hexdigest()))
    manifest = dict(schema_version=1, protocol=dict(
        stock='empty: no produce; half: some produce with substantial unfilled space; full: full/nearly full. Provisional visual definitions; uncertain when ambiguous.',
        compliance='Visible product type matches expected product; do not guess cultivar, brand or origin. Empty/blocked areas have unknown compliance.',
        holdout='Area-disjoint and excludes all areas in existing qwen sample manifests. Keep holdout results out of prompt tuning.'), items=items)
    manifest['set_id'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:16]
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    html = Path(__file__).with_name('label_review.html').read_text()
    payload = json.dumps(manifest).replace('<', '\\u003c')
    (output/'index.html').write_text(html.replace('__MANIFEST__', payload).replace('__SUGGESTIONS__', '{}'))
    print(f'{len(items)} observations; {sum(x["split"]=="development" for x in items)} development; '
          f'{sum(x["split"]=="holdout" for x in items)} holdout; set {manifest["set_id"]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, default=Path('data/prepared-v1'))
    parser.add_argument('--dataset', type=Path, default=Path('new_dataset_hackathon_junctionx_10_oct_2026_v2'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.prepared, args.dataset, args.output)
