"""Exercise WeChat image preparation through its CLI."""

import io
import json
from pathlib import Path
import random
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageCms, ImageOps
from PIL.PngImagePlugin import PngInfo


SCRIPT = Path(__file__).resolve().parents[1] / "skills/wechat-mp-publisher/scripts/images.py"


class WechatImageTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def prepare(self, source, quality, role="body"):
        run = subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(source), "--out-dir", str(self.root / "out"),
             "--quality", quality, "--role", role, "--stem", "first-photo"],
            capture_output=True, text=True, check=False,
        )
        result = json.loads(run.stdout)
        self.assertEqual(run.returncode, result.get("code", 0))
        return result

    def test_exif_orientation_and_private_metadata(self):
        source = self.root / "camera.jpg"
        photo = Image.new("RGB", (40, 20), "navy")
        photo.paste("white", (0, 0, 12, 8))
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = "Private photographer"
        exif[34853] = {1: "N", 2: (30, 4, 0), 3: "E", 4: (100, 2, 0)}
        profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        photo.save(source, exif=exif, icc_profile=profile)
        original = source.read_bytes()
        result = self.prepare(source, "lossless")
        self.assertTrue(result["ok"], result)
        with Image.open(source) as input_image, Image.open(result["path"]) as ready:
            self.assertEqual(ready.size, (20, 40))
            self.assertEqual(ready.convert("RGB").tobytes(), ImageOps.exif_transpose(input_image).convert("RGB").tobytes())
            self.assertFalse(ready.getexif())
            self.assertEqual(ready.info.get("icc_profile"), profile)
        self.assertTrue(result["pixel_equal"])
        self.assertIsNone(result["remote_pixel_equal"])
        self.assertEqual(source.read_bytes(), original)

    def test_clean_jpeg_that_cannot_fit_as_png(self):
        source = self.root / "texture.jpg"
        pixels = random.Random(1526).randbytes(800 * 800 * 3)
        photo = Image.frombytes("RGB", (800, 800), pixels)
        for progressive in (False, True):
            with self.subTest(progressive=progressive):
                photo.save(source, quality=84, progressive=progressive)
                original = source.read_bytes()
                with Image.open(source) as decoded:
                    png = io.BytesIO()
                    decoded.save(png, "PNG", optimize=True)
                self.assertLess(len(original), 1024 * 1024)
                self.assertGreater(len(png.getvalue()), 1024 * 1024)
                result = self.prepare(source, "lossless")
                self.assertTrue(result["ok"], result)
                self.assertTrue(result["pixel_equal"])
                self.assertEqual(Path(result["path"]).read_bytes(), original)
        # Pillow's initial list of JPEG segments omits metadata after the first scan.
        for unsafe in (original[:-2] + b"\xff\xfe\x00\x08Secret" + original[-2:], original + b"Private trailer"):
            source.write_bytes(unsafe)
            self.assertEqual(self.prepare(source, "lossless")["code"], 7)

    def test_rgba_including_transparent_rgb_and_png_text(self):
        source = self.root / "card.png"
        image = Image.new("RGBA", (8, 8), (47, 2, 18, 0))
        image.putpixel((3, 2), (20, 70, 40, 130))
        info = PngInfo()
        info.add_text("Description", "Private location")
        image.save(source, pnginfo=info)
        result = self.prepare(source, "lossless")
        self.assertTrue(result["ok"], result)
        with Image.open(result["path"]) as ready:
            self.assertEqual(ready.tobytes(), image.tobytes())
            self.assertNotIn("Description", ready.info)

    def test_different_limits_and_balanced_fallback(self):
        source = self.root / "noise.png"
        pixels = random.Random(1526).randbytes(620 * 620 * 3)
        Image.frombytes("RGB", (620, 620), pixels).save(source)
        strict = self.prepare(source, "lossless")
        self.assertEqual(strict["code"], 7)
        self.assertFalse((self.root / "out").exists())
        cover = self.prepare(source, "lossless", "cover")
        self.assertTrue(cover["pixel_equal"])
        self.assertGreaterEqual(cover["output_bytes"], 1024 * 1024)
        body = self.prepare(source, "balanced")
        self.assertTrue(body["ok"], body)
        self.assertFalse(body["pixel_equal"])
        self.assertLess(body["output_bytes"], 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
