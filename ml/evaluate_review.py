"""Validate frozen human reviews, prepare split inputs, and score independent tasks."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from ml.scoring import LEVELS, PAYOFF


def load_review(path, manifest_path):
    review = json.loads(path.read_text())
    manifest = json.loads(manifest_path.read_text())
    if review.get('status') != 'frozen' or not review.get('reviewer') or not review.get('frozen_at'):
        raise ValueError('A frozen named human review is required')
    if review.get('set_id') != manifest['set_id'] or review.get('protocol', {}).get('revision') != 'sensei-box-capacity-v2':
        raise ValueError('Wrong set or annotation protocol')
    expected = {x['id']: x for x in manifest['items']}
    items = review['items']
    if len(items) != len(expected) or {x['id'] for x in items} != set(expected):
        raise ValueError('Missing, duplicate or unexpected review IDs')
    for item in items:
        if any(item[k] != expected[item['id']][k] for k in expected[item['id']]):
            raise ValueError('Review metadata differs from original manifest')
        label = item.get('label')
        if not label or label.get('protocol_revision') != 'sensei-box-capacity-v2':
            raise ValueError('Unreviewed or old-protocol label')
        if label.get('visibility') not in ('clear', 'occluded', 'unknown'):
            raise ValueError('Invalid visibility')
        if label.get('stock_level') is not None and label['stock_level'] not in LEVELS:
            raise ValueError('Invalid stock label')
        if label.get('planogram_compliant') is not None and type(label['planogram_compliant']) is not bool:
            raise ValueError('Invalid compliance label')
        if label['visibility'] != 'clear' and (label['stock_level'] is not None or label['planogram_compliant'] is not None):
            raise ValueError('Blocked/unknown view has a definite task label')
    return review


def evaluate(items, predictions):
    expected = {x['id'] for x in items}
    if set(predictions) != expected:
        raise ValueError('Prediction coverage must match selected split exactly')
    result = dict(total=len(items), excluded_visibility=0, stock_n=0, stock_correct=0,
                  stock_points=0, compliance_n=0, compliance_correct=0, compliance_points=0,
                  stock_fallbacks=0, compliance_fallbacks=0, errors=[],
                  confusion={truth:{pred:0 for pred in LEVELS} for truth in LEVELS})
    for item in items:
        label, prediction = item['label'], predictions[item['id']]
        stock = prediction.get('observed_stock')
        compliance = prediction.get('observed_compliance')
        if stock is not None and stock not in LEVELS:
            raise ValueError('Invalid predicted stock')
        if compliance is not None and type(compliance) is not bool:
            raise ValueError('Invalid predicted compliance')
        if label['visibility'] != 'clear':
            result['excluded_visibility'] += 1
            continue
        # Fixed operational fallback; never drop a hard case because the model abstained.
        stock_fallback, compliance_fallback = stock is None, compliance is None
        stock = stock if stock is not None else 'half'
        compliance = compliance if compliance is not None else True
        for field, truth, pred in [('stock',label['stock_level'],stock),('compliance',label['planogram_compliant'],compliance)]:
            if truth is None:
                continue
            result[field+'_n'] += 1
            result[field+'_correct'] += truth == pred
            result[field+'_fallbacks'] += stock_fallback if field=='stock' else compliance_fallback
            points = PAYOFF[list(LEVELS).index(pred)][list(LEVELS).index(truth)] if field=='stock' else (1 if pred==truth else -2)
            result[field+'_points'] += points
            if field=='stock':
                result['confusion'][truth][pred] += 1
            if truth != pred:
                result['errors'].append(dict(id=item['id'], field=field, truth=truth, prediction=pred))
    result['points'] = result['stock_points']+result['compliance_points']
    result['maximum'] = result['stock_n']+result['compliance_n']
    for field in ('stock','compliance'):
        n = result[field+'_n']
        result[field+'_accuracy'] = result[field+'_correct']/n if n else None
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','score'])
    parser.add_argument('labels',type=Path)
    parser.add_argument('--review-dir',type=Path,default=Path('data/human-review-v1'))
    parser.add_argument('--prepared',type=Path,default=Path('data/prepared-v1'))
    parser.add_argument('--split',choices=['development','holdout'],default='development')
    parser.add_argument('--predictions',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    review=load_review(args.labels,args.review_dir/'manifest.json')
    items=[x for x in review['items'] if x['split']==args.split]
    if args.output.exists():
        raise ValueError('Output exists; preserve prior experiment')
    if args.mode=='prepare':
        args.output.mkdir(parents=True)
        samples=[]
        for item in items:
            sample={k:item[k] for k in ('camera_id','image_file','area_id','product_name')}
            sample['sample_id']=item['id']
            for kind in ('crop','context'):
                source=args.review_dir/item[kind]
                if kind=='crop' and hashlib.sha256(source.read_bytes()).hexdigest()!=item['crop_sha256']:
                    raise ValueError('Crop hash mismatch')
                sample[kind]=Path(item[kind]).name
                shutil.copyfile(source,args.output/sample[kind])
            sample['mask']=item['id']+'_valid.png'
            shutil.copyfile(args.prepared/'assets'/sample['mask'],args.output/sample['mask'])
            samples.append(sample)
        (args.output/'sample.json').write_text(json.dumps(samples,indent=2)+'\n')
        print(f'Prepared {len(samples)} {args.split} inputs; no labels sent to model')
    else:
        if args.predictions is None:
            parser.error('--predictions required for score')
        predictions=json.loads(args.predictions.read_text())
        results=dict(split=args.split, labels_sha256=hashlib.sha256(args.labels.read_bytes()).hexdigest(),
                     predictions_sha256=hashlib.sha256(args.predictions.read_bytes()).hexdigest(),
                     model=evaluate(items,predictions),baselines={})
        for stock in LEVELS:
            results['baselines'][stock]=evaluate(items,{x['id']:dict(observed_stock=stock,observed_compliance=True) for x in items})
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(results,indent=2)+'\n')
        for name,r in [('model',results['model']),*results['baselines'].items()]:
            print(name, f"stock {r['stock_correct']}/{r['stock_n']}; compliance {r['compliance_correct']}/{r['compliance_n']}; points {r['points']}/{r['maximum']}")


if __name__=='__main__':
    main()
