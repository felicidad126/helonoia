"""Gambar uji sintetis dengan warna yang diketahui pasti.

Digambar 4× lebih besar lalu diperkecil, supaya tepinya ber-anti-aliasing seperti logo asli.
"""
from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFont

SS = 4  # supersampling

BADGE_COLORS = ["#FFFFFF", "#E63946", "#1D3557", "#F1C40F", "#2A9D8F"]
LINEART_COLORS = ["#FFFFFF", "#111111"]


def _font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def _finish(im: Image.Image, size: int) -> Image.Image:
    if im.mode == "RGBA":  # perkecil dengan alpha premultiplied supaya tepi tidak berpinggiran
        return im.convert("RGBa").resize((size, size), Image.LANCZOS).convert("RGBA")
    return im.resize((size, size), Image.LANCZOS)


def badge(size: int = 600, transparent: bool = False) -> Image.Image:
    """Logo flat: latar putih (atau transparan), lingkaran merah, persegi membulat biru,
    segi lima kuning, teks putih, garis tepi hijau 3 px."""
    s = size * SS
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0) if transparent else BADGE_COLORS[0])
    d = ImageDraw.Draw(im)
    u = s / 100
    d.ellipse([10 * u, 10 * u, 90 * u, 90 * u], fill=BADGE_COLORS[1],
              outline=BADGE_COLORS[4], width=round(3 * size / 600 * SS * 2))
    d.rounded_rectangle([22 * u, 55 * u, 78 * u, 75 * u], radius=5 * u, fill=BADGE_COLORS[2])
    d.regular_polygon((50 * u, 33 * u, 15 * u), n_sides=5, rotation=0, fill=BADGE_COLORS[3])
    d.text((50 * u, 65 * u), "HELO", fill=BADGE_COLORS[0], font=_font(round(13 * u)),
           anchor="mm")
    im = _finish(im, size)
    return im if transparent else im.convert("RGB")


ACCENT_COLORS = ["#120B1E", "#B26BFF", "#F2EEFE", "#F151A7"]


def accent(size: int = 600) -> Image.Image:
    """Wajah ungu di latar gelap dengan mata putih dan lidah merah muda yang sangat kecil
    (sekitar 0,05% area): warna aksen yang harus tetap ada."""
    s = size * SS
    im = Image.new("RGB", (s, s), ACCENT_COLORS[0])
    d = ImageDraw.Draw(im)
    u = s / 100
    d.ellipse([20 * u, 20 * u, 80 * u, 80 * u], fill=ACCENT_COLORS[1])
    for x in (38, 62):
        d.ellipse([(x - 7) * u, 35 * u, (x + 7) * u, 49 * u], fill=ACCENT_COLORS[2])
    d.ellipse([48.5 * u, 63.5 * u, 51.5 * u, 65.5 * u], fill=ACCENT_COLORS[3])
    return _finish(im, size)


SHADOW_COLORS = ["#0D081C", "#B362FA", "#2D1459"]  # latar, karakter, inti bayangan


def shadow(size: int = 600) -> Image.Image:
    """Karakter flat (lingkaran ungu) di atas bayangan elips yang memudar lembut ke latar."""
    import numpy as np
    s = size
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float64) + 0.5
    r = np.sqrt(((xx - 0.5 * s) / (0.32 * s)) ** 2 + ((yy - 0.78 * s) / (0.06 * s)) ** 2)
    fade = np.clip(1 - r, 0, 1) ** 1.5
    bg = np.array([int(SHADOW_COLORS[0][i:i + 2], 16) for i in (1, 3, 5)], np.float64)
    core = np.array([int(SHADOW_COLORS[2][i:i + 2], 16) for i in (1, 3, 5)], np.float64)
    img = bg + (core - bg) * fade[..., None]
    im = Image.fromarray(img.round().astype(np.uint8), "RGB").resize((s * SS, s * SS))
    d = ImageDraw.Draw(im)
    u = s * SS / 100
    d.ellipse([35 * u, 25 * u, 65 * u, 72 * u], fill=SHADOW_COLORS[1])
    return _finish(im, size)


def lineart(size: int = 600) -> Image.Image:
    """Line-art: garis hitam tipis (sekitar 2 px pada ukuran akhir) di latar putih."""
    s = size * SS
    im = Image.new("RGB", (s, s), LINEART_COLORS[0])
    d = ImageDraw.Draw(im)
    u = s / 100
    w = round(2 * size / 600 * SS)
    d.ellipse([20 * u, 20 * u, 80 * u, 80 * u], outline=LINEART_COLORS[1], width=w)
    d.line([20 * u, 50 * u, 80 * u, 50 * u], fill=LINEART_COLORS[1], width=w)
    d.arc([35 * u, 35 * u, 65 * u, 65 * u], 200, 340, fill=LINEART_COLORS[1], width=w)
    for x in (40, 60):
        d.ellipse([(x - 3) * u, 37 * u, (x + 3) * u, 43 * u], outline=LINEART_COLORS[1], width=w)
    return _finish(im, size)


def as_jpeg(im: Image.Image, size: int, quality: int) -> Image.Image:
    """Versi "kotor": diperkecil dan dikompres JPEG, seperti kiriman WhatsApp."""
    buf = io.BytesIO()
    im.resize((size, size), Image.LANCZOS).save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")
