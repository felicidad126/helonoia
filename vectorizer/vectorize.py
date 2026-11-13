#!/usr/bin/env python3
"""Helonoia Vectorizer: ubah logo dan ilustrasi flat (PNG/JPG/WebP) menjadi SVG.

Alur:
  1. Muat gambar dan ubah ke ukuran kerja (gambar kecil diperbesar, gambar besar diperkecil).
  2. Bersihkan noise (artefak JPEG) tanpa merusak tepi.
  3. Tentukan palet: otomatis dari area warna yang rata, jumlah warna tetap, atau palet terkunci.
  4. Beri setiap piksel satu warna palet, lalu haluskan tepinya.
  5. Lacak bentuk dengan VTracer.
  6. Rapikan SVG: warna dikunci ke palet, ukuran dikembalikan ke ukuran asli.

Contoh:
  python3 vectorizer/vectorize.py logo.jpg
  python3 vectorizer/vectorize.py logo.jpg -o hasil/ --palette helonoia --remove-bg
  python3 vectorizer/vectorize.py folder_gambar/ -o hasil/ --format svg,pdf

Lihat vectorizer/README.md untuk semua opsi.
"""
from __future__ import annotations

import argparse
import io
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import vtracer
from PIL import Image, ImageOps

try:  # Hanya untuk PDF/EPS/PNG dan laporan kemiripan.
    import cairosvg
except ImportError:  # pragma: no cover
    cairosvg = None

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

PALETTES = {
    # Warna logo Helonoia: Malam, Ungu Noia, Ungu Tua, Lilac, Lime, Putih Halo.
    "helonoia": ["#120B1E", "#B26BFF", "#7C3FD6", "#CDA6FF", "#C6FF3D", "#F4EFFF"],
}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
OUTPUT_FORMATS = ("svg", "pdf", "eps", "png")



@dataclass(frozen=True)
class Precision:
    work_size: int  # sisi terpanjang gambar saat diproses (piksel)
    max_upscale: float  # pembesaran maksimal untuk gambar kecil
    splice: int  # ambang sudut VTracer untuk menyambung kurva; kecil = kurva lebih rapat


# Resolusi kerja paling menentukan ketelitian bentuk: tepi diletakkan pada grid kerja,
# jadi grid yang lebih halus = batas warna yang lebih tepat. Diukur pada ilustrasi
# 1536 px: 2000 px → PSNR 27,1 dB, 4000 px → 29,9 dB, dengan waktu kira-kira 3×.
# splice 20 (bukan 45, bawaan VTracer) mencegah kurva "kebablasan" menutupi garis tipis.
PRECISIONS = {
    "tinggi": Precision(work_size=4000, max_upscale=8.0, splice=20),
    "cepat": Precision(work_size=2000, max_upscale=4.0, splice=20),
}
FLAT_GRADIENT = 6.0  # ΔE antar piksel tetangga; di bawah ini area dianggap rata
SAMPLE_SIZE = 60_000  # jumlah piksel contoh untuk menentukan palet
AUTO_MAX_COLORS = 24  # batas warna mode otomatis
REDUCE_SAMPLE = 300_000  # piksel contoh untuk menghitung "kerusakan" saat menyederhanakan
REDUCE_ACCENT_AREA = 0.01  # warna yang sangat berbeda dihitung seolah luasnya minimal 1%
GRADIENT_MIN_AREA = 150  # luas minimum area yang dicoba diisi gradasi (piksel asli)
GRADIENT_MAX_SHARE = 0.05  # area yang lebih luas dari ini (porsi gambar) tidak dicoba
GRADIENT_GAIN = 0.7  # gradasi dipakai bila selisihnya ≤ 70% selisih bidang rata ...
GRADIENT_MIN_DROP = 1.0  # ... dan turun minimal ΔE 1
GRADIENT_MAX_STEP = 12.0  # gradasi berubah bertahap: lompatan antar stop maksimal ΔE ini
GRADIENT_MIN_RANGE = 10.0  # dan benar-benar berubah: rentang warna stop minimal ΔE ini
GRADIENT_INLIER_DE = 12.0  # piksel yang lebih jauh dari gradasi = bentuk lain di atasnya
GRADIENT_MIN_INLIERS = 0.85  # porsi piksel area yang harus cocok dengan gradasi
GRADIENT_FEATHER = 8  # bayangan/glow: area diperluas sejauh ini ke latar (piksel asli)
GRADIENT_FEATHER_STEP = 20.0  # bayangan memudar lebih cepat: lompatan antar stop maksimal ini
GRADIENT_STOPS = 16
GRADIENT_SAMPLE = 40_000
MISSING_DE = 28.0  # piksel sejauh ini dari palet (dan bukan campuran) = warna yang terlewat
ACCENT_DE = 30.0  # warna aksen: sejauh ini dari semua warna palet ...
ACCENT_SHARE = 0.0002  # ... cukup 0,02% area untuk dipertahankan (lidah, pipi, tanda kecil)
MISSING_SAMPLE = 300_000  # sampel lebih besar supaya area 0,02% tetap terhitung andal
BLEND_RGB = 18.0  # piksel sedekat ini (RGB) ke campuran dua warna palet = tepi anti-aliasing
HALO_DE = 20.0  # warna "pita tipis" yang semirip ini dengan warna lain dianggap artefak tepi
CORE_RATIO = 0.2  # porsi area yang harus tersisa setelah erosi agar warna dianggap "tebal"


@dataclass(frozen=True)
class Detail:
    denoise: float  # kekuatan denoise non-local means (0 = mati)
    edge_sigma: float  # penghalusan tepi, dalam piksel gambar asli
    speckle: float  # sisi bercak terkecil yang dipertahankan, dalam piksel gambar asli
    merge_de: float  # dua warna yang lebih dekat dari ini (ΔE) dianggap satu warna
    min_share: float  # porsi minimum area rata agar sebuah warna masuk palet
    thickness: float  # warna yang hanya muncul sebagai pita setipis ini (piksel asli) = artefak
    corner: int  # ambang sudut VTracer (derajat): makin kecil, makin banyak sudut tajam


DETAILS = {
    "low": Detail(denoise=8, edge_sigma=1.0, speckle=4, merge_de=12, min_share=0.004,
                  thickness=3.5, corner=75),
    "medium": Detail(denoise=5, edge_sigma=0.7, speckle=2, merge_de=6.5, min_share=0.001,
                     thickness=2.5, corner=60),
    "high": Detail(denoise=3, edge_sigma=0.45, speckle=1, merge_de=4, min_share=0.0003,
                   thickness=1.25, corner=45),
}


@dataclass
class Options:
    colors: int | None = None  # paling banyak sekian warna (None = sebanyak yang ditemukan)
    palette: list[str] | None = None  # palet terkunci (hex)
    detail: str = "medium"
    stacking: str = "stacked"  # "stacked" atau "cutout"
    remove_bg: str | None = None  # None, "tepi" (tersambung ke pinggir), atau "semua"
    precision: str = "tinggi"  # "tinggi" atau "cepat"
    gradients: bool = False  # eksperimental: isi area bergradasi dengan gradasi SVG


@dataclass
class Result:
    svg: str
    palette: list[str]  # hex, urut dari area terbesar
    shares: list[float]  # porsi area tiap warna (0..1) pada gambar akhir
    paths: int
    size: tuple[int, int]  # (lebar, tinggi) asli
    work_size: tuple[int, int]
    removed_bg: str | None
    found_colors: int  # jumlah warna sebelum disederhanakan
    gradients: int  # jumlah area yang diisi gradasi
    debug_image: Image.Image  # gambar berlabel yang dilacak VTracer


# ---------------------------------------------------------------------------
# Warna


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6 or any(c not in "0123456789abcdefABCDEF" for c in v):
        raise ValueError(f"warna tidak valid: {value!r} (pakai format #RRGGBB)")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def rgb_to_hex(rgb) -> str:
    r, g, b = (int(round(float(c))) for c in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def to_lab(rgb: np.ndarray) -> np.ndarray:
    """RGB uint8 (…×3) → CIE Lab float32 (L 0–100). Jarak Euclidean ≈ ΔE76."""
    shape = rgb.shape
    flat = rgb.reshape(-1, 1, 3).astype(np.float32) / 255.0
    return cv2.cvtColor(flat, cv2.COLOR_RGB2Lab).reshape(shape)


def parse_palette(value: str) -> list[str]:
    if value.lower() in PALETTES:
        return list(PALETTES[value.lower()])
    colors = [rgb_to_hex(hex_to_rgb(c)) for c in value.split(",") if c.strip()]
    if not colors:
        raise ValueError("palet kosong")
    return colors


# ---------------------------------------------------------------------------
# Tahap 1–2: muat, ubah ukuran, bersihkan


def load_image(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Kembalikan (rgb uint8 H×W×3, alpha uint8 H×W)."""
    with Image.open(path) as im:
        im.seek(0)  # GIF/TIFF berlapis: pakai frame pertama
        im = ImageOps.exif_transpose(im)
        if im.mode in ("I", "F") or im.mode.startswith("I;16"):
            # Grayscale 16-bit/32-bit: Pillow tidak menskalakannya ke 8-bit saat convert().
            arr = np.asarray(im, np.float64)
            top = 65535.0 if arr.max() > 255 else 255.0
            im = Image.fromarray(np.clip(arr / top * 255 + 0.5, 0, 255).astype(np.uint8), "L")
        rgba = np.asarray(im.convert("RGBA"))
    return np.ascontiguousarray(rgba[..., :3]), np.ascontiguousarray(rgba[..., 3])


def prepare(rgb: np.ndarray, alpha: np.ndarray, detail: Detail, prec: Precision):
    """Denoise pada resolusi terkecil yang wajar, lalu ubah ke ukuran kerja.

    Mengembalikan (rgb kerja, mask tidak transparan, skala, dasar). `dasar` adalah gambar
    hasil denoise sebelum diperbesar, dipakai palette_view().
    """
    h, w = alpha.shape
    scale = min(prec.work_size / max(h, w), prec.max_upscale)
    if scale < 1:  # gambar besar: perkecil dulu supaya denoise cepat
        size = (max(1, round(w * scale)), max(1, round(h * scale)))
        rgb = cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
        alpha = cv2.resize(alpha, size, interpolation=cv2.INTER_AREA)
    if detail.denoise > 0:
        rgb = cv2.fastNlMeansDenoisingColored(rgb, None, detail.denoise, detail.denoise, 7, 21)
    base = (rgb, alpha, min(scale, 1.0))
    if scale > 1:
        rgb, alpha = resize_to(rgb, alpha, (round(w * scale), round(h * scale)), up=True)
    return rgb, alpha >= 128, scale, base


def resize_to(rgb: np.ndarray, alpha: np.ndarray, size: tuple[int, int], up: bool):
    if up:
        return (cv2.resize(rgb, size, interpolation=cv2.INTER_CUBIC),
                cv2.resize(alpha, size, interpolation=cv2.INTER_LINEAR))
    return (cv2.resize(rgb, size, interpolation=cv2.INTER_AREA),
            cv2.resize(alpha, size, interpolation=cv2.INTER_AREA))


# ---------------------------------------------------------------------------
# Tahap 3: palet


def palette_view(base, size: tuple[int, int]):
    """Gambar pada resolusi standar (mode --cepat), khusus untuk menaksir palet.

    Ambang penaksiran palet (area rata, artefak JPEG) disetel pada resolusi ini. Pada
    pembesaran yang lebih tinggi, noise JPEG ikut membesar menjadi bercak halus yang
    terlihat seperti warna tersendiri. Dengan begini palet sama di kedua mode presisi;
    resolusi tinggi hanya mempertajam letak tepi.
    """
    rgb, alpha, base_scale = base
    std = PRECISIONS["cepat"]
    est = min(std.work_size / max(size), std.max_upscale)
    if abs(est - base_scale) > 1e-9:
        dims = (max(1, round(size[0] * est)), max(1, round(size[1] * est)))
        rgb, alpha = resize_to(rgb, alpha, dims, up=est > base_scale)
    return rgb, to_lab(rgb), alpha >= 128


def flat_pixels(lab: np.ndarray, opaque: np.ndarray) -> np.ndarray:
    """Mask piksel di bagian dalam area warna (bukan tepi anti-aliasing)."""
    kernel = np.ones((3, 3), np.uint8)
    grad = np.zeros(opaque.shape, np.float32)
    for c in range(3):
        ch = lab[..., c]
        grad += (cv2.dilate(ch, kernel) - cv2.erode(ch, kernel)) ** 2
    flat = (np.sqrt(grad) < FLAT_GRADIENT) & opaque
    if flat.sum() < 0.01 * max(1, opaque.sum()):  # hampir tak ada area rata (mis. foto)
        flat = opaque
    return flat


def kmeans(samples: np.ndarray, k: int) -> np.ndarray:
    k = min(k, len(samples))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.2)
    cv2.setRNGSeed(0)
    _, _, centers = cv2.kmeans(samples, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    return centers


def nearest(lab: np.ndarray, centers: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Indeks warna terdekat dan jarak kuadratnya, tanpa membuat matriks N×K besar."""
    best = np.full(lab.shape[:-1], np.inf, np.float32)
    idx = np.zeros(lab.shape[:-1], np.int32)
    for i, c in enumerate(centers):
        d = ((lab - c) ** 2).sum(-1)
        better = d < best
        best[better] = d[better]
        idx[better] = i
    return idx, best


def estimate_palette(rgb: np.ndarray, lab: np.ndarray, opaque: np.ndarray,
                     detail: Detail) -> tuple[list[str], list[bool]]:
    mask = flat_pixels(lab, opaque)
    rgb_s, lab_s = rgb[mask], lab[mask]
    if len(lab_s) == 0:
        raise ValueError("gambar kosong (semua piksel transparan)")
    if len(lab_s) > SAMPLE_SIZE:
        pick = np.random.default_rng(0).choice(len(lab_s), SAMPLE_SIZE, replace=False)
        rgb_s, lab_s = rgb_s[pick], lab_s[pick]
    lab_s = np.ascontiguousarray(lab_s, np.float32)

    # Sengaja pecah jadi banyak cluster, lalu gabungkan yang hampir sama.
    # Cara ini menemukan warna kecil (mis. garis Ungu Tua 0,5% area) yang terlewat bila
    # jumlah cluster dinaikkan satu per satu, karena k-means mengutamakan area besar.
    centers = kmeans(lab_s, AUTO_MAX_COLORS)
    idx, _ = nearest(lab_s, centers)
    clusters = [[float((idx == i).sum()), centers[i].astype(np.float64), [i]]
                for i in range(len(centers)) if (idx == i).any()]
    while len(clusters) > 1:
        cs = np.array([c[1] for c in clusters])
        d = np.sqrt(((cs[:, None] - cs[None]) ** 2).sum(-1))
        np.fill_diagonal(d, np.inf)
        a, b = np.unravel_index(d.argmin(), d.shape)
        if d[a, b] >= detail.merge_de:
            break
        (wa, ca, ia), (wb, cb, ib) = clusters[a], clusters[b]
        clusters[a] = [wa + wb, (ca * wa + cb * wb) / (wa + wb), ia + ib]
        del clusters[b]

    total = sum(c[0] for c in clusters)
    clusters = [c for c in clusters if c[0] / total >= detail.min_share] or clusters[:1]
    clusters.sort(key=lambda c: -c[0])
    # Warna sementara = median RGB anggota; refine_colors() nanti memakai gambar asli.
    # Median bisa lebih berdekatan daripada pusat cluster, jadi gabungkan sekali lagi.
    palette: list[np.ndarray] = []
    for _, _, members in clusters:  # urut dari yang terbesar
        color = np.median(rgb_s[np.isin(idx, members)], axis=0)
        c_lab = to_lab(color.round().astype(np.uint8))
        if all(np.linalg.norm(c_lab - to_lab(p.round().astype(np.uint8))) >= detail.merge_de
               for p in palette):
            palette.append(color)

    # Garis tipis hampir tak punya "bagian dalam", jadi bisa terlewat di atas.
    rgb_all = rgb[opaque]

    def pick(k: int, seed: int) -> np.ndarray:
        if len(rgb_all) <= k:
            return rgb_all
        return rgb_all[np.random.default_rng(seed).choice(len(rgb_all), k, replace=False)]

    palette, accents = add_missing_colors(pick(SAMPLE_SIZE, 1), pick(MISSING_SAMPLE, 3),
                                          palette, AUTO_MAX_COLORS, detail)
    return [rgb_to_hex(c) for c in palette], accents


def blend_distance(points: np.ndarray, colors: np.ndarray) -> np.ndarray:
    """Jarak (RGB) tiap titik ke campuran terdekat dua warna palet.

    Piksel tepi anti-aliasing adalah campuran dua warna yang bersebelahan, jadi letaknya
    di garis lurus antara keduanya dalam ruang RGB.
    """
    pts = points.astype(np.float32)
    best = np.full(len(pts), np.inf, np.float32)
    cols = colors.astype(np.float32)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            a, ab = cols[i], cols[j] - cols[i]
            t = np.clip(((pts - a) @ ab) / max(float(ab @ ab), 1e-6), 0, 1)
            d = np.sqrt(((pts - (a + t[:, None] * ab)) ** 2).sum(-1))
            np.minimum(best, d, out=best)
    return best


def add_missing_colors(rgb_all: np.ndarray, rgb_big: np.ndarray, palette: list[np.ndarray],
                       max_colors: int, detail: Detail) -> tuple[list[np.ndarray], list[bool]]:
    """Tambahkan warna yang tidak dijelaskan palet.

    Piksel dianggap sudah dijelaskan bila dekat dengan sebuah warna palet atau merupakan
    campuran dua warna palet (tepi anti-aliasing). Sisanya ditambahkan bila cukup banyak,
    atau, untuk warna aksen yang sangat berbeda (lidah merah muda di wajah ungu), walau
    areanya sangat kecil. Sisa piksel dikelompokkan, lalu kelompok yang paling jauh dari
    palet (inti garis, bukan gradasi tepinya) ditambahkan.

    `rgb_all` (sampel standar) dipakai untuk warna biasa; `rgb_big` (sampel besar) hanya
    untuk warna aksen, supaya area 0,02% tetap terhitung andal.
    Mengembalikan (palet, tanda aksen). Warna aksen hanya dipertahankan nanti bila berupa
    bidang, bukan pita tipis di tepi (lihat drop_edge_artifacts).
    """
    samples = [(rgb_all, to_lab(rgb_all.reshape(-1, 1, 3)).reshape(-1, 3)),
               (rgb_big, to_lab(rgb_big.reshape(-1, 1, 3)).reshape(-1, 3))]
    palette = list(palette)
    accent_flags = [False] * len(palette)

    def unexplained(rgb_s: np.ndarray, lab_s: np.ndarray, pal: np.ndarray, de: float):
        _, d2 = nearest(lab_s, to_lab(pal.round().astype(np.uint8)))
        far = np.flatnonzero(d2 > de**2)
        if len(pal) >= 2 and len(far):
            far = far[blend_distance(rgb_s[far], pal) > BLEND_RGB]
        return far

    while len(palette) < max_colors:
        pal = np.array(palette, np.float32)
        far = unexplained(*samples[0], pal, MISSING_DE)
        if len(far) >= detail.min_share * 3 * len(samples[0][0]):
            (rgb_s, lab_s), pool, is_accent = samples[0], far, False
        else:
            accent = unexplained(*samples[1], pal, ACCENT_DE)
            if len(accent) < max(ACCENT_SHARE * len(samples[1][0]), 20):
                break
            (rgb_s, lab_s), pool, is_accent = samples[1], accent, True
        mask = np.zeros(len(lab_s), bool)
        mask[pool] = True
        out_lab = np.ascontiguousarray(lab_s[mask])
        centers = kmeans(out_lab, 4)
        idx, _ = nearest(out_lab, centers)
        _, dc = nearest(centers, to_lab(pal.round().astype(np.uint8)))
        counts = np.bincount(idx, minlength=len(centers))
        big = counts >= 0.1 * len(out_lab)
        pick = int(np.argmax(np.where(big, dc, -1)))
        palette.append(np.median(rgb_s[mask][idx == pick], axis=0))
        accent_flags.append(is_accent)
    return palette, accent_flags


def refine_colors(rgb: np.ndarray, alpha: np.ndarray, palette: list[str],
                  detail: Detail) -> list[str]:
    """Ambil warna akhir dari gambar asli (bukan hasil denoise).

    Bila sebagian besar piksel sebuah warna bernilai persis sama (PNG bersih), warna itu
    yang dipakai, jadi #B26BFF tetap #B26BFF. Bila tidak (JPEG), dipakai median.
    """
    step = max(1, int(np.ceil(np.sqrt(alpha.size / 1.5e6))))
    rgb_s = rgb[::step, ::step]
    lab_s = to_lab(rgb_s)
    mask = flat_pixels(lab_s, alpha[::step, ::step] >= 128)
    rgb_f, lab_f = rgb_s[mask], lab_s[mask]
    pal_lab = to_lab(np.array([hex_to_rgb(c) for c in palette], np.uint8))
    idx, d2 = nearest(lab_f, pal_lab)
    close = d2 < max(detail.merge_de, 8.0) ** 2
    out = []
    for i, current in enumerate(palette):
        members = rgb_f[(idx == i) & close].astype(np.int64)
        if len(members) < 20:
            out.append(current)
            continue
        packed = (members[:, 0] << 16) | (members[:, 1] << 8) | members[:, 2]
        values, counts = np.unique(packed, return_counts=True)
        top = counts.argmax()
        if counts[top] >= 0.3 * len(members):
            v = int(values[top])
            out.append(rgb_to_hex(((v >> 16) & 255, (v >> 8) & 255, v & 255)))
        else:
            out.append(rgb_to_hex(np.median(members, axis=0)))
    return out


# ---------------------------------------------------------------------------
# Tahap 4: label piksel


def smooth_labels(labels: np.ndarray, n: int, sigma: float) -> np.ndarray:
    """Haluskan tepi bergerigi: setiap piksel ikut label yang paling dominan di sekitarnya
    (bobot Gaussian selebar `sigma`). Bercak dan tonjolan yang lebih kecil dari `sigma` hilang."""
    if sigma <= 0.3:
        return labels
    best = np.full(labels.shape, -1.0, np.float32)
    out = labels.copy()
    for i in range(n):
        m = labels == i
        if not m.any():
            continue
        vote = cv2.GaussianBlur(m.astype(np.float32), (0, 0), sigma)
        better = vote > best
        best[better] = vote[better]
        out[better] = i
    return out


def drop_edge_artifacts(labels: np.ndarray, lab: np.ndarray, pal_rgb: np.ndarray,
                        pal_lab: np.ndarray, thickness: float,
                        accents: list[bool]) -> tuple[np.ndarray, list[int]]:
    """Buang warna yang hanya muncul sebagai pita tipis di tepi dan berupa artefak:
    mirip warna lain (ringing, chroma bleed JPEG) atau campuran dua warna lain
    (anti-aliasing).

    Warna aksen (ditambahkan karena sangat berbeda walau areanya kecil) dibuang bila tidak
    ada bagiannya yang cukup tebal untuk memuat lingkaran berdiameter 2 × `thickness`:
    itu pita ringing JPEG, bukan lidah atau pipi merona.

    Piksel warna seperti itu dipindah ke warna tersisa yang paling mirip. Garis tipis yang
    kontras (mis. garis hitam di atas putih) tetap dipertahankan karena bukan keduanya.
    Mengembalikan (label baru, indeks warna yang dipertahankan).
    """
    n = len(pal_lab)
    r = max(1, int(thickness / 2 + 0.5))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    areas = np.bincount(labels.ravel(), minlength=n + 1)[:n]
    thin = []
    for i in range(n):
        if areas[i] == 0:
            continue
        core = cv2.erode((labels == i).astype(np.uint8), kernel).sum()
        if core < CORE_RATIO * areas[i]:
            thin.append(i)
    weak = [i for i in range(n) if accents[i] and areas[i] > 0 and cv2.distanceTransform(
        (labels == i).astype(np.uint8), cv2.DIST_L2, 3).max() < thickness]
    thin = [i for i in thin if i not in weak]
    keep = [i for i in range(n) if areas[i] > 0 and i not in thin and i not in weak]
    drop = list(weak)
    for i in sorted(thin, key=lambda j: areas[j]):  # yang terkecil dulu
        others = keep + [t for t in thin if t not in drop and t != i]
        if not others:
            keep.append(i)
            continue
        de = np.sqrt(((pal_lab[others] - pal_lab[i]) ** 2).sum(-1)).min()
        blend = (len(others) >= 2 and
                 blend_distance(pal_rgb[i:i + 1], pal_rgb[others])[0] < BLEND_RGB)
        if de < HALO_DE or blend:
            drop.append(i)
        else:
            keep.append(i)
    keep = sorted(keep)
    if not drop:
        return labels, keep
    gone = np.isin(labels, drop)
    sub, _ = nearest(lab[gone], pal_lab[keep])
    labels = labels.copy()
    labels[gone] = np.asarray(keep)[sub]
    return labels, keep


def reduce_colors(labels: np.ndarray, lab: np.ndarray, pal_lab: np.ndarray,
                  target: int) -> tuple[np.ndarray, list[int]]:
    """Sederhanakan jadi `target` warna dengan total selisih warna sekecil mungkin.

    Warna dibuang satu per satu. Setiap kali, yang dibuang adalah warna yang bila dilebur
    ke warna pengganti terbaiknya menambah selisih warna (ΔE) paling sedikit secara total:
    luas area × kenaikan selisih rata-rata. Jadi area kecil yang warnanya mirip tetangganya
    (kilau tipis, gradasi, warna kembar) dibuang lebih dulu, sedangkan area luas dan warna
    yang sangat berbeda dipertahankan. Warna yang sangat berbeda dari penggantinya
    (ΔE ≥ ACCENT_DE, mis. lidah merah muda di wajah ungu) dihitung seolah luasnya
    minimal REDUCE_ACCENT_AREA, karena detail kecil yang kontras paling mudah terlihat.

    Setiap area tersambung dari warna yang dibuang dipindah utuh ke satu warna pengganti,
    supaya bentuknya tetap rapi (tidak belang seperti bila tiap piksel dipindah sendiri).
    Mengembalikan (label baru, indeks warna yang dipertahankan).
    """
    n = len(pal_lab)
    flat = labels.ravel()
    idx = np.flatnonzero(flat < n)
    if len(idx) > REDUCE_SAMPLE:
        idx = np.random.default_rng(2).choice(idx, REDUCE_SAMPLE, replace=False)
    cur = flat[idx].copy()
    pts = lab.reshape(-1, 3)[idx]
    dist = np.stack([np.sqrt(((pts - c) ** 2).sum(-1)) for c in pal_lab], axis=1)
    alive = [i for i in range(n) if (cur == i).any()]
    while len(alive) > max(target, 1):
        best = None
        for i in alive:
            others = [j for j in alive if j != i]
            m = cur == i
            means = dist[m].mean(0)
            j = others[int(np.argmin(means[others]))]
            shift = max(float(means[j] - dist[m, i].mean()), 0.0)
            distinct = np.linalg.norm(pal_lab[i] - pal_lab[j]) >= ACCENT_DE
            area = max(m.mean(), REDUCE_ACCENT_AREA) if distinct else m.mean()
            cost = area * shift
            if best is None or cost < best[0]:
                best = (cost, i, j)
        _, i, j = best
        cur[cur == i] = j
        alive.remove(i)

    removed = [i for i in range(n) if i not in alive and (labels == i).any()]
    if not removed:
        return labels, alive
    comp = np.zeros(labels.shape, np.int32)
    count = 0
    for i in removed:
        m = labels == i
        k, cc = cv2.connectedComponents(m.astype(np.uint8), connectivity=8)
        comp[m] = cc[m] + count
        count += k - 1
    gone = comp > 0
    ids = comp[gone] - 1
    px = lab[gone]
    sums = np.stack([np.bincount(ids, weights=np.sqrt(((px - pal_lab[j]) ** 2).sum(-1)),
                                 minlength=count) for j in alive], axis=1)
    labels = labels.copy()
    labels[gone] = np.asarray(alive)[sums.argmin(1)][ids]
    return labels, alive


def compact(labels: np.ndarray, palette: list[str], keep: list[int]):
    """Sisakan warna `keep` saja dengan indeks rapat 0..len(keep)-1 (urutan `keep`).

    Label warna yang dibuang harus sudah dipindah sebelumnya. Transparan tetap di indeks
    terakhir."""
    n = len(palette)
    remap = np.full(n + 1, len(keep), np.int32)
    remap[keep] = np.arange(len(keep))
    return remap[labels], [palette[i] for i in keep]


def background_label(labels: np.ndarray, n_colors: int) -> int | None:
    """Warna yang menguasai pinggir gambar (≥60%), atau None."""
    border = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    border = border[border < n_colors]
    if len(border) == 0:
        return None
    values, counts = np.unique(border, return_counts=True)
    top = counts.argmax()
    return int(values[top]) if counts[top] >= 0.6 * len(border) else None


def remove_background(labels: np.ndarray, bg: int, transparent: int) -> np.ndarray:
    """Buat transparan area latar yang tersambung ke pinggir gambar saja.

    Area berwarna sama di dalam objek (mis. garis mulut berwarna gelap) tetap ada.
    """
    mask = (labels == bg).astype(np.uint8)
    n, comp = cv2.connectedComponents(mask, connectivity=4)
    edge_ids = np.unique(np.concatenate([comp[0], comp[-1], comp[:, 0], comp[:, -1]]))
    edge_ids = edge_ids[edge_ids > 0]
    out = labels.copy()
    out[np.isin(comp, edge_ids)] = transparent
    return out


# ---------------------------------------------------------------------------
# Tahap 4b: gradasi (bayangan lembut, kilau, shading halus)


@dataclass
class Gradient:
    kind: str  # "radial" (elips) atau "linear"
    geometry: tuple[float, ...]  # radial: matriks SVG (a, b, c, d, e, f); linear: (x1, y1, x2, y2)
    stops: list[tuple[float, str, float]]  # (offset 0..1, hex, opacity)


def fill_holes(mask: np.ndarray) -> np.ndarray:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros(mask.shape, np.uint8)
    cv2.drawContours(filled, contours, -1, 1, thickness=cv2.FILLED)
    return filled.astype(bool)


def gradient_profile(t: np.ndarray, rgb_px: np.ndarray):
    """Warna median per pita t (0..1); kembalikan (offset, warna, prediksi per piksel)."""
    k = GRADIENT_STOPS
    idx = np.clip((t * k).astype(int), 0, k - 1)
    offsets, colors = [], []
    for i in range(k):
        m = idx == i
        if m.sum() >= 5:
            offsets.append((i + 0.5) / k)
            colors.append(np.median(rgb_px[m], axis=0))
    if len(offsets) < 2:
        return None
    offsets_a, colors_a = np.array(offsets), np.array(colors)
    pred = np.stack([np.interp(t, offsets_a, colors_a[:, c]) for c in range(3)], axis=1)
    return offsets_a, colors_a, pred


def gradient_models(xy: np.ndarray, shape_xy: np.ndarray, lab_px: np.ndarray):
    """Kandidat (jenis, geometri, t per piksel): elips dari bentuk area, dan linear searah
    perubahan warna terbesar."""
    models = []
    mu = shape_xy.mean(0)
    cov = np.cov((shape_xy - mu).T)
    evals, evecs = np.linalg.eigh(cov)
    if evals.min() > 0.25:
        r_shape = np.sqrt(np.einsum("ij,jk,ik->i", shape_xy - mu, np.linalg.inv(cov),
                                    shape_xy - mu))
        r_max = max(float(np.percentile(r_shape, 99.5)), 1e-6)
        r = np.sqrt(np.einsum("ij,jk,ik->i", xy - mu, np.linalg.inv(cov), xy - mu))
        m = evecs @ np.diag(np.sqrt(evals) * r_max)
        models.append(("radial", (m[0, 0], m[1, 0], m[0, 1], m[1, 1], mu[0], mu[1]),
                       np.clip(r / r_max, 0, 1)))
    centered = xy - xy.mean(0)
    design = np.column_stack([np.ones(len(xy)), centered])
    coef, *_ = np.linalg.lstsq(design, lab_px, rcond=None)
    _, _, vt = np.linalg.svd(coef[1:].T)
    u = vt[0]
    proj = (xy - mu) @ u
    t0, t1 = np.percentile(proj, [0.5, 99.5])
    if t1 - t0 > 1:
        p0, p1 = mu + t0 * u, mu + t1 * u
        models.append(("linear", (p0[0], p0[1], p1[0], p1[1]),
                       np.clip((proj - t0) / (t1 - t0), 0, 1)))
    return models


def gradient_t(kind: str, geom, xy: np.ndarray) -> np.ndarray:
    """Posisi 0..1 tiap titik pada gradasi dengan geometri SVG `geom`."""
    if kind == "radial":
        a, b, c, d, e, f = geom
        inv = np.linalg.inv(np.array([[a, c], [b, d]]))
        local = (xy - (e, f)) @ inv.T
        return np.clip(np.sqrt((local ** 2).sum(1)), 0, 1)
    x1, y1, x2, y2 = geom
    u = np.array([x2 - x1, y2 - y1])
    return np.clip(((xy - (x1, y1)) @ u) / max(float(u @ u), 1e-9), 0, 1)


def fit_gradient(xy, shape_xy, rgb_px, lab_px, max_step: float = GRADIENT_MAX_STEP):
    """Model gradasi terbaik: (rata-rata ΔE, jenis, geometri, offset, warna, ΔE per piksel)."""
    best = None
    for kind, geom, t in gradient_models(xy, shape_xy, lab_px):
        prof = gradient_profile(t, rgb_px)
        if prof is None:
            continue
        offsets, colors, pred = prof
        # Perubahan bertahap saja: pupil hitam di tengah putih mata bukan gradasi.
        stops_lab = to_lab(colors.round().clip(0, 255).astype(np.uint8))
        if np.sqrt((np.diff(stops_lab, axis=0) ** 2).sum(-1)).max() > max_step:
            continue
        spread = stops_lab[:, None] - stops_lab[None]
        if np.sqrt((spread ** 2).sum(-1)).max() < GRADIENT_MIN_RANGE:
            continue  # warna rata yang sedikit lebih tepat, bukan gradasi
        err = np.sqrt(((to_lab(pred.round().clip(0, 255).astype(np.uint8)) - lab_px) ** 2)
                      .sum(-1))
        if best is None or err.mean() < best[0]:
            best = (float(err.mean()), kind, geom, offsets, colors, err)
    return best


def fade_stops(offsets, colors, bg_rgb) -> list[tuple[float, str, float]]:
    """Ubah warna yang memudar ke latar (yang dihapus) menjadi warna + transparansi,
    supaya bayangan tetap memudar di atas latar apa pun."""
    bg = np.asarray(bg_rgb, np.float64)
    core = colors[int(np.argmax(np.linalg.norm(colors - bg, axis=1)))]
    axis = core - bg
    stops = []
    for off, c in zip(offsets, colors, strict=True):
        a = float(np.clip((c - bg) @ axis / max(axis @ axis, 1e-6), 0, 1))
        color = core if a < 0.05 else np.clip(bg + (c - bg) / a, 0, 255)
        stops.append((float(off), rgb_to_hex(color), a))
    return stops


def find_gradients(labels: np.ndarray, lab: np.ndarray, rgb: np.ndarray, pal_lab: np.ndarray,
                   n: int, scale: float, removed_rgb) -> tuple[np.ndarray, list[Gradient]]:
    """Cari area yang lebih cocok diisi gradasi daripada bidang-bidang warna rata.

    Setiap area (beserta pita-pita di dalamnya) dicoba diisi gradasi elips atau linear yang
    dicocokkan dengan piksel aslinya. Gradasi dipakai hanya bila selisihnya jauh lebih kecil
    daripada versi bidang rata. Piksel yang tidak cocok dengan gradasi (mis. ujung cakar di
    atas bayangan) tetap menjadi bentuk sendiri di atasnya. Label area gradasi ke-k menjadi
    n + 1 + k (n = transparan).
    """
    h, w = labels.shape
    min_px = GRADIENT_MIN_AREA * max(scale, 1) ** 2
    max_px = GRADIENT_MAX_SHARE * h * w

    # Bentuk tersambung (komponen) per warna, dengan id global.
    comp = np.zeros(labels.shape, np.int32)
    comp_label, boxes, areas = [0], [None], [0]
    for i in range(n):
        k, cc, stats, _ = cv2.connectedComponentsWithStats((labels == i).astype(np.uint8),
                                                           connectivity=8)
        m = cc > 0
        comp[m] = cc[m] + len(comp_label) - 1
        for j in range(1, k):
            x, y, bw, bh, area = stats[j]
            comp_label.append(i)
            boxes.append((x, y, x + bw, y + bh))
            areas.append(int(area))
    areas_a = np.array(areas)

    def candidate(members: list[int]):
        x0 = max(min(boxes[c][0] for c in members) - 2, 0)
        y0 = max(min(boxes[c][1] for c in members) - 2, 0)
        x1 = min(max(boxes[c][2] for c in members) + 2, w)
        y1 = min(max(boxes[c][3] for c in members) + 2, h)
        filled = fill_holes(np.isin(comp[y0:y1, x0:x1], members))
        return int(filled.sum()), (x0, y0, x1, y1), filled

    # Kandidat 1: satu bentuk beserta semua yang ada di dalamnya (pita yang melingkar).
    cands = [candidate([c]) for c in range(1, len(areas)) if min_px <= areas[c] <= max_px]
    # Kandidat 2: bentuk-bentuk bersebelahan yang warnanya mirip (pita yang berjajar, mis.
    # bayangan yang ujung-ujungnya memudar). Bentuk yang sangat luas (latar) tidak ikut.
    parent = list(range(len(areas)))

    def root(c: int) -> int:
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    pairs = np.concatenate([
        np.stack([comp[:, :-1].ravel(), comp[:, 1:].ravel()], 1),
        np.stack([comp[:-1].ravel(), comp[1:].ravel()], 1)])
    pairs = pairs[(pairs[:, 0] != pairs[:, 1]) & (pairs > 0).all(1)]
    pairs = np.unique(np.sort(pairs, 1), axis=0)
    lab_of = np.array(comp_label)
    near = np.sqrt(((pal_lab[lab_of[pairs[:, 0]]] - pal_lab[lab_of[pairs[:, 1]]]) ** 2)
                   .sum(-1)) <= 2 * GRADIENT_MAX_STEP
    small = (areas_a[pairs[:, 0]] <= max_px) & (areas_a[pairs[:, 1]] <= max_px)
    for a, b in pairs[near & small]:
        parent[root(int(a))] = root(int(b))
    groups: dict[int, list[int]] = {}
    for c in range(1, len(areas)):
        groups.setdefault(root(c), []).append(c)
    for members in groups.values():
        total = int(areas_a[members].sum())
        if len(members) > 1 and min_px <= total <= max_px:
            cands.append(candidate(members))
    cands.sort(key=lambda c: -c[0])

    used = np.zeros(labels.shape, bool)
    labels = labels.copy()
    gradients: list[Gradient] = []
    er = max(1, round(1.5 * max(scale, 1)))
    edge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * er + 1, 2 * er + 1))
    rng = np.random.default_rng(4)

    def sample(count: int, size: int) -> np.ndarray:
        return np.arange(size) if size <= count else rng.choice(size, count, replace=False)

    def try_fit(xy, shape_xy, sy, sx, max_step=GRADIENT_MAX_STEP):
        """Cocokkan gradasi; kembalikan fit bila lolos semua syarat."""
        lab_px, rgb_px = lab[sy, sx], rgb[sy, sx].astype(np.float64)
        fit = fit_gradient(xy, shape_xy, rgb_px, lab_px, max_step)
        if fit is None:
            return None
        inl = fit[5] < GRADIENT_INLIER_DE
        if inl.mean() < GRADIENT_MIN_INLIERS:
            return None
        fit = fit_gradient(xy[inl], shape_xy, rgb_px[inl], lab_px[inl], max_step)
        if fit is None:
            return None
        # Pembanding: warna rata terbaik untuk tiap bagian (median pikselnya sendiri),
        # bukan warna palet; kalau tidak, warna rata yang sedikit lebih tepat dikira gradasi.
        part = labels[sy[inl], sx[inl]]
        best_flat = np.zeros_like(lab_px[inl])
        for lb in np.unique(part):
            best_flat[part == lb] = np.median(lab_px[inl][part == lb], axis=0)
        flat_err = np.sqrt(((best_flat - lab_px[inl]) ** 2).sum(-1)).mean()
        if fit[0] > GRADIENT_GAIN * flat_err or flat_err - fit[0] < GRADIENT_MIN_DROP:
            return None
        return fit

    def fit_pixels(ys: np.ndarray, xs: np.ndarray, shape_xy: np.ndarray,
                   max_step: float = GRADIENT_MAX_STEP):
        """Saring cepat dengan sampel kecil (kebanyakan area memang rata), lalu cocokkan."""
        quick = sample(3_000, len(xs))
        if try_fit(np.column_stack([xs[quick] + 0.5, ys[quick] + 0.5]), shape_xy,
                   ys[quick], xs[quick], max_step) is None:
            return None
        pick = sample(GRADIENT_SAMPLE, len(xs))
        return try_fit(np.column_stack([xs[pick] + 0.5, ys[pick] + 0.5]), shape_xy,
                       ys[pick], xs[pick], max_step)

    def residual(fit, ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
        _, kind, geom, offsets, colors, _ = fit
        t = gradient_t(kind, geom, np.column_stack([xs + 0.5, ys + 0.5]))
        pred = np.stack([np.interp(t, offsets, colors[:, c]) for c in range(3)], 1)
        return np.sqrt(((to_lab(pred.round().clip(0, 255).astype(np.uint8))
                         - lab[ys, xs]) ** 2).sum(-1))

    def interior_fit(group, inner, shape_xy, x0, y0):
        """Gradasi di bagian dalam area (shading halus). Tepi tidak dinilai: piksel
        anti-aliasing bergeser warna, dan gradasi "menggelap ke tepi" bisa menirunya walau
        bidangnya rata."""
        ys, xs = np.nonzero(inner)
        if len(xs) < min_px / 2:
            return None
        fit = fit_pixels(ys + y0, xs + x0, shape_xy)
        if fit is None:
            return None
        gy, gx = np.nonzero(group)
        err = residual(fit, gy + y0, gx + x0)
        # Semua piksel area ikut, kecuali yang di bagian dalam jelas bukan gradasi (bentuk
        # lain di atasnya). Tepi ikut supaya tidak tersisa cincin warna lama.
        return fit, (y0, x0), group, ~(inner[gy, gx] & (err >= GRADIENT_INLIER_DE))

    def feather_fit(group, x0, y0):
        """Bentuk yang tepinya memudar ke latar (bayangan, glow): area diperluas ke latar
        di sekelilingnya dan gradasi dicocokkan sampai memudar ke warna latar."""
        m = max(2, round(GRADIENT_FEATHER * max(scale, 1)))
        gh, gw = group.shape
        fx0, fy0 = max(x0 - m, 0), max(y0 - m, 0)
        fx1, fy1 = min(x0 + gw + m, w), min(y0 + gh + m, h)
        gmask = np.zeros((fy1 - fy0, fx1 - fx0), np.uint8)
        gmask[y0 - fy0:y0 - fy0 + gh, x0 - fx0:x0 - fx0 + gw] = group
        disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * m + 1, 2 * m + 1))
        ring = cv2.dilate(gmask, disk).astype(bool) & ~gmask.astype(bool)
        lab_crop = labels[fy0:fy1, fx0:fx1]
        ring &= ~used[fy0:fy1, fx0:fx1] & (lab_crop < n)
        if not ring.any():
            return None
        values, counts = np.unique(lab_crop[ring], return_counts=True)
        surround = values[counts.argmax()]
        if counts.max() < 0.8 * ring.sum():
            return None  # bukan di atas satu latar
        region = gmask.astype(bool) | (ring & (lab_crop == surround))
        ys, xs = np.nonzero(region)
        # Elips mengikuti bentuk inti; perluasan ke latar hanya untuk menilai pudarnya.
        cy, cx = np.nonzero(gmask)
        shape_xy = np.column_stack([cx + fx0 + 0.5, cy + fy0 + 0.5])[sample(20_000, len(cx))]
        fit = fit_pixels(ys + fy0, xs + fx0, shape_xy, GRADIENT_FEATHER_STEP)
        if fit is None:
            return None
        err = residual(fit, ys + fy0, xs + fx0)
        # Latar yang tidak ikut memudar tetap latar; bagian area sendiri ikut semuanya.
        return fit, (fy0, fx0), region, gmask[ys, xs].astype(bool) | (err < GRADIENT_INLIER_DE)

    for _, (x0, y0, x1, y1), filled in cands:
        crop = labels[y0:y1, x0:x1]
        group = inside_parts(crop, filled, n)
        if used[y0:y1, x0:x1][group].any() or group.sum() < min_px:
            continue
        gy, gx = np.nonzero(group)
        shape_xy = np.column_stack([gx + x0 + 0.5, gy + y0 + 0.5])[sample(20_000, len(gx))]
        inner = cv2.erode(group.astype(np.uint8), edge_kernel).astype(bool)
        found = interior_fit(group, inner, shape_xy, x0, y0)
        if found is None:
            found = feather_fit(group, x0, y0)
        if found is None:
            continue
        fit, (fy0, fx0), region, keep = found
        _, kind, geom, offsets, colors, _ = fit
        ry, rx = np.nonzero(region)
        g = len(gradients)
        labels[ry[keep] + fy0, rx[keep] + fx0] = n + 1 + g
        used[fy0:fy0 + region.shape[0], fx0:fx0 + region.shape[1]] |= region
        touches_bg = False
        if removed_rgb is not None:
            ring = cv2.dilate(filled.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            touches_bg = bool((crop[ring] == n).any())
        stops = (fade_stops(offsets, colors, removed_rgb) if touches_bg else
                 [(float(o), rgb_to_hex(c), 1.0) for o, c in zip(offsets, colors, strict=True)])
        gradients.append(Gradient(kind=kind, geometry=tuple(float(v) for v in geom),
                                  stops=stops))
    return labels, gradients


def inside_parts(crop: np.ndarray, filled: np.ndarray, n: int) -> np.ndarray:
    """Bagian dari `filled` yang terdiri atas bentuk-bentuk yang seluruhnya di dalamnya
    (pita-pita gradasi). Bentuk yang hanya menumpang sebagian (karakter di atas bayangan)
    tidak diikutkan."""
    out = np.zeros(filled.shape, bool)
    for i in np.unique(crop[filled]):
        if i >= n:
            continue
        k, cc = cv2.connectedComponents((crop == i).astype(np.uint8), connectivity=8)
        inside = np.ones(k, bool)
        inside[np.unique(cc[~filled])] = False
        edge = np.concatenate([cc[0], cc[-1], cc[:, 0], cc[:, -1]])
        inside[np.unique(edge)] = False
        inside[0] = False
        out |= inside[cc]
    return out


def marker_colors(count: int, palette_rgb: np.ndarray) -> list[tuple[int, int, int]]:
    """Warna pengganti untuk area gradasi saat dilacak: unik, dan jauh dari warna palet
    supaya tidak tertukar. Diambil dari grid tetap, jadi selalu selesai."""
    out: list[tuple[int, int, int]] = []
    pal = palette_rgb.astype(np.float64)
    for r in range(3, 256, 9):
        for g in range(3, 256, 9):
            for b in range(3, 256, 9):
                if len(out) == count:
                    return out
                if len(pal) == 0 or np.sqrt(((pal - (r, g, b)) ** 2).sum(1)).min() >= 24:
                    out.append((r, g, b))
    raise ValueError("terlalu banyak area gradasi")


def parse_translate(value: str | None) -> tuple[float, float]:
    if not value or not value.startswith("translate("):
        return 0.0, 0.0
    parts = value[len("translate("):-1].replace(",", " ").split()
    return float(parts[0]), float(parts[1]) if len(parts) > 1 else 0.0


def gradient_element(g: Gradient, gid: str, tx: float, ty: float) -> ET.Element:
    """Elemen gradasi SVG dalam koordinat path (path VTracer memakai translate sendiri)."""
    if g.kind == "radial":
        a, b, c, d, e, f = g.geometry
        el = ET.Element(f"{{{SVG_NS}}}radialGradient", {
            "id": gid, "gradientUnits": "userSpaceOnUse", "cx": "0", "cy": "0", "r": "1",
            "gradientTransform": f"matrix({a:.4f} {b:.4f} {c:.4f} {d:.4f} "
                                 f"{e - tx:.2f} {f - ty:.2f})"})
    else:
        x1, y1, x2, y2 = g.geometry
        el = ET.Element(f"{{{SVG_NS}}}linearGradient", {
            "id": gid, "gradientUnits": "userSpaceOnUse",
            "x1": f"{x1 - tx:.2f}", "y1": f"{y1 - ty:.2f}",
            "x2": f"{x2 - tx:.2f}", "y2": f"{y2 - ty:.2f}"})
    for off, color, opacity in g.stops:
        attrs = {"offset": f"{off:.3f}", "stop-color": color}
        if opacity < 0.999:
            attrs["stop-opacity"] = f"{opacity:.3f}"
        ET.SubElement(el, f"{{{SVG_NS}}}stop", attrs)
    return el


# ---------------------------------------------------------------------------
# Tahap 5–6: lacak dan rapikan SVG


def trace(rgba: np.ndarray, opts: Options, detail: Detail, scale: float) -> str:
    prec = PRECISIONS[opts.precision]
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG")
    return vtracer.convert_raw_image_to_svg(
        buf.getvalue(),
        img_format="png",
        colormode="color",
        hierarchical=opts.stacking,
        mode="spline",
        filter_speckle=max(1, round(detail.speckle * max(scale, 1))),
        color_precision=8,
        layer_difference=1,
        corner_threshold=detail.corner,
        length_threshold=4.0,
        max_iterations=10,
        splice_threshold=prec.splice,
        path_precision=1,
    )


def path_labels(svg: str, labels: np.ndarray, n_labels: int) -> list[int | None]:
    """Label yang diwakili tiap path: label terbanyak di piksel yang terlihat dari path itu.

    SVG dirender sekali tanpa anti-aliasing, dengan warna identitas unik per path. Ini
    lebih andal daripada membaca warna fill VTracer, yang merata-ratakan warna bentuk kecil
    yang digabung ke induknya. None bila path tidak terlihat sama sekali.
    """
    root = ET.fromstring(svg)
    root.set("shape-rendering", "crispEdges")
    els = list(root.iter(f"{{{SVG_NS}}}path"))
    for i, el in enumerate(els):
        v = i + 1
        el.set("fill", f"#{(v >> 16) & 255:02X}{(v >> 8) & 255:02X}{v & 255:02X}")
    h, w = labels.shape
    png = cairosvg.svg2png(bytestring=ET.tostring(root), output_width=w, output_height=h)
    with Image.open(io.BytesIO(png)) as im:
        px = np.asarray(im.convert("RGBA")).astype(np.int64)
    ids = (px[..., 0] << 16) | (px[..., 1] << 8) | px[..., 2]
    ok = (px[..., 3] == 255) & (ids >= 1) & (ids <= len(els))
    key = (ids[ok] - 1) * n_labels + labels[ok]
    counts = np.bincount(key, minlength=len(els) * n_labels).reshape(len(els), n_labels)
    return [int(c.argmax()) if c.sum() else None for c in counts]


def clean_svg(svg: str, palette_rgb: np.ndarray, palette_hex: list[str],
              size: tuple[int, int], work: tuple[int, int],
              fills: list | None = None) -> tuple[str, int]:
    """Rapikan SVG VTracer: ukuran asli dan setiap fill dikunci ke palet.

    `fills` (opsional, per path) memberi isian yang sudah pasti: hex warna palet atau
    Gradient. Path tanpa isian pasti dikunci ke warna palet terdekat.
    """
    root = ET.fromstring(svg)
    root.attrib.pop("version", None)
    root.set("width", str(size[0]))
    root.set("height", str(size[1]))
    root.set("viewBox", f"0 0 {work[0]} {work[1]}")
    pal_lab = to_lab(palette_rgb.astype(np.uint8))
    defs = ET.Element(f"{{{SVG_NS}}}defs")
    paths = 0
    for i, el in enumerate(root.iter(f"{{{SVG_NS}}}path")):
        paths += 1
        known = fills[i] if fills and i < len(fills) else None
        if isinstance(known, Gradient):
            tx, ty = parse_translate(el.get("transform"))
            gid = f"g{len(defs)}"
            defs.append(gradient_element(known, gid, tx, ty))
            el.set("fill", f"url(#{gid})")
            continue
        if known:
            el.set("fill", known)
            continue
        fill = el.get("fill")
        if fill and fill.startswith("#"):
            lab = to_lab(np.array(hex_to_rgb(fill), np.uint8))
            el.set("fill", palette_hex[int(np.argmin(((pal_lab - lab) ** 2).sum(-1)))])
    if len(defs):
        root.insert(0, defs)
    body = ET.tostring(root, encoding="unicode")
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Dibuat dengan Helonoia Vectorizer -->\n'
    return header + body + "\n", paths


# ---------------------------------------------------------------------------
# Inti


def vectorize(rgb: np.ndarray, alpha: np.ndarray, opts: Options) -> Result:
    detail = DETAILS[opts.detail]
    h, w = alpha.shape
    work_rgb, opaque, scale, base = prepare(rgb, alpha, detail, PRECISIONS[opts.precision])
    wh, ww = opaque.shape
    lab = to_lab(work_rgb)

    locked = opts.palette is not None
    if locked:
        palette, accents = list(opts.palette), [False] * len(opts.palette)
    else:
        palette, accents = estimate_palette(*palette_view(base, (w, h)), detail)
        # Hex asli dulu, baru label: label dari warna sementara menggeser batas tepi.
        refined: dict[str, bool] = {}
        for c, a in zip(refine_colors(rgb, alpha, palette, detail), accents, strict=True):
            refined[c] = refined.get(c, True) and a
        palette, accents = list(refined), list(refined.values())
    n = len(palette)
    transparent = n
    pal_lab = to_lab(np.array([hex_to_rgb(c) for c in palette], np.uint8))

    labels, _ = nearest(lab, pal_lab)
    labels[~opaque] = transparent
    if not locked:
        pal_rgb0 = np.array([hex_to_rgb(c) for c in palette], np.float32)
        labels, kept = drop_edge_artifacts(labels, lab, pal_rgb0, pal_lab,
                                           detail.thickness * scale, accents)
        if len(kept) < n:
            labels, palette = compact(labels, palette, kept)
    sigma = detail.edge_sigma * scale
    labels = smooth_labels(labels, len(palette) + 1, sigma)
    present = [i for i in range(len(palette)) if (labels == i).any()]
    labels, palette = compact(labels, palette, present)
    found = len(palette)
    if not locked and opts.colors and len(palette) > opts.colors:
        pal_lab = to_lab(np.array([hex_to_rgb(c) for c in palette], np.uint8))
        labels, kept = reduce_colors(labels, lab, pal_lab, opts.colors)
        labels, palette = compact(labels, palette, kept)
        labels = smooth_labels(labels, len(palette) + 1, sigma)
    n = len(palette)
    transparent = n
    pal_rgb = np.array([hex_to_rgb(c) for c in palette], np.float32)

    removed = None
    if opts.remove_bg:
        bg = background_label(labels, n)
        if bg is not None:
            if opts.remove_bg == "semua":
                labels = np.where(labels == bg, transparent, labels)
            else:
                labels = remove_background(labels, bg, transparent)
            removed = palette[bg]

    # Urutkan palet dari area terbesar, buang warna yang tak terpakai.
    counts = np.bincount(labels.ravel(), minlength=n + 1)[:n]
    order = [i for i in np.argsort(-counts) if counts[i] > 0]
    if not order:
        raise ValueError("tidak ada yang tersisa untuk dilacak (semua piksel transparan)")
    used_hex = [palette[i] for i in order]
    used_rgb = pal_rgb[order]
    total = counts.sum()
    shares = [counts[i] / total for i in order]

    grads: list[Gradient] = []
    if opts.gradients and cairosvg is not None:  # pemetaan path→gradasi butuh render
        labels, grads = find_gradients(labels, lab, work_rgb, to_lab(pal_rgb.astype(np.uint8)),
                                       n, scale, hex_to_rgb(removed) if removed else None)
    marks = marker_colors(len(grads), pal_rgb)

    lut = np.zeros((n + 1 + len(grads), 4), np.uint8)
    lut[:n, :3] = pal_rgb.round().astype(np.uint8)
    lut[:n, 3] = 255
    for k, c in enumerate(marks):
        lut[n + 1 + k] = (*c, 255)
    rgba = lut[labels]

    raw = trace(rgba, opts, detail, scale)
    fills = None
    if grads:
        fill_of = {i: palette[i] for i in range(n)} | {n + 1 + k: g for k, g in enumerate(grads)}
        fills = [fill_of.get(lb) if lb is not None else None
                 for lb in path_labels(raw, labels, n + 1 + len(grads))]
    svg, paths = clean_svg(raw, used_rgb, used_hex, (w, h), (ww, wh), fills)
    return Result(svg=svg, palette=used_hex, shares=shares, paths=paths, size=(w, h),
                  work_size=(ww, wh), removed_bg=removed, found_colors=found,
                  gradients=len(grads), debug_image=Image.fromarray(rgba, "RGBA"))


# ---------------------------------------------------------------------------
# Laporan dan output


def render(svg: str, size: tuple[int, int]) -> np.ndarray:
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size[0], output_height=size[1])
    with Image.open(io.BytesIO(png)) as im:
        return np.asarray(im.convert("RGBA"))


def similarity(result: Result, rgb: np.ndarray, alpha: np.ndarray) -> tuple[float, float] | None:
    """(PSNR dB, ΔE rata-rata) antara render SVG dan gambar asli, di atas latar yang sama."""
    if cairosvg is None:
        return None
    out = render(result.svg, result.size).astype(np.float32)
    base = np.array(hex_to_rgb(result.removed_bg or "#FFFFFF"), np.float32)
    a_in = alpha[..., None].astype(np.float32) / 255
    a_out = out[..., 3:4] / 255
    src = rgb.astype(np.float32) * a_in + base * (1 - a_in)
    dst = out[..., :3] * a_out + base * (1 - a_out)
    mse = ((src - dst) ** 2).mean()
    psnr = float("inf") if mse == 0 else 10 * np.log10(255**2 / mse)
    de = np.sqrt(((to_lab(src.round().astype(np.uint8)) -
                   to_lab(dst.round().astype(np.uint8))) ** 2).sum(-1)).mean()
    return float(psnr), float(de)


def write_outputs(result: Result, svg_path: Path, formats: list[str]) -> list[Path]:
    written = []
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(result.svg, encoding="utf-8")
    written.append(svg_path)
    for fmt in formats:
        if fmt == "svg":
            continue
        if cairosvg is None:
            raise RuntimeError(f"format {fmt} butuh cairosvg (pip install cairosvg)")
        target = svg_path.with_suffix(f".{fmt}")
        convert = {"pdf": cairosvg.svg2pdf, "eps": cairosvg.svg2eps, "png": cairosvg.svg2png}[fmt]
        convert(bytestring=result.svg.encode(), write_to=str(target))
        written.append(target)
    if "svg" not in formats:  # SVG tetap dibuat sebagai sumber, tapi dihapus bila tak diminta
        svg_path.unlink()
        written.remove(svg_path)
    return written


def collect_inputs(items: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in items:
        p = Path(item)
        if p.is_dir():
            found = sorted(f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXTS)
            if not found:
                print(f"peringatan: tidak ada gambar di folder {p}", file=sys.stderr)
            files.extend(found)
        elif p.is_file():
            files.append(p)
        else:
            raise FileNotFoundError(f"tidak ditemukan: {p}")
    return files


def output_path(src: Path, output: str | None, many: bool) -> Path:
    if output is None:
        return src.with_suffix(".svg")
    out = Path(output)
    if not many and out.suffix.lower() == ".svg":
        return out
    return out / f"{src.stem}.svg"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vectorize.py",
        description="Ubah logo dan ilustrasi flat (PNG/JPG/WebP) menjadi SVG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Contoh:\n"
               "  python3 vectorizer/vectorize.py logo.jpg\n"
               "  python3 vectorizer/vectorize.py logo.jpg -o hasil/ -p helonoia --remove-bg\n"
               "  python3 vectorizer/vectorize.py folder/ -o hasil/ --format svg,pdf",
    )
    p.add_argument("inputs", nargs="+", help="file gambar atau folder berisi gambar")
    p.add_argument("-o", "--output",
                   help="file .svg (untuk satu input) atau folder. Default: di sebelah file input")
    color = p.add_mutually_exclusive_group()
    color.add_argument("-c", "--colors", type=int,
                       help="sederhanakan jadi paling banyak N warna; yang dibuang lebih dulu "
                            "adalah warna yang paling sedikit pengaruhnya pada tampilan. "
                            "Default: semua warna yang ditemukan")
    color.add_argument("-p", "--palette",
                       help="kunci warna ke palet: 'helonoia' atau daftar hex, "
                            "mis. '#120B1E,#B26BFF,#FFFFFF'")
    p.add_argument("-d", "--detail", choices=list(DETAILS), default="medium",
                   help="low = lebih halus dan sederhana, high = lebih banyak detail "
                        "(default medium)")
    p.add_argument("--stacking", choices=["stacked", "cutout"], default="stacked",
                   help="stacked = bentuk bertumpuk, aman dari celah (default); "
                        "cutout = bentuk saling memotong, untuk cutting/engraving")
    p.add_argument("--remove-bg", nargs="?", const="tepi", choices=["tepi", "semua"],
                   help="buat latar transparan (warna yang menguasai pinggir gambar). "
                        "tepi (default) = hanya area yang tersambung ke pinggir; "
                        "semua = juga area berwarna sama di dalam objek, mis. lubang huruf O")
    p.add_argument("--gradasi", action="store_true",
                   help="eksperimental: isi area bergradasi (shading halus, bayangan lembut) "
                        "dengan gradasi SVG, bukan pita-pita warna rata")
    p.add_argument("--cepat", action="store_true",
                   help="sekitar 3× lebih cepat dengan bentuk sedikit kurang teliti "
                        "(resolusi kerja 2000 px, bukan 4000 px)")
    p.add_argument("-f", "--format", default="svg",
                   help=f"format output, pisahkan dengan koma: {', '.join(OUTPUT_FORMATS)} "
                        "(default svg)")
    p.add_argument("--debug", action="store_true",
                   help="simpan juga gambar berlabel yang dilacak (*.debug.png)")
    p.add_argument("-q", "--quiet", action="store_true", help="tanpa laporan per file")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
        bad = [f for f in formats if f not in OUTPUT_FORMATS]
        if bad or not formats:
            raise ValueError(f"format tidak dikenal: {', '.join(bad) or '(kosong)'}")
        if args.colors is not None and not 1 <= args.colors <= 64:
            raise ValueError("--colors harus antara 1 dan 64")
        opts = Options(colors=args.colors,
                       palette=parse_palette(args.palette) if args.palette else None,
                       detail=args.detail, stacking=args.stacking, remove_bg=args.remove_bg,
                       precision="cepat" if args.cepat else "tinggi",
                       gradients=args.gradasi)
        files = collect_inputs(args.inputs)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not files:
        print("error: tidak ada gambar untuk diproses", file=sys.stderr)
        return 2

    many = len(files) > 1 or any(Path(i).is_dir() for i in args.inputs)
    failed = 0
    for src in files:
        start = time.time()
        try:
            rgb, alpha = load_image(src)
            result = vectorize(rgb, alpha, opts)
            target = output_path(src, args.output, many)
            written = write_outputs(result, target, formats)
            if args.debug:
                result.debug_image.save(target.with_suffix(".debug.png"))
        except Exception as e:  # lanjut ke file berikutnya
            failed += 1
            print(f"✗ {src}: {e}", file=sys.stderr)
            continue
        if args.quiet:
            continue
        w, h = result.size
        ww, wh = result.work_size
        print(f"✓ {src} → {', '.join(str(p) for p in written)}")
        print(f"  ukuran {w}×{h}, diproses {ww}×{wh}")
        colors = " ".join(f"{c} {s * 100:.1f}%" for c, s in zip(result.palette, result.shares,
                                                                strict=True))
        note = ""
        if opts.colors and result.found_colors > opts.colors:
            note = f" (disederhanakan dari {result.found_colors})"
        elif opts.colors and result.found_colors < opts.colors:
            note = f" (hanya ditemukan {result.found_colors})"
        print(f"  palet {len(result.palette)} warna{note}: {colors}")
        if result.gradients:
            print(f"  {result.gradients} area diisi gradasi")
        if result.removed_bg:
            print(f"  latar {result.removed_bg} dihapus")
        line = f"  {result.paths} path · {len(result.svg.encode()) / 1024:.0f} KB"
        sim = similarity(result, rgb, alpha)
        if sim:
            line += f" · PSNR {sim[0]:.1f} dB · ΔE rata-rata {sim[1]:.1f}"
        print(line + f" · {time.time() - start:.1f} s")
    if failed:
        print(f"{failed} dari {len(files)} file gagal", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
