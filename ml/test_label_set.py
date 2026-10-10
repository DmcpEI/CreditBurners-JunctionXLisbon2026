import unittest
from ml.label_set import select_samples


class LabelSetTests(unittest.TestCase):
    def test_area_disjoint_unexposed_holdout_and_stable_selection(self):
        rows = [dict(camera_id=c, area_id=c+'_'+a, image_file=str(t)+'.jpg')
                for c in ('6215','6383') for a in ('1','2','3') for t in (100,200,300)]
        exposed={'6215_1','6383_1'}
        result=select_samples(rows, exposed)
        dev={r['area_id'] for r in result if r['split']=='development'}
        hold={r['area_id'] for r in result if r['split']=='holdout'}
        self.assertFalse(dev & hold)
        self.assertFalse(hold & exposed)
        self.assertEqual(result,select_samples(list(reversed(rows)),exposed))
        self.assertEqual(len({(r['area_id'],r['image_file']) for r in result}),len(result))
        with self.assertRaises(ValueError):
            select_samples(rows,{r['area_id'] for r in rows})

    def test_expansion_keeps_splits_excludes_used_and_curtains(self):
        from ml.label_set import select_expansion
        rows = [dict(camera_id=c, area_id=f'{c}_{a}', image_file=f'{t}.jpg', product_name=f'P{a} KG')
                for c in ('1', '2') for a in range(1, 6) for t in range(100, 1000, 100)]
        previous = [dict(camera_id=c, area_id=f'{c}_1', image_file='100.jpg', split='development') for c in ('1', '2')] + \
                   [dict(camera_id=c, area_id=f'{c}_2', image_file='100.jpg', split='holdout') for c in ('1', '2')]
        result = select_expansion(rows, previous, {'1_3'}, {('2', '500.jpg')}, dict(development=6, holdout=4, fresh=4))
        keys = [(r['camera_id'], r['image_file'], r['area_id']) for r in result]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertFalse({('1', '100.jpg', '1_1'), ('2', '100.jpg', '2_1')} & set(keys))
        self.assertFalse([r for r in result if (r['camera_id'], r['image_file']) == ('2', '500.jpg')])
        split = {r['area_id']: r['split'] for r in result}
        self.assertEqual(split['1_1'], 'development')
        self.assertEqual(split['1_2'], 'holdout')
        self.assertEqual(split.get('1_3', 'development'), 'development')  # exposed area never in evaluation
        self.assertFalse({a for a, s in split.items() if s == 'evaluation'} & {'1_1', '1_2', '1_3', '2_1', '2_2'})
        self.assertEqual(result, select_expansion(list(reversed(rows)), previous, {'1_3'}, {('2', '500.jpg')},
                                                  dict(development=6, holdout=4, fresh=4)))
