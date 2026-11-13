"""
HELONOIA – generator gambar vektor (SVG)
========================================

Membuat gambar siap pakai (post Instagram, story, OG image, banner, ikon aplikasi)
dari aset brand: maskot, tulisan HELONOIA, palet warna, dan judul bebas.
Semua hasil berupa SVG vektor murni. Tidak butuh library tambahan: cukup Python 3.

Contoh:

    python3 generate.py                                   # semua format, tanpa judul
    python3 generate.py -f og -j "Halo, kami Helonoia"    # satu format + judul
    python3 generate.py -f persegi -j "Undangan digital" -s "Kecil tapi pasti" -l terang
    python3 generate.py --ukuran 1600x900 -j "Ukuran bebas" -o hasil/custom.svg
    python3 generate.py -f story --png                    # + PNG (perlu `pip install cairosvg`)

Format bawaan (lihat FORMAT di bawah): persegi, potret, story, og, banner, ikon.
Latar: gelap (#120B1E), terang (#F4EFFF), ungu (#7C3FD6), transparan.

Judul dan subjudul ditulis sebagai <text> dengan font Fredoka / Plus Jakarta Sans,
jadi tampil benar bila font itu terpasang (atau dibuka di browser yang memuatnya).
Supaya teks tampil sama di mana saja, ubah teks menjadi path dengan memberi file font:

    pip install fonttools
    python3 generate.py -f og -j "Halo" --font Fredoka.ttf

Tulisan HELONOIA di logo selalu berupa path, jadi tidak butuh font.
"""

import argparse
import math
import os
import random
import sys
from xml.sax.saxutils import escape

import helonoia_monster as hm

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Format bawaan: nama -> (lebar, tinggi, keterangan)
# ---------------------------------------------------------------------------
FORMAT = {
    "persegi": (1080, 1080, "Post Instagram / feed 1:1"),
    "potret":  (1080, 1350, "Post Instagram 4:5"),
    "story":   (1080, 1920, "Story / Reels / status WhatsApp 9:16"),
    "og":      (1200, 630,  "Pratinjau tautan (og:image)"),
    "banner":  (1500, 500,  "Header X / Twitter, banner web"),
    "ikon":    (512, 512,   "Ikon aplikasi / foto profil (hanya maskot)"),
}

# Warna per latar: (latar, judul, subjudul, warna "HELO", warna "NOIA", dekor utama, kilau)
TEMA = {
    "gelap":      (hm.BG,    hm.WHITE, hm.BELLY, hm.WHITE, hm.VIO,   hm.VIO,   hm.LIME),
    "terang":     (hm.WHITE, hm.BG,    hm.DEEP,  hm.BG,    hm.DEEP,  hm.BELLY, hm.VIO),
    "ungu":       (hm.DEEP,  hm.WHITE, hm.BELLY, hm.WHITE, hm.LIME,  hm.VIO,   hm.LIME),
    "transparan": (None,     hm.WHITE, hm.BELLY, hm.WHITE, hm.VIO,   None,     None),
}

FONT_JUDUL = "Fredoka, 'Plus Jakarta Sans', 'Arial Rounded MT Bold', sans-serif"
FONT_SUB = "'Plus Jakarta Sans', Fredoka, Arial, sans-serif"
LEBAR_HURUF = 0.56       # perkiraan lebar rata-rata satu huruf judul (x ukuran font), untuk memotong baris
LEBAR_HURUF_SUB = 0.50   # idem untuk subjudul (Plus Jakarta Sans lebih ramping)


# ---------------------------------------------------------------------------
# Komponen
# ---------------------------------------------------------------------------
def maskot(x, y, w):
    """Maskot dalam kotak persegi w x w dengan pojok kiri atas (x, y)."""
    return (f'<svg x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{w:.1f}" '
            f'viewBox="{hm.VIEWBOX}">{hm.build_monster()}</svg>')


def lebar_logo(size):
    """Lebar tulisan HELONOIA pada ukuran font `size`."""
    k = size / 1000
    return sum(hm.GLYPHS[c][0] for c in "HELONOIA") * k + hm.WORD_TRACK * size * 7


def logo_teks(x, baseline, size, helo, noia, anchor="start"):
    """Tulisan HELONOIA (path) mulai di x, atau berpusat di x bila anchor='middle'."""
    k = size / 1000
    gap = hm.WORD_TRACK * size
    if anchor == "middle":
        x -= lebar_logo(size) / 2
    out = ""
    for i, ch in enumerate("HELONOIA"):
        adv, d = hm.GLYPHS[ch]
        out += (f'<path transform="translate({x:.2f} {baseline:.2f}) scale({k:.4f} {-k:.4f})" '
                f'd="{d}" fill="{helo if i < 4 else noia}"/>')
        x += adv * k + gap
    return out


def potong_baris(teks, size, maks, lebar_huruf=LEBAR_HURUF):
    """Pecah teks menjadi beberapa baris supaya tiap baris muat di lebar `maks`."""
    per_baris = max(4, int(maks / (size * lebar_huruf)))

    def susun(batas):
        baris, kini = [], ""
        for kata in teks.split():
            coba = f"{kini} {kata}".strip()
            if len(coba) <= batas or not kini:
                kini = coba
            else:
                baris.append(kini)
                kini = kata
        if kini:
            baris.append(kini)
        return baris

    # cari batas terkecil yang tetap menghasilkan jumlah baris yang sama -> baris seimbang,
    # tidak ada satu kata yatim di baris terakhir
    baris = susun(per_baris)
    batas = per_baris
    while batas > 4 and len(susun(batas - 1)) == len(baris):
        batas -= 1
    return susun(batas)


class Tulisan:
    """Menulis teks sebagai <text>, atau sebagai path bila diberi file font (perlu fonttools)."""

    def __init__(self, font_path=None, berat=600):
        self.font = None
        if not font_path:
            return
        try:
            from fontTools.ttLib import TTFont
        except ImportError:
            sys.exit("--font butuh fonttools: pip install fonttools")
        font = TTFont(font_path)
        if "fvar" in font:   # font variabel (mis. Fredoka dari Google Fonts) -> pilih ketebalan
            from fontTools.varLib.instancer import instantiateVariableFont
            sumbu = {a.axisTag: a for a in font["fvar"].axes}
            if "wght" in sumbu:
                w = min(max(berat, sumbu["wght"].minValue), sumbu["wght"].maxValue)
                font = instantiateVariableFont(font, {"wght": w})
        self.font = font
        self.glyphs = font.getGlyphSet()
        self.cmap = font.getBestCmap()
        self.upm = font["head"].unitsPerEm

    def lebar(self, teks, size):
        if not self.font:
            return len(teks) * size * LEBAR_HURUF
        hmtx = self.font["hmtx"]
        return sum(hmtx[self.cmap.get(ord(c), ".notdef")][0] for c in teks) * size / self.upm

    def tulis(self, teks, x, baseline, size, warna, anchor="start", keluarga=FONT_JUDUL, berat=600):
        if not self.font:
            return (f'<text x="{x:.1f}" y="{baseline:.1f}" font-family="{keluarga}" '
                    f'font-size="{size:.1f}" font-weight="{berat}" fill="{warna}" '
                    f'text-anchor="{anchor}">{escape(teks)}</text>')
        from fontTools.pens.svgPathPen import SVGPathPen
        k = size / self.upm
        if anchor == "middle":
            x -= self.lebar(teks, size) / 2
        out = ""
        for c in teks:
            nama = self.cmap.get(ord(c), ".notdef")
            pen = SVGPathPen(self.glyphs)
            self.glyphs[nama].draw(pen)
            d = pen.getCommands()
            if d:
                out += (f'<path transform="translate({x:.2f} {baseline:.2f}) scale({k:.4f} {-k:.4f})" '
                        f'd="{d}" fill="{warna}"/>')
            x += self.font["hmtx"][nama][0] * k
        return out


def kilau(cx, cy, r, warna):
    """Bintang kilau 4 sudut."""
    q = r * 0.22
    return (f'<path d="M {cx:.1f} {cy-r:.1f} Q {cx+q:.1f} {cy-q:.1f} {cx+r:.1f} {cy:.1f} '
            f'Q {cx+q:.1f} {cy+q:.1f} {cx:.1f} {cy+r:.1f} Q {cx-q:.1f} {cy+q:.1f} {cx-r:.1f} {cy:.1f} '
            f'Q {cx-q:.1f} {cy-q:.1f} {cx:.1f} {cy-r:.1f} Z" fill="{warna}"/>')


def dekor(W, H, warna, c_kilau, seed, hindari):
    """Hiasan latar: bulatan lembut, grid titik, dan kilau.
    `hindari` = daftar kotak (x, y, w, h) yang tidak boleh ditimpa kilau."""
    rng = random.Random(seed)
    u = min(W, H)
    out = f'<g opacity="0.18" fill="{warna}">'
    for cx, cy, r in ((W * 0.92, H * 0.08, u * 0.42), (W * 0.04, H * 0.96, u * 0.30)):
        out += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'
    out += "</g>"
    # grid titik di pojok kiri atas
    jarak = u * 0.045
    rt = u * 0.006

    def kena(x, y, r):
        return any(bx - r < x < bx + bw + r and by - r < y < by + bh + r for bx, by, bw, bh in hindari)

    out += f'<g fill="{warna}" opacity="0.35">'
    for i in range(5):
        for j in range(5):
            x, y = u * 0.05 + i * jarak, u * 0.05 + j * jarak
            if not kena(x, y, jarak * 0.6):
                out += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rt:.1f}"/>'
    out += "</g>"
    # kilau lime di tempat kosong
    dipasang, coba = 0, 0
    while dipasang < 5 and coba < 200:
        coba += 1
        x, y = rng.uniform(0.05, 0.95) * W, rng.uniform(0.05, 0.95) * H
        r = rng.uniform(0.012, 0.028) * u
        if kena(x, y, r * 2):
            continue
        out += kilau(x, y, r, c_kilau)
        dipasang += 1
    return out


# ---------------------------------------------------------------------------
# Tata letak
# ---------------------------------------------------------------------------
def buat(W, H, judul="", sub="", latar="gelap", pakai_maskot=True, pakai_logo=True,
         pakai_dekor=True, seed=7, tulisan=None, hanya_maskot=False):
    tulisan = tulisan or Tulisan()
    bg, c_judul, c_sub, helo, noia, c_dekor, c_kilau = TEMA[latar]
    u = min(W, H)
    pad = u * 0.08
    isi, kotak = "", []

    if hanya_maskot:
        # ikon: maskot di tengah, latar persegi membulat
        m = u * 0.86
        isi = maskot((W - m) / 2, (H - m) / 2 + u * 0.02, m)
        latar_svg = (f'<rect width="{W}" height="{H}" rx="{u*0.22:.1f}" fill="{bg}"/>' if bg else "")
        return bungkus(W, H, latar_svg + isi)

    horizontal = W / H > 1.4
    if horizontal:
        # teks di kiri, maskot di kanan
        m = H * 0.92 if pakai_maskot else 0
        mx = W - m - pad * 0.3
        if pakai_maskot:
            isi += maskot(mx, (H - m) / 2 + H * 0.03, m)
            kotak.append((mx, 0, m, H))
        kolom = (mx if pakai_maskot else W - pad) - pad * 1.5
        ukuran_logo = min(kolom / 5.2, H * 0.16)
        ukuran_judul = min(H * 0.13, ukuran_logo * 1.05)
        ukuran_sub = ukuran_judul * 0.5
        baris_j = potong_baris(judul, ukuran_judul, kolom) if judul else []
        baris_s = potong_baris(sub, ukuran_sub, kolom, LEBAR_HURUF_SUB) if sub else []
        tinggi = ((ukuran_logo * 0.72 if pakai_logo else 0)
                  + (ukuran_logo * 0.55 if pakai_logo and (baris_j or baris_s) else 0)
                  + len(baris_j) * ukuran_judul * 1.15
                  + (ukuran_sub * 0.6 if baris_s else 0)
                  + len(baris_s) * ukuran_sub * 1.35)
        y = (H - tinggi) / 2
        x = pad
        kotak.append((x, y, kolom, tinggi))
        anchor = "start"
    else:
        # bertumpuk: maskot, logo, judul, subjudul – rata tengah
        kolom = W - pad * 2
        tinggi_rasio = min(max(H / W, 1), 1.4)   # format tinggi (story) -> teks lebih besar
        ukuran_logo = min(kolom / 5.2 * 0.8, u * 0.11 * tinggi_rasio)
        ukuran_judul = ukuran_logo * 0.68
        ukuran_sub = ukuran_judul * 0.6
        baris_j = potong_baris(judul, ukuran_judul, kolom) if judul else []
        baris_s = potong_baris(sub, ukuran_sub, kolom, LEBAR_HURUF_SUB) if sub else []
        teks_h = ((ukuran_logo * 0.72 if pakai_logo else 0)
                  + (ukuran_logo * 0.6 if pakai_logo and (baris_j or baris_s) else 0)
                  + len(baris_j) * ukuran_judul * 1.15
                  + (ukuran_sub * 0.6 if baris_s else 0)
                  + len(baris_s) * ukuran_sub * 1.35)
        sisa = H - pad * 2 - teks_h
        m = min(kolom * (0.85 + 0.15 * (tinggi_rasio - 1) / 0.4), sisa * 0.95) if pakai_maskot else 0
        jeda = ukuran_logo * 0.35 if pakai_maskot and teks_h else 0
        y = (H - (m + jeda + teks_h)) / 2
        if pakai_maskot:
            isi += maskot((W - m) / 2, y, m)
            kotak.append(((W - m) / 2, y, m, m))
            y += m + jeda
        x = W / 2
        kotak.append((pad, y, kolom, teks_h))
        anchor = "middle"

    if pakai_logo:
        y += ukuran_logo * 0.72
        isi += logo_teks(x, y, ukuran_logo, helo, noia, anchor)
        if baris_j or baris_s:
            y += ukuran_logo * 0.6
    for b in baris_j:
        y += ukuran_judul * 0.95
        isi += tulisan.tulis(b, x, y, ukuran_judul, c_judul, anchor)
        y += ukuran_judul * 0.2
    if baris_s:
        y += ukuran_sub * 0.6
    for b in baris_s:
        y += ukuran_sub * 1.1
        isi += tulisan.tulis(b, x, y, ukuran_sub, c_sub, anchor, FONT_SUB, 500)
        y += ukuran_sub * 0.25

    latar_svg = f'<rect width="{W}" height="{H}" fill="{bg}"/>' if bg else ""
    hias = dekor(W, H, c_dekor, c_kilau, seed, kotak) if pakai_dekor and c_dekor else ""
    return bungkus(W, H, latar_svg + hias + isi)


def bungkus(W, H, isi):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}">{isi}</svg>\n')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def simpan(path, svg_teks, png=False, W=None, H=None):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_teks)
    print(f"Tersimpan: {path}")
    if png:
        try:
            import cairosvg
        except ImportError:
            print("  (PNG dilewati – pasang `cairosvg` jika ingin ekspor PNG)")
            return
        p = os.path.splitext(path)[0] + ".png"
        cairosvg.svg2png(bytestring=svg_teks.encode(), write_to=p, output_width=W, output_height=H)
        print(f"Tersimpan: {p}")


def main(argv=None):
    daftar = "\n".join(f"  {k:<8} {w} x {h}  {d}" for k, (w, h, d) in FORMAT.items())
    ap = argparse.ArgumentParser(
        description="Generator gambar vektor (SVG) brand Helonoia.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Format:\n" + daftar)
    ap.add_argument("-f", "--format", choices=FORMAT, action="append",
                    help="format gambar (boleh diulang). Tanpa -f dan --ukuran: semua format.")
    ap.add_argument("--ukuran", metavar="LxT", help="ukuran bebas, mis. 1600x900")
    ap.add_argument("-j", "--judul", default="", help="judul utama")
    ap.add_argument("-s", "--sub", default="", help="subjudul / keterangan")
    ap.add_argument("-l", "--latar", choices=TEMA, default="gelap", help="warna latar (bawaan: gelap)")
    ap.add_argument("-o", "--out", help="file keluaran (hanya untuk satu gambar). Bawaan: hasil/<format>.svg")
    ap.add_argument("--tanpa-maskot", action="store_true", help="jangan gambar maskot")
    ap.add_argument("--tanpa-logo", action="store_true", help="jangan tulis HELONOIA")
    ap.add_argument("--tanpa-dekor", action="store_true", help="tanpa hiasan latar")
    ap.add_argument("--seed", type=int, default=7, help="acak posisi kilau (bawaan: 7)")
    ap.add_argument("--font", help="file .ttf/.otf untuk mengubah judul menjadi path (perlu fonttools)")
    ap.add_argument("--png", action="store_true", help="ekspor PNG juga (perlu cairosvg)")
    a = ap.parse_args(argv)

    tugas = []
    if a.ukuran:
        try:
            w, h = (int(v) for v in a.ukuran.lower().split("x"))
        except ValueError:
            ap.error("--ukuran harus berbentuk LEBARxTINGGI, mis. 1600x900")
        tugas.append((f"{w}x{h}", w, h))
    for nama in a.format or ([] if a.ukuran else FORMAT):
        tugas.append((nama, *FORMAT[nama][:2]))
    if a.out and len(tugas) > 1:
        ap.error("-o hanya bisa dipakai untuk satu gambar; pilih satu -f atau --ukuran")

    tulisan = Tulisan(a.font)
    for nama, w, h in tugas:
        svg_teks = buat(w, h, a.judul, a.sub, a.latar,
                        pakai_maskot=not a.tanpa_maskot, pakai_logo=not a.tanpa_logo,
                        pakai_dekor=not a.tanpa_dekor, seed=a.seed, tulisan=tulisan,
                        hanya_maskot=(nama == "ikon"))
        akhiran = "" if a.latar == "gelap" else f"_{a.latar}"
        out = a.out or os.path.join(HERE, "hasil", f"{nama}{akhiran}.svg")
        simpan(out, svg_teks, a.png, w, h)


if __name__ == "__main__":
    main()
