import json
import tempfile
import unittest
from pathlib import Path
from ml.evaluate_review import evaluate, load_review


class ReviewEvaluationTests(unittest.TestCase):
    def test_exclusions_fallbacks_and_asymmetric_penalties(self):
        def row(key, visibility, stock, compliance):
            return dict(id=key,label=dict(visibility=visibility,stock_level=stock,planogram_compliant=compliance))
        items=[row('a','clear','empty',True),row('b','clear','half',None),row('c','occluded',None,None)]
        predictions={'a':dict(observed_stock='half',observed_compliance=None),
                     'b':dict(observed_stock='empty',observed_compliance=False),'c':{}}
        r=evaluate(items,predictions)
        self.assertEqual(r['stock_points'],-5)
        self.assertEqual(r['compliance_points'],1)
        self.assertEqual(r['maximum'],3)
        self.assertEqual(r['excluded_visibility'],1)
        self.assertEqual(r['compliance_fallbacks'],1)
        self.assertEqual(r['stock_n'],2)
        with self.assertRaises(ValueError):
            evaluate(items,{'a':predictions['a']})

    def test_frozen_labels_and_metadata_are_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            item=dict(id='x',split='development',area_id='a')
            manifest=dict(set_id='fixed',items=[item])
            review=dict(status='frozen',reviewer='Member1',frozen_at='time',set_id='fixed',
                        protocol=dict(revision='sensei-box-capacity-v2'),items=[dict(item,label=dict(
                        protocol_revision='sensei-box-capacity-v2',visibility='clear',stock_level='half',planogram_compliant=True))])
            (root/'manifest').write_text(json.dumps(manifest))
            (root/'labels').write_text(json.dumps(review))
            self.assertEqual(load_review(root/'labels',root/'manifest')['reviewer'],'Member1')
            review['items'][0]['area_id']='changed'
            (root/'labels').write_text(json.dumps(review))
            with self.assertRaises(ValueError):
                load_review(root/'labels',root/'manifest')
