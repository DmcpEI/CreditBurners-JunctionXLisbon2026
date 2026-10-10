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
