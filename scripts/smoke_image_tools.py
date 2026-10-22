"""Smoke the image tools with synthetic local inputs and the selected interpreter."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = {**os.environ, "PHOTO_SELECTOR_PYTHON": sys.executable,
           "PHOTO_SELECTOR_BACKEND": "python-pillow", "PYTHONDONTWRITEBYTECODE": "1"}

    def run(*args):
        result = subprocess.run([str(arg) for arg in args], env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)

    with tempfile.TemporaryDirectory(prefix="image-tools-smoke-") as directory:
        temp = Path(directory)
        photos = temp / "photos"
        photos.mkdir()
        for index in range(5):
            Image.new("RGB", (80, 120), (30 * index, 50, 100)).save(photos / f"sample-{index}.jpg")
        original = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in photos.iterdir()}
        scripts = ROOT / "skills/photo-selector/scripts"
        if os.name == "nt":
            shell = shutil.which("pwsh")
            if not shell:
                raise RuntimeError("PowerShell 7 is required to smoke the Windows entrypoint")
            wrapper = [shell, "-NoProfile", "-File", scripts / "make_contact_sheets.ps1"]
        else:
            shell = shutil.which("bash")
            if not shell:
                raise RuntimeError("bash is required to smoke the shell entrypoint")
            wrapper = [shell, scripts / "make_contact_sheets.sh"]
        sheets = temp / "sheets"
        run(*wrapper, photos, sheets, 2, 2, 120, 100)
        pages = sorted(sheets.glob("sheet_*.jpg"))
        assert len(pages) == 2
        for page in pages:
            with Image.open(page) as image:
                assert image.size == (240, 200)
        candidates = temp / "candidates.txt"
        candidates.write_text("sample-4.jpg\nsample-1.jpg\n", encoding="utf-8")
        selected = temp / "selected"
        run(*wrapper, photos, selected, 2, 2, 120, 100, candidates)
        assert len(list(selected.glob("sheet_*.jpg"))) == 1
        assert "sample-4.jpg - sample-1.jpg" in (selected / "index.txt").read_text(encoding="utf-8-sig")

        tools = ROOT / "skills/id-photo-maker/scripts"
        processed = temp / "processed"
        run(sys.executable, "-B", tools / "process_local_photo.py", photos / "sample-0.jpg",
            "--size", "1-inch", "--background", "white", "--skip-background-removal", "--output-dir", processed)
        with Image.open(processed / "id-photo.png") as image:
            assert image.size == (295, 413)
            assert image.getpixel((0, 0)) == (255, 255, 255, 255)
        run(sys.executable, "-B", tools / "render_print_sheet.py", "--photo", processed / "id-photo.png",
            "--size", "1-inch", "--pages", "a4,6inch", "--output-dir", temp / "print")
        for name in ("print-a4.html", "print-6inch.html", "index.html", "print-sheet.json"):
            assert (temp / "print" / name).is_file()
        assert original == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in photos.iterdir()}
    print(json.dumps({"result": "passed", "pillow": pillow_version,
                      "checks": ["pagination", "candidate order", "sheet dimensions", "ID size/background",
                                 "print outputs", "source preservation"],
                      "not_tested": ["AI background removal", "Liblib API", "macOS JXA"]}))


if __name__ == "__main__":
    main()
