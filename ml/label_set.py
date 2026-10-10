"""Build a prediction-blind, area-disjoint local review set from prepared images."""
import argparse
import hashlib
import json
import re
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


PACKAGED = re.compile(r'EMB|(?<![/\d])\d+(?:[.,]\d+)?\s*(?:G|GR|KG)\b')  # weight in name; '73/85 KG' is a loose caliber
SPLIT_COUNTS = dict(development=50, holdout=20, evaluation=70)


def spread(rows, k):
    """k frames spread over the day (rows sorted by time)."""
    rows = sorted(rows, key=lambda r: int(Path(r['image_file']).stem))
    return [rows[min(len(rows)-1, int((j+0.5)*len(rows)/k))] for j in range(min(k, len(rows)))]


def hashed(text):
    return hashlib.sha256(text.encode()).hexdigest()


def select_expansion(index, previous_items, exposed, excluded_images, counts=SPLIT_COUNTS):
    """New observations only. Old areas keep their split; never-used areas form a new evaluation group."""
    split = {x['area_id']: x['split'] for x in previous_items}
    for area in exposed - set(split):
        split[area] = 'development'  # used in prompt experiments: never evaluation
    used = {(x['camera_id'], x['image_file'], x['area_id']) for x in previous_items}
    areas = defaultdict(list)
    for row in index:
        if (row['camera_id'], row['image_file']) in excluded_images or (row['camera_id'], row['image_file'], row['area_id']) in used:
            continue
        areas[row['area_id']].append(row)
    result = []
    for name in ('development', 'holdout'):
        pool = sorted((a for a, s in split.items() if s == name), key=hashed)
        base, extra = divmod(counts[name], len(pool))
        for i, area in enumerate(pool):
            result += [dict(r, split=name) for r in spread(areas[area], base + (i < extra))]
    by_camera = defaultdict(list)
    for area, rows in areas.items():
        if area not in split:
            by_camera[rows[0]['camera_id']].append(area)
    per_camera, seen_products = counts['evaluation'] // len(by_camera), set()
    for camera in sorted(by_camera):
        # packaged first, then products not yet chosen, then a stable hash order
        names = sorted(by_camera[camera], key=lambda a: (not PACKAGED.search(areas[a][0]['product_name']),
                                                         areas[a][0]['product_name'] in seen_products, hashed(a)))
        chosen = names[:per_camera]
        seen_products.update(areas[a][0]['product_name'] for a in chosen)
        frames = [len(chosen) and per_camera // len(chosen) + (i < per_camera % len(chosen)) for i in range(len(chosen))]
        picks = [r for a, k in zip(chosen, frames) for r in spread(areas[a], k)]
        # rotate start times so one camera's areas cover morning to evening
        times = sorted({r['image_file'] for a in chosen for r in areas[a]}, key=lambda f: int(Path(f).stem))
        for j, area in enumerate(chosen):
            if frames[j] == 1:
                target = times[min(len(times)-1, int((j+0.5)*len(times)/len(chosen)))]
                picks = [r for r in picks if r['area_id'] != area] + [min(areas[area], key=lambda r: abs(int(Path(r['image_file']).stem)-int(Path(target).stem)))]
        result += [dict(r, split='evaluation') for r in picks]
    return result


def outlined_context(original, coordinates):
    with Image.open(original) as source:
        context = source.convert('RGB')
    points = [tuple(coordinates[k]) for k in CORNERS]
    ImageDraw.Draw(context).line(points+[points[0]], fill='red', width=4)
    return context


def make_item(row, prepared, cameras, assets):
    camera, filename, area = row['camera_id'], row['image_file'], row['area_id']
    key = f'{camera}_{Path(filename).stem}_{area}'
    crop = prepared/row['crop_file']
    original = prepared/'assets'/f'{camera}_{filename}'
    target = next(a for a in cameras[camera]['products'] if a['area_id'] == area)
    outlined_context(original, target['image_coordinates']).save(assets/f'{key}-context.jpg', quality=92)
    shutil.copyfile(crop, assets/f'{key}-crop.png')
    return dict(id=key, camera_id=camera, image_file=filename, area_id=area,
                product_name=row['product_name'], split=row['split'],
                captured_at=datetime.fromtimestamp(int(Path(filename).stem), timezone.utc).isoformat(),
                valid_fraction=row['valid_fraction'], crop=f'assets/{key}-crop.png',
                context=f'assets/{key}-context.jpg',
                image_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                crop_sha256=hashlib.sha256(crop.read_bytes()).hexdigest())


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
    items = [make_item(row, prepared, cameras, assets) for row in samples]
    manifest = dict(schema_version=1, protocol=dict(
        stock='Judge supplied polygon only, relative to capacity for this product. Empty includes nearly depleted; half is intermediate stock; full is full/nearly full. No exact numeric thresholds supplied; uncertain when ambiguous.',
        compliance='Visible product type matches expected product; do not guess cultivar, brand or origin. No-visible-produce/blocked areas have unknown compliance; near-empty stock with visible produce may still match.',
        holdout='Area-disjoint and excludes all areas in existing qwen sample manifests. Keep holdout results out of prompt tuning.'), items=items)
    manifest['set_id'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:16]
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    render_page(output)
    print(f'{len(items)} observations; {sum(x["split"]=="development" for x in items)} development; '
          f'{sum(x["split"]=="holdout" for x in items)} holdout; set {manifest["set_id"]}')


def render_page(output, suggestions=None, references=None):
    """(Re)write only index.html; the manifest is never touched."""
    manifest = json.loads((output/'manifest.json').read_text())
    safe = lambda x: json.dumps(x).replace('<', '\\u003c')
    html = Path(__file__).with_name('label_review.html').read_text()
    (output/'index.html').write_text(html.replace('__MANIFEST__', safe(manifest)).replace('__SUGGESTIONS__', safe(suggestions or {}))
                                     .replace('__REFERENCES__', safe(references or {})))


def build_expansion(prepared, dataset, previous_dir, labels, output, excluded_images):
    """Versioned 140-crop expansion; previous manifest, labels and browser storage stay untouched."""
    if output.exists():
        raise ValueError('Output already exists; preserve this fixed set and choose a new directory')
    previous = json.loads((previous_dir/'manifest.json').read_text())
    exposed = set()
    for sample in prepared.parent.glob('*/sample.json'):
        exposed.update(s['area_id'] for s in json.loads(sample.read_text()))
    rows = select_expansion(json.loads((prepared/'index.json').read_text()), previous['items'], exposed, excluded_images)
    cameras = load_planogram(dataset/'planogram.json')
    assets = output/'assets'
    assets.mkdir(parents=True)
    items = [make_item(row, prepared, cameras, assets) for row in rows]
    manifest = dict(schema_version=2, previous_set_id=previous['set_id'], protocol=dict(
        revision='sensei-box-capacity-v3',
        stock='Judge only the supplied polygon, relative to capacity for this product (not the whole physical tray). Empty includes nearly depleted; half is intermediate; full is full/nearly full. Two large fruits may be half while two lemons may be empty; examples, not count thresholds. Uncertain when ambiguous.',
        compliance='Visible product type matches the expected product; no cultivar, brand or origin from appearance. A genuinely empty area is compliant; near-empty stock of a wrong product can be non-compliant.',
        splits='Areas keep their v1 split (development/holdout); areas used in any experiment are development; never-used areas form the evaluation group. Do not tune on holdout or evaluation.',
        exclusions='Closed-curtain images ' + ', '.join(f'{c}/{f}' for c, f in sorted(excluded_images)) + ' excluded.'), items=items)
    manifest['set_id'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:16]
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    review = json.loads(labels.read_text())
    references = defaultdict(list)
    for item in review['items']:
        references[item['area_id']].append(dict(captured_at=item['captured_at'], split=item['split'], **{
            k: item['label'][k] for k in ('visibility', 'stock_level', 'planogram_compliant', 'notes')}))
    (output/'references.json').write_text(json.dumps(references, indent=2)+'\n')
    render_page(output, {}, references)
    print(f'{len(items)} observations; ' + '; '.join(f'{sum(x["split"]==s for x in items)} {s}' for s in SPLIT_COUNTS)
          + f'; set {manifest["set_id"]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, default=Path('data/prepared-v1'))
    parser.add_argument('--dataset', type=Path, default=Path('new_dataset_hackathon_junctionx_10_oct_2026_v2'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expand-from', type=Path, help='Previous review set dir: build the versioned 140-crop expansion')
    parser.add_argument('--labels', type=Path, default=Path('data/ground-truth/human-v2-frozen.json'))
    parser.add_argument('--exclude-image', action='append', default=[], metavar='CAMERA/FILE',
                        help='Confirmed closed-curtain image to leave out')
    parser.add_argument('--suggestions', type=Path, help='Only re-render index.html of --output with these suggestions')
    args = parser.parse_args()
    if args.suggestions:
        render_page(args.output, json.loads(args.suggestions.read_text()),
                    json.loads((args.output/'references.json').read_text()))
    elif args.expand_from:
        build_expansion(args.prepared, args.dataset, args.expand_from, args.labels, args.output,
                        {tuple(x.split('/')) for x in args.exclude_image})
    else:
        build(args.prepared, args.dataset, args.output)
