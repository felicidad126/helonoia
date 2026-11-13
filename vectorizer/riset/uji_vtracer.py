"""Uji coba VTracer untuk riset vektorisasi (lihat RISET-VEKTORISASI.md).

Jalankan dari root repo:
    pip install vtracer pillow numpy opencv-python-headless cairosvg
    python3 vectorizer/riset/uji_vtracer.py

Hasil (SVG, render PNG, gambar perbandingan) ditulis ke vectorizer/riset/hasil/.
"""
import io
import os
import re

import cairosvg
import cv2
import numpy as np
import vtracer
from PIL import Image, ImageDraw

SRC = "helonoia/helonoia_logo.png"
OUT = "vectorizer/riset/hasil"


def render(svg_path, size):
    png = cairosvg.svg2png(url=svg_path, output_width=size[0], output_height=size[1])
    return Image.open(io.BytesIO(png)).convert("RGB")


def psnr(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    return 10 * np.log10(255**2 / ((a - b) ** 2).mean())


def report(name, svg_path, ref):
    s = open(svg_path).read()
    r = render(svg_path, ref.size)
    r.save(svg_path.replace(".svg", "_render.png"))
    colors = len(set(re.findall(r'fill="(#[0-9A-Fa-f]{6})"', s)))
    print(f"{name:22s} PSNR {psnr(r, ref):5.1f} dB  {os.path.getsize(svg_path) // 1024:4d} KB"
          f"  path {s.count('<path'):4d}  warna {colors}")


def preprocess(img, k):
    """Upscale 3x, denoise yang menjaga tepi, lalu kuantisasi ke k warna."""
    up = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    den = cv2.medianBlur(cv2.bilateralFilter(up, 9, 40, 9), 5)
    z = den.reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
    _, lab, cent = cv2.kmeans(z, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    q = cent.astype(np.uint8)[lab.flatten()].reshape(den.shape)
    return cv2.medianBlur(q, 3)


def main():
    os.makedirs(OUT, exist_ok=True)
    clean = Image.open(SRC).convert("RGB")

    print("== Input bersih ==")
    for name, kw in {"bersih_spline": {}, "bersih_polygon": {"mode": "polygon"}}.items():
        p = f"{OUT}/{name}.svg"
        vtracer.convert_image_to_svg_py(SRC, p, colormode="color", **kw)
        report(name, p, clean)

    print("== Input kotor (300 px, JPEG q60) ==")
    dirty_path = f"{OUT}/kotor.jpg"
    clean.resize((300, 300), Image.LANCZOS).save(dirty_path, quality=60)
    dirty = Image.open(dirty_path).convert("RGB")

    cases = {
        "kotor_default": {},
        "kotor_diperketat": {"filter_speckle": 10, "color_precision": 4, "layer_difference": 40},
    }
    for name, kw in cases.items():
        p = f"{OUT}/{name}.svg"
        vtracer.convert_image_to_svg_py(dirty_path, p, colormode="color", **kw)
        report(name, p, dirty)

    for k in (6, 8, 12):
        pre = f"{OUT}/praproses_k{k}.png"
        Image.fromarray(preprocess(np.asarray(dirty), k)).save(pre)
        p = f"{OUT}/praproses_k{k}.svg"
        vtracer.convert_image_to_svg_py(pre, p, colormode="color",
                                        filter_speckle=12, color_precision=8, layer_difference=1)
        report(f"praproses_k{k}", p, dirty)

    items = [
        (dirty_path, "Input JPEG 300px q60"),
        (f"{OUT}/kotor_default_render.png", "VTracer default"),
        (f"{OUT}/kotor_diperketat_render.png", "VTracer diperketat"),
        (f"{OUT}/praproses_k6_render.png", "Praproses + K=6"),
    ]
    w = 300
    sheet = Image.new("RGB", (w * 4, w + 30), "white")
    d = ImageDraw.Draw(sheet)
    for i, (f, t) in enumerate(items):
        sheet.paste(Image.open(f).convert("RGB").resize((w, w)), (i * w, 30))
        d.text((i * w + 6, 8), t, fill="black")
    sheet.save(f"{OUT}/perbandingan.png")
    print(f"Perbandingan: {OUT}/perbandingan.png")


if __name__ == "__main__":
    main()
