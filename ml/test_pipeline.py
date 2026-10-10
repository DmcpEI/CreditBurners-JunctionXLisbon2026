import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image

from ml.prepare import crop_area, load_planogram, prepare
from ml.scoring import LEVELS, PAYOFF, choose_stock, score, validate_submission


def prediction(level, compliant=True):
    return {"planogram_compliant": compliant, "stock_level": level, "stock_value": LEVELS[level]}


class PipelineTests(unittest.TestCase):
    def test_payoffs_and_missing(self):
        for i, guessed in enumerate(LEVELS):
            for j, actual in enumerate(LEVELS):
                truth = {"cam": {"1.jpg": {"a": prediction(actual)}}}
                output = {"cam": {"1.jpg": {"a": prediction(guessed)}}}
                self.assertEqual(score(truth, output)["score"], 1+PAYOFF[i][j])
                output["cam"]["1.jpg"]["a"]["planogram_compliant"] = False
                self.assertEqual(score(truth, output)["score"], -2+PAYOFF[i][j])
        self.assertEqual(score(truth, {})["score"], -5)
        self.assertEqual(score(truth, {})["missing"], 1)

    def test_decision_and_validation(self):
        self.assertEqual(choose_stock([0.30, 0.34, 0.36]), "empty")
        self.assertEqual(choose_stock([0, 0, 1]), "full")
        with self.assertRaises(ValueError):
            choose_stock([0.9, 0.9, 0.9])
        output = {"cam": {"1.jpg": {"a": prediction("half")}}}
        self.assertEqual(validate_submission(output, [["cam", "1.jpg", "a"]]), 1)
        with self.assertRaises(ValueError):
            validate_submission(output, [])
        output["cam"]["1.jpg"]["a"]["planogram_compliant"] = "true"
        with self.assertRaises(ValueError):
            validate_submission(output, [["cam", "1.jpg", "a"]])
        output["cam"]["1.jpg"]["a"] = prediction("full")
        output["cam"]["1.jpg"]["a"]["stock_value"] = True
        with self.assertRaises(ValueError):
            validate_submission(output, [["cam", "1.jpg", "a"]])

    def test_padding_and_orientation(self):
        image = Image.new("RGB", (8, 8), "red")
        points = dict(top_left=[-4, 0], top_right=[8, 0], bottom_right=[8, 8], bottom_left=[-4, 8])
        crop, valid = crop_area(image, points)
        self.assertEqual(crop.size, (12, 8))
        self.assertEqual(valid.getpixel((0, 4)), 0)
        self.assertEqual(valid.getpixel((6, 4)), 255)
        self.assertEqual(crop.getpixel((6, 4)), (255, 0, 0))
        image.paste("blue", (0, 4, 8, 8))
        points.update(top_left=[0, 0], bottom_left=[0, 8])
        crop, _ = crop_area(image, points)
        self.assertEqual(crop.getpixel((3, 1)), (255, 0, 0))
        self.assertEqual(crop.getpixel((3, 6)), (0, 0, 255))

    def test_full_pipeline_and_safety(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            area = dict(area_id="cam_1", product_id="demo", product_name="Banana",
                        image_coordinates=dict(top_left=[-4, 0], top_right=[8, 0],
                                               bottom_right=[8, 8], bottom_left=[-4, 8]))
            planogram = {"Frutas e Legumes": {"cameras": {"cam": {"products": [area]}}}}
            (root/"planogram.json").write_text(json.dumps(planogram))
            buffer = io.BytesIO()
            Image.new("RGB", (8, 8), "green").save(buffer, format="JPEG")
            with zipfile.ZipFile(root/"images.zip", "w") as archive:
                archive.writestr("images/cam/1700000000.jpg", buffer.getvalue())
                archive.writestr("__MACOSX/images/cam/._1700000000.jpg", b"not an image")
                archive.writestr("../../unrelated.txt", b"must not be extracted")
            out = root/"prepared"
            report = prepare(root, out)
            self.assertEqual(report["area_observations"], 1)
            self.assertEqual(report["clipped_areas"], ["cam_1"])
            expected = json.loads((out/"expected.json").read_text())
            for level in LEVELS:
                self.assertEqual(validate_submission(json.loads((out/f"baseline-{level}.json").read_text()), expected), 1)
            snapshot = json.loads((out/"snapshots.json").read_text())[0]
            self.assertTrue(snapshot["areas"][0]["fallback_used"])
            self.assertEqual(snapshot["areas"][0]["visibility"], "unknown")
            self.assertTrue((out/snapshot["areas"][0]["crop_url"].lstrip("/")).is_file())
            with self.assertRaises(ValueError):
                prepare(root, out)
            area["image_coordinates"]["top_right"] = [-4, 0]
            (root/"planogram.json").write_text(json.dumps(planogram))
            with self.assertRaises(ValueError):
                load_planogram(root/"planogram.json")


if __name__ == "__main__":
    unittest.main()
