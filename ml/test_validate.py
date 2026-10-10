import tempfile
import unittest
import zipfile
from pathlib import Path
from ml.validate import read_images


class ReadImagesTests(unittest.TestCase):
    def test_folder_and_zip_skip_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "val"
            for name in ("6215/1.jpg", "6383/2.JPG", "__MACOSX/6215/._1.jpg", "6215/.DS_Store", "notes.txt"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(b"x")
            self.assertEqual([str(p) for p, _ in read_images(root)], ["6215/1.jpg", "6383/2.JPG"])
            archive = Path(d) / "val.zip"
            with zipfile.ZipFile(archive, "w") as z:
                for p in sorted(root.rglob("*")):
                    if p.is_file():
                        z.write(p, p.relative_to(root).as_posix())
            self.assertEqual([str(p) for p, _ in read_images(archive)], ["6215/1.jpg", "6383/2.JPG"])
