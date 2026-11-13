"""Test Helonoia Vectorizer. Jalankan dari root repo: python3 -m pytest vectorizer/tests -q"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import samples  # noqa: E402
import vectorize as v  # noqa: E402

REPO = HERE.parent.parent
LOGO = REPO / "helonoia" / "helonoia_logo.png"
LOGO_COLORS = {"#120B1E", "#B26BFF", "#F4EFFF", "#CDA6FF", "#C6FF3D", "#9A57F0", "#7C3FD6",
               "#0B0712"}


def run(image, **opts):
    rgba = np.asarray(image.convert("RGBA"))
    rgb, alpha = np.ascontiguousarray(rgba[..., :3]), np.ascontiguousarray(rgba[..., 3])
    return v.vectorize(rgb, alpha, v.Options(**opts)), rgb, alpha


def de(a: str, b: str) -> float:
    la = v.to_lab(np.array(v.hex_to_rgb(a), np.uint8))
    lb = v.to_lab(np.array(v.hex_to_rgb(b), np.uint8))
    return float(np.linalg.norm(la - lb))


def fills(svg: str) -> set[str]:
    root = ET.fromstring(svg.split("-->", 1)[1])
    return {el.get("fill") for el in root.iter(f"{{{v.SVG_NS}}}path")}


def matched(found: list[str], expected: list[str], tol: float) -> list[str]:
    """Warna `expected` yang punya pasangan di `found` dengan jarak < tol."""
    return [e for e in expected if min(de(e, f) for f in found) < tol]


# --- Gambar bersih -----------------------------------------------------------


def test_badge_png_finds_exact_palette():
    result, rgb, alpha = run(samples.badge(400))
    assert len(result.palette) == len(samples.BADGE_COLORS)
    assert matched(result.palette, samples.BADGE_COLORS, 2) == samples.BADGE_COLORS
    assert fills(result.svg) <= set(result.palette)
    psnr, mean_de = v.similarity(result, rgb, alpha)
    assert psnr > 30 and mean_de < 1.5


def test_svg_keeps_original_size():
    result, _, _ = run(samples.badge(400))
    root = ET.fromstring(result.svg.split("-->", 1)[1])
    assert (root.get("width"), root.get("height")) == ("400", "400")
    assert root.get("viewBox") == f"0 0 {result.work_size[0]} {result.work_size[1]}"


def test_small_distinct_accent_color_is_kept():
    image = samples.accent(600)
    pink = np.asarray(image).reshape(-1, 3)
    share = (np.abs(pink.astype(int) - v.hex_to_rgb(samples.ACCENT_COLORS[3])).sum(1) < 30).mean()
    assert share < 0.001  # memang sangat kecil
    result, rgb, alpha = run(image)
    assert matched(result.palette, samples.ACCENT_COLORS, 3) == samples.ACCENT_COLORS
    assert len(result.palette) == len(samples.ACCENT_COLORS)


def test_lineart_keeps_thin_lines():
    result, rgb, alpha = run(samples.lineart(400))
    assert len(result.palette) == 2
    dark = min(result.palette, key=lambda c: sum(v.hex_to_rgb(c)))
    assert de(dark, samples.LINEART_COLORS[1]) < 12
    assert v.similarity(result, rgb, alpha)[0] > 30


@pytest.mark.skipif(not LOGO.exists(), reason="logo Helonoia tidak ada")
def test_helonoia_logo_exact_brand_colors():
    rgb, alpha = v.load_image(LOGO)
    result = v.vectorize(rgb, alpha, v.Options())
    assert set(result.palette) == LOGO_COLORS
    assert v.similarity(result, rgb, alpha)[0] > 32


# --- Gambar kotor (JPEG kecil) -----------------------------------------------


def test_badge_jpeg_ignores_compression_artifacts():
    dirty = samples.as_jpeg(samples.badge(600), 300, 50)
    result, rgb, alpha = run(dirty)
    # Garis tepi 1,5 px rusak oleh JPEG; empat warna besar harus tetap tepat.
    assert matched(result.palette, samples.BADGE_COLORS[:4], 5) == samples.BADGE_COLORS[:4]
    assert len(result.palette) <= 6
    assert result.paths < 40


def test_colors_drops_jpeg_artifact_first():
    dirty = samples.as_jpeg(samples.badge(600), 300, 50)
    result, _, _ = run(dirty, colors=5)
    assert len(result.palette) == 5
    assert result.found_colors == 6
    assert matched(result.palette, samples.BADGE_COLORS[:4], 5) == samples.BADGE_COLORS[:4]


def test_colors_keeps_large_and_distinct_colors():
    # Garis tepi tipis (2,5% area) dibuang lebih dulu daripada bidang besar.
    result, _, _ = run(samples.badge(400), colors=4)
    assert matched(result.palette, samples.BADGE_COLORS[:4], 2) == samples.BADGE_COLORS[:4]


@pytest.mark.skipif(not LOGO.exists(), reason="logo Helonoia tidak ada")
def test_colors_keeps_small_but_distinct_color():
    # Lime hanya 1,3% area tapi sangat berbeda; lilac 2,3% tapi mirip ungu.
    rgb, alpha = v.load_image(LOGO)
    result = v.vectorize(rgb, alpha, v.Options(colors=4))
    assert set(result.palette) == {"#120B1E", "#B26BFF", "#F4EFFF", "#C6FF3D"}


def test_colors_more_than_found_keeps_all():
    result, _, _ = run(samples.badge(300), colors=9)
    assert len(result.palette) == result.found_colors == 5


def test_cli_reports_simplification(tmp_path, capsys):
    src = tmp_path / "logo.png"
    samples.badge(200).save(src)
    assert v.main([str(src), "-c", "3"]) == 0
    assert "palet 3 warna (disederhanakan dari 5)" in capsys.readouterr().out


def test_lineart_jpeg():
    dirty = samples.as_jpeg(samples.lineart(600), 400, 60)
    result, rgb, alpha = run(dirty)
    assert len(result.palette) == 2
    assert v.similarity(result, rgb, alpha)[0] > 30


# --- Opsi --------------------------------------------------------------------


def test_palette_lock_uses_only_given_colors():
    palette = ["#000000", "#FFFFFF", "#FF0000"]
    result, _, _ = run(samples.badge(300), palette=palette)
    assert set(result.palette) <= set(palette)
    assert fills(result.svg) <= set(palette)


def test_remove_bg_keeps_inner_areas():
    result, _, _ = run(samples.badge(400), remove_bg="tepi")
    assert result.removed_bg == "#FFFFFF"
    # Teks putih di dalam persegi biru tidak tersambung ke pinggir, jadi tetap ada.
    assert "#FFFFFF" in result.palette
    out = v.render(result.svg, result.size)
    assert out[2, 2, 3] == 0 and out[200, 200, 3] == 255


def test_remove_bg_all_removes_inner_areas_too():
    result, _, _ = run(samples.badge(400), remove_bg="semua")
    assert result.removed_bg == "#FFFFFF"
    assert "#FFFFFF" not in result.palette


def test_cli_remove_bg_flag_default(tmp_path):
    src = tmp_path / "logo.png"
    samples.badge(200).save(src)
    assert v.build_parser().parse_args([str(src), "--remove-bg"]).remove_bg == "tepi"
    assert v.main([str(src), "--remove-bg", "-q"]) == 0


def test_transparent_input_stays_transparent():
    result, rgb, alpha = run(samples.badge(400, transparent=True))
    out = v.render(result.svg, result.size)
    assert out[2, 2, 3] == 0
    assert matched(result.palette, samples.BADGE_COLORS, 3) == samples.BADGE_COLORS
    assert v.similarity(result, rgb, alpha)[0] > 30


def test_stacking_cutout():
    result, _, _ = run(samples.badge(300), stacking="cutout")
    assert result.paths > 0


@pytest.mark.parametrize("detail", ["low", "high"])
def test_detail_levels(detail):
    result, rgb, alpha = run(samples.badge(300), detail=detail)
    assert v.similarity(result, rgb, alpha)[0] > 27


def test_16bit_grayscale_png(tmp_path):
    gray = np.asarray(samples.badge(200).convert("L")).astype(np.uint16) * 257
    path = tmp_path / "abu16.png"
    from PIL import Image
    Image.fromarray(gray).save(path)
    rgb, alpha = v.load_image(path)
    assert abs(int(rgb[100, 100, 0]) - int(gray[100, 100] // 257)) <= 1
    assert len(v.vectorize(rgb, alpha, v.Options()).palette) >= 3


def test_fast_mode_same_palette_and_keeps_thin_outline():
    image = samples.badge(400)
    fast, rgb, alpha = run(image, precision="cepat")
    full, _, _ = run(image)
    assert fast.palette == full.palette
    assert fast.work_size[0] < full.work_size[0]
    # Garis tepi hijau 3 px tidak boleh tertutup kurva lingkaran merah.
    assert v.similarity(fast, rgb, alpha)[0] > 33


def test_fully_transparent_image_fails_cleanly():
    from PIL import Image
    with pytest.raises(ValueError):
        run(Image.new("RGBA", (50, 50), (0, 0, 0, 0)))


# --- Fungsi kecil ------------------------------------------------------------


def test_hex_parsing():
    assert v.hex_to_rgb("#fff") == (255, 255, 255)
    assert v.rgb_to_hex((178, 107, 255)) == "#B26BFF"
    assert v.parse_palette("helonoia") == v.PALETTES["helonoia"]
    assert v.parse_palette("#000, #ffffff") == ["#000000", "#FFFFFF"]
    with pytest.raises(ValueError):
        v.hex_to_rgb("#12345")


def test_blend_distance():
    colors = np.array([[0, 0, 0], [255, 255, 255]], np.float32)
    d = v.blend_distance(np.array([[128, 128, 128], [255, 0, 0]], np.float32), colors)
    assert d[0] < 1 and d[1] > 100


# --- CLI ---------------------------------------------------------------------


def test_cli_folder_and_formats(tmp_path):
    src = tmp_path / "masuk"
    src.mkdir()
    samples.badge(200).save(src / "a.png")
    samples.as_jpeg(samples.lineart(400), 200, 70).save(src / "b.jpg")
    out = tmp_path / "keluar"
    code = v.main([str(src), "-o", str(out), "-f", "svg,pdf", "--debug", "-q"])
    assert code == 0
    for name in ("a", "b"):
        assert (out / f"{name}.svg").stat().st_size > 0
        assert (out / f"{name}.pdf").read_bytes().startswith(b"%PDF")
        assert (out / f"{name}.debug.png").exists()


def test_cli_single_file_output_name(tmp_path):
    src = tmp_path / "logo.png"
    samples.badge(200).save(src)
    target = tmp_path / "hasil.svg"
    assert v.main([str(src), "-o", str(target), "-q"]) == 0
    assert target.exists()


def test_cli_errors(tmp_path):
    assert v.main([str(tmp_path / "tidak-ada.png")]) == 2
    assert v.main([str(tmp_path), "-f", "gif"]) == 2
    broken = tmp_path / "rusak.png"
    broken.write_bytes(b"bukan gambar")
    assert v.main([str(broken), "-q"]) == 1
