#!/usr/bin/env python3
"""
Convert the site's PNG/JPG images to WebP and point the HTML at the new files.

Run from the website folder (the one that contains index.html and assets/):
    pip install pillow
    python3 tools/to-webp.py            # convert + update references, keep originals
    python3 tools/to-webp.py --delete   # same, then delete the original PNG/JPG files

Left alone on purpose: assets/og-image.jpg (social networks need JPG/PNG),
assets/logo.png (used as favicon and in structured data), and any line that is
a favicon, Open Graph, Twitter or JSON-LD tag.
"""
import re, sys, pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEEP = {"og-image.jpg", "logo.png"}
EXT = {".png", ".jpg", ".jpeg"}
delete = "--delete" in sys.argv

converted = []
for f in sorted((ROOT / "assets").rglob("*")):
    if f.suffix.lower() in EXT and f.name not in KEEP:
        out = f.with_suffix(".webp")
        im = Image.open(f)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
        im.save(out, "WEBP", quality=82, method=6)
        converted.append(f)
        print(f"{f.relative_to(ROOT)}  {f.stat().st_size//1024} KB -> {out.stat().st_size//1024} KB")

SKIP_LINE = re.compile(r'rel="icon"|property="og:|name="twitter:|application/ld\+json')
PATH = re.compile(r'(assets/[^"\'`\s)<>]*?)\.(?:png|jpe?g)\b', re.I)
for page in list(ROOT.glob("*.html")) + list(ROOT.glob("*/index.html")):
    lines = page.read_text(encoding="utf-8").split("\n")
    changed = False
    for i, line in enumerate(lines):
        if SKIP_LINE.search(line):
            continue
        new = PATH.sub(lambda m: m.group(0) if pathlib.Path(m.group(0)).name in KEEP else m.group(1) + ".webp", line)
        new = re.sub(r'(photo\$\{k\})\.jpg', r'\1.webp', new)  # gallery onerror selector
        if new != line:
            lines[i] = new
            changed = True
    if changed:
        page.write_text("\n".join(lines), encoding="utf-8")
        print("updated", page.relative_to(ROOT))

if delete:
    for f in converted:
        f.unlink()
    print("deleted", len(converted), "originals")
print("done:", len(converted), "images converted")
