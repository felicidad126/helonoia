"""
HELONOIA – generator karakter "Noia" dengan pose & ekspresi
===========================================================

Menyusun karakter Noia sebagai SVG vektor murni dari bagian-bagian tubuh yang dijiplak
dari gambar sumber (sumber/noia.webp -> noia_bagian.json, lihat jiplak_noia.py).
Pose "siaga" dengan ekspresi "galak" sama dengan gambar sumber; pose lain dibuat dengan
memutar kepala, lengan, kaki, dan ekor di sendinya, dan ekspresi lain digambar di atas
kepala yang wajahnya dikosongkan. Cukup Python 3, tanpa library tambahan.

    python3 helonoia_karakter.py                      # semua pose + lembar pose & ekspresi
    python3 helonoia_karakter.py -p siaga -e galak    # satu kombinasi
    python3 helonoia_karakter.py -e kaget             # kepala saja
    python3 helonoia_karakter.py --semua              # semua kombinasi pose x ekspresi
    python3 helonoia_karakter.py --daftar             # daftar pose & ekspresi
    python3 helonoia_karakter.py --png                # + PNG (perlu `pip install cairosvg`)

Hasil (bawaan) di folder karakter/.

Susunan script
--------------
1. Data bagian      path hasil jiplakan + titik sendi
2. Kanvas           penampung SVG + batas gambar
3. Wajah            mata, alis, mulut, efek (untuk ekspresi selain bawaan sumber)
4. EKSPRESI, POSE   data: tinggal tambah entri baru
5. Perakitan        gambar(pose, ekspresi)
6. Lembar & CLI

Satuan koordinat = piksel gambar sumber (1536 x 1024).
"""

import argparse
import json
import math
import os
import re

DI_SINI = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 1. Data bagian
# ---------------------------------------------------------------------------
with open(os.path.join(DI_SINI, "noia_bagian.json")) as _f:
    _DATA = json.load(_f)
BAGIAN = _DATA["bagian"]
URUTAN = _DATA["urutan"]          # dari belakang ke depan

INK    = "#0A0212"   # garis
VIO    = BAGIAN["kepala"]["dasar"]   # warna kulit kepala (untuk kelopak mata)
VIO_SH = "#6C24C5"   # alas badan (terlihat kalau lengan/kepala bergeser)
LIME   = "#DAF45A"
WHITE  = "#FFFFFF"
MOUTH  = "#3B1258"
TONGUE = "#FF7FB0"
BLUSH  = "#FF7FB0"
TEAR   = "#8FD8FF"
OL = 6.0             # tebal garis untuk bentuk tambahan (efek, alas)

# Titik putar tiap bagian (koordinat sumber)
SENDI = {
    "kepala": (720, 500),      # leher
    "lengan_n": (838, 515),    # bahu kanan layar (pusat potongan lingkaran di jiplak_noia.py)
    "lengan_k": (612, 558),    # bahu kiri layar
    "kaki_k": (640, 770),      # pinggul kiri layar
    "ekor": (880, 690),        # pangkal ekor
}
PUSAT = (730, 600)             # titik putar seluruh badan
# Alas badan: bidang gelap di bawah leher & bahu supaya tidak bolong saat bagian diputar
ALAS = "M 640 500 C 700 470 800 470 850 500 C 880 540 860 610 800 630 C 740 640 660 630 640 590 Z"


# ---------------------------------------------------------------------------
# 2. Kanvas
# ---------------------------------------------------------------------------
def putar(p, deg, pusat):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    x, y = p[0] - pusat[0], p[1] - pusat[1]
    return (pusat[0] + x * c - y * s, pusat[1] + x * s + y * c)


def ubah_path(d, f):
    """Terapkan fungsi titik f((x, y)) -> (x, y) ke semua koordinat path (perintah absolut M L C Q Z)."""
    out, x = [], None
    for tok in re.findall(r"[MLCQZ]|-?\d+\.?\d*", d):
        if tok in "MLCQZ":
            out.append(tok)
        elif x is None:
            x = float(tok)
        else:
            out.append("%.1f %.1f" % f((x, float(tok))))
            x = None
    return " ".join(out)


def bulat(cx, cy, rx, ry=None, n=40):
    ry = ry or rx
    return "M " + " L ".join("%.1f %.1f" % (cx + rx * math.cos(2 * math.pi * i / n),
                                           cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)) + " Z"


def gores(d, w=6, warna=INK, fill="none"):
    return (f'<path d="{d}" fill="{fill}" stroke="{warna}" stroke-width="{w:.1f}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


class Kanvas:
    _seri = 0   # awalan id clip unik, supaya beberapa gambar aman digabung dalam satu lembar

    def __init__(self):
        Kanvas._seri += 1
        self.awalan = f"c{Kanvas._seri}_"
        self.out, self.defs, self.nid = [], [], 0
        self.box = [1e9, 1e9, -1e9, -1e9]

    def lacak(self, d, f=None):
        """Perluas batas gambar dengan titik-titik path `d` (f = transformasi titik)."""
        v = [float(x) for x in re.findall(r"-?\d+\.?\d*", d)]
        b = self.box
        for i in range(0, len(v) - 1, 2):
            x, y = f((v[i], v[i + 1])) if f else (v[i], v[i + 1])
            b[0], b[1], b[2], b[3] = min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)

    def clip(self, d):
        self.nid += 1
        cid = f"{self.awalan}{self.nid}"
        self.defs.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        return cid

    def tambah(self, svg, lacak=None, f=None):
        if lacak:
            self.lacak(lacak, f)
        self.out.append(svg)

    def bingkai(self, pad=24):
        x0, y0, x1, y1 = self.box
        s = max(x1 - x0, y1 - y0) + 2 * pad
        return ((x0 + x1 - s) / 2, (y0 + y1 - s) / 2, s)

    def isi(self):
        return f'<defs>{"".join(self.defs)}</defs>{"".join(self.out)}'

    def svg(self, ukuran=1000):
        x, y, s = self.bingkai()
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.1f} {y:.1f} {s:.1f} {s:.1f}" '
                f'width="{ukuran}" height="{ukuran}">{self.isi()}</svg>\n')


def svg_bagian(nama):
    """Satu bagian hasil jiplakan: siluet berwarna dasar, area warna lain, lalu garis tinta."""
    b = BAGIAN[nama]
    return (f'<path d="{b["siluet"]}" fill="{b["dasar"]}"/>'
            + "".join(f'<path d="{d}" fill="{w}" fill-rule="evenodd"/>' for w, d in b["lapis"])
            + f'<path d="{b["tinta"]}" fill="{INK}" fill-rule="evenodd"/>')


# ---------------------------------------------------------------------------
# 3. Wajah (untuk ekspresi yang bukan bawaan sumber) – koordinat sumber
# ---------------------------------------------------------------------------
# Mata: (pusat, skala, cermin). Satuan lokal mata: bola mata 30 x 24, x positif = sisi luar
# wajah. Mata jauh (kiri layar) lebih kecil dan dicerminkan karena kepala menghadap 3/4.
MATA = (((560, 420), 1.75, -1), ((735, 388), 2.6, 1))
MULUT = (660, 474)
SKALA_MULUT = 2.0


def mata(K, cfg):
    jenis = cfg.get("bentuk", "buka")
    for (cx, cy), s, sx in MATA:
        def f(p):
            return (cx + p[0] * s * sx, cy + p[1] * s)

        def g(d, w=5.5):
            return gores(ubah_path(d, f), w * s)

        o = ""
        if jenis == "buka":
            rx, ry = cfg.get("rx", 30), cfg.get("ry", 24)
            bola = ubah_path(bulat(0, 0, rx, ry), f)
            cid = K.clip(bola)
            gx, gy = cfg.get("lirik", (0, 0))     # lirikan dalam arah layar
            pr = cfg.get("pupil", 12) * s
            px, py = cx + gx * s, cy + gy * s
            isi = (f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{pr:.1f}" fill="{INK}"/>'
                   f'<circle cx="{px - pr * 0.35:.1f}" cy="{py - pr * 0.4:.1f}" r="{pr * 0.3:.1f}" fill="{WHITE}"/>')
            if cfg.get("kilau"):
                isi += f'<circle cx="{px + pr * 0.4:.1f}" cy="{py + pr * 0.35:.1f}" r="{pr * 0.17:.1f}" fill="{WHITE}"/>'
            kelopak = ""
            if "kelopak" in cfg:
                # garis kelopak dari sisi dalam (x negatif) ke sisi luar; di atasnya tertutup kulit
                xi, xo = -rx - 8, rx + 8
                yi, yo = cfg["kelopak"]
                tutup = ubah_path(f"M {xi} {yi} L {xo} {yo} L {xo} -70 L {xi} -70 Z", f)
                isi += f'<path d="{tutup}" fill="{VIO}"/>'
                kelopak = g(f"M {xi + 4} {yi + (yo - yi) * 4 / (xo - xi):.1f} L {xo - 2} {yo}", 5)
            o = (f'<path d="{bola}" fill="{WHITE}"/><g clip-path="url(#{cid})">{isi}</g>'
                 + gores(bola, 2.3 * s) + kelopak)
        elif jenis == "senang":     # ^ ^
            o = g("M -24 8 Q 0 -22 24 8")
        elif jenis == "tidur":      # u u
            o = g("M -24 -4 Q 0 16 24 -4", 5) + g("M 24 -4 L 32 -9", 4)
        elif jenis == "tawa":       # > <
            o = g("M 20 -16 L -14 0 L 20 16")
        if cfg.get("alis"):
            (x0, y0), (x1, y1), (x2, y2) = cfg["alis"]
            o += g(f"M {x0} {y0} Q {x1} {y1} {x2} {y2}")
        K.tambah(o)


def mulut(K, jenis):
    """Mulut, ditulis dalam satuan kecil di sekitar (0, 0) lalu diperbesar ke titik MULUT."""
    k = SKALA_MULUT

    def f(p):
        return (MULUT[0] + p[0] * k, MULUT[1] + p[1] * k)

    def g(d, w=3.0):
        return gores(ubah_path(d, f), w * k)

    def gigi(x, y, w=7, h=9):
        d = f"M {x - w / 2} {y} L {x - w * 0.3} {y + h} L {x + w * 0.4} {y + h * 0.8} L {x + w / 2} {y} Z"
        return gores(ubah_path(d, f), 2.2 * k, INK, WHITE)

    if jenis == "seringai":
        o = g("M -24 -2 Q 0 12 26 -10") + gigi(14, -3, 8, 11)
    elif jenis in ("senyum", "tawa"):
        lb, dl = (26, 20) if jenis == "senyum" else (30, 24)
        d = ubah_path(f"M {-lb} -8 Q 0 -2 {lb} -8 Q {lb - 4} {dl} 0 {dl + 2} Q {-lb + 4} {dl} {-lb} -8 Z", f)
        lidah = ubah_path(bulat(3, dl, lb * 0.6, dl * 0.5), f)
        cid = K.clip(d)
        o = (f'<path d="{d}" fill="{MOUTH}"/><g clip-path="url(#{cid})"><path d="{lidah}" fill="{TONGUE}"/></g>'
             + gores(d, 2.8 * k) + gigi(-lb * 0.5, -6, 8, 10) + gigi(lb * 0.5, -6, 8, 10))
    elif jenis == "o":
        o = gores(ubah_path(bulat(0, 2, 10, 13), f), 2.8 * k, INK, MOUTH)
    elif jenis == "sedih":
        o = g("M -20 8 Q -9 -6 0 0 Q 9 -6 20 8")
    elif jenis == "kecil":
        o = g("M -8 0 Q 0 6 8 0")
    elif jenis == "malu":
        o = g("M -18 2 Q -12 -4 -6 2 Q 0 8 6 2 Q 12 -4 18 2")
    else:
        o = ""
    K.tambah(o)


def tetes(x, y, s, warna):
    d = (f"M {x} {y - 20 * s} C {x + 4 * s} {y - 10 * s} {x + 13 * s} {y} {x + 13 * s} {y + 8 * s} "
         f"C {x + 13 * s} {y + 16 * s} {x + 7 * s} {y + 21 * s} {x} {y + 21 * s} "
         f"C {x - 7 * s} {y + 21 * s} {x - 13 * s} {y + 16 * s} {x - 13 * s} {y + 8 * s} "
         f"C {x - 13 * s} {y} {x - 4 * s} {y - 10 * s} {x} {y - 20 * s} Z")
    return f'<path d="{d}" fill="{warna}" stroke="{INK}" stroke-width="{OL}"/>'


def efek_wajah(K, daftar):
    """Efek yang menempel di wajah (ikut miring bersama kepala)."""
    o = ""
    for e in daftar:
        if e == "merona":
            o += (f'<ellipse cx="552" cy="472" rx="28" ry="13" fill="{BLUSH}" opacity="0.7"/>'
                  f'<ellipse cx="790" cy="462" rx="40" ry="17" fill="{BLUSH}" opacity="0.7"/>')
        elif e == "keringat":
            o += tetes(585, 262, 1.9, WHITE)
        elif e == "air_mata":
            o += tetes(548, 492, 1.2, TEAR) + tetes(770, 482, 1.6, TEAR)
    K.tambah(o)


def efek_melayang(daftar):
    """Efek di sekitar kepala yang tidak ikut miring (huruf, tanda baca, hati).
    Mengembalikan (svg, path batas)."""
    o, kotak = "", ""
    for e in daftar:
        if e == "seru":
            x, y = 345, 90
            o += (f'<path d="M {x - 20} {y} L {x + 20} {y} L {x + 8} {y + 100} L {x - 8} {y + 100} Z" fill="{LIME}" '
                  f'stroke="{INK}" stroke-width="{OL * 1.6}" stroke-linejoin="round"/>'
                  f'<circle cx="{x}" cy="{y + 134}" r="16" fill="{LIME}" stroke="{INK}" stroke-width="{OL * 1.6}"/>')
            kotak += f"M {x - 30} {y - 10} L {x + 30} {y + 160} "
        elif e == "tanya":
            x, y = 345, 120
            d = (f"M {x - 44} {y + 30} Q {x - 44} {y - 30} {x} {y - 30} Q {x + 46} {y - 30} {x + 44} {y + 14} "
                 f"Q {x + 42} {y + 44} {x + 4} {y + 60} L {x + 4} {y + 92}")
            o += gores(d, 26) + gores(d, 12, LIME)
            o += f'<circle cx="{x + 4}" cy="{y + 132}" r="15" fill="{LIME}" stroke="{INK}" stroke-width="{OL * 1.6}"/>'
            kotak += f"M {x - 60} {y - 46} L {x + 60} {y + 152} "
        elif e == "zzz":
            for (x, y), s in zip(((400, 200), (345, 120), (280, 25)), (44, 58, 74)):
                d = f"M {x} {y} L {x + s} {y} L {x} {y + s} L {x + s} {y + s}"
                o += gores(d, 22) + gores(d, 10, LIME)
                kotak += f"M {x - 12} {y - 12} L {x + s + 12} {y + s + 12} "
        elif e == "hati":
            for x, y, s in ((360, 170, 2.4), (1040, 70, 1.8)):
                d = (f"M {x} {y + 14 * s} C {x - 26 * s} {y - 4 * s} {x - 14 * s} {y - 26 * s} {x} {y - 12 * s} "
                     f"C {x + 14 * s} {y - 26 * s} {x + 26 * s} {y - 4 * s} {x} {y + 14 * s} Z")
                o += f'<path d="{d}" fill="{BLUSH}" stroke="{INK}" stroke-width="{OL * 1.4}" stroke-linejoin="round"/>'
                kotak += f"M {x - 30 * s} {y - 26 * s} L {x + 30 * s} {y + 18 * s} "
    return o, kotak


EFEK_MELAYANG = ("seru", "tanya", "zzz", "hati")


# ---------------------------------------------------------------------------
# 4. Ekspresi & pose
# ---------------------------------------------------------------------------
# "galak" = wajah asli dari gambar sumber. Ekspresi lain digambar di kepala polos:
#   mata : bentuk "buka" (kelopak=(y sisi dalam, y sisi luar), lirik=(x, y) arah layar, pupil)
#          atau "senang" / "tidur" / "tawa"; alis = 3 titik kurva dalam satuan mata
#   mulut: seringai, senyum, tawa, o, sedih, kecil, malu
#   efek : merona, keringat, air_mata, seru, tanya, zzz, hati
EKSPRESI = {
    "galak": dict(asli=True, ket="Galak – wajah asli gambar sumber"),
    "senang": dict(mata=dict(bentuk="senang", alis=((-22, -24), (2, -36), (26, -26))),
                   mulut="senyum", efek=["merona"], ket="Senang – menyapa duluan"),
    "curiga": dict(mata=dict(bentuk="buka", kelopak=(-6, -8), lirik=(14, 4), pupil=11,
                             alis=((-30, -22), (0, -24), (30, -22))),
                   mulut="seringai", efek=["keringat"], ket="Curiga – teliti sampai rewel"),
    "kaget": dict(mata=dict(bentuk="buka", rx=30, ry=29, lirik=(0, 0), pupil=7,
                            alis=((-22, -40), (2, -50), (26, -42))),
                  mulut="o", efek=["seru"], ket="Kaget"),
    "sedih": dict(mata=dict(bentuk="buka", kelopak=(-22, 0), lirik=(0, 8), pupil=14, kilau=True,
                            alis=((-28, -40), (0, -34), (28, -18))),
                  mulut="sedih", efek=["air_mata"], ket="Sedih"),
    "ngantuk": dict(mata=dict(bentuk="tidur", alis=((-24, -22), (0, -26), (26, -22))),
                    mulut="kecil", efek=["zzz"], ket="Ngantuk / tidur"),
    "tertawa": dict(mata=dict(bentuk="tawa", alis=((-22, -28), (2, -38), (26, -30))),
                    mulut="tawa", efek=["merona"], ket="Tertawa"),
    "malu": dict(mata=dict(bentuk="buka", kelopak=(-16, -12), lirik=(-12, 8), pupil=12, kilau=True,
                           alis=((-24, -30), (0, -36), (26, -28))),
                 mulut="malu", efek=["merona", "keringat"], ket="Malu-malu"),
    "bingung": dict(mata=dict(bentuk="buka", kelopak=(-24, -12), lirik=(8, -8), pupil=11,
                              alis=((-24, -36), (0, -40), (26, -30))),
                    mulut="kecil", efek=["tanya"], ket="Bingung / berpikir"),
    "jatuh_cinta": dict(mata=dict(bentuk="buka", lirik=(0, 2), pupil=15, kilau=True,
                                  alis=((-22, -36), (2, -46), (26, -38))),
                        mulut="senyum", efek=["merona", "hati"], ket="Terpesona"),
}

# Pose = sudut putar tiap bagian di sendinya (derajat, positif = searah jarum jam).
#   kepala, lengan_n (kanan layar), lengan_k (kiri layar), kaki_k, ekor
#   badan = (geser x, geser y, putar) untuk seluruh karakter
#   depan = bagian yang digambar paling depan; gerak = garis gerak tambahan
POSE = {
    "siaga": dict(ket="Siaga – kuda-kuda dengan cakar terbuka (gambar sumber)", ekspresi="galak"),
    "melambai": dict(lengan_n=-34, kepala=3, ekor=-6, gerak="lambai",
                     ket="Melambai – menyapa duluan", ekspresi="senang"),
    "sorak": dict(lengan_n=-36, lengan_k=34, kepala=-2, badan=(0, -30, 0), ekor=-10, gerak="lompat",
                  ket="Bersorak – kedua cakar terangkat", ekspresi="tertawa"),
    "menerkam": dict(lengan_n=-18, lengan_k=16, kepala=-5, badan=(0, 0, -4), ekor=8,
                     ket="Menerkam – cakar terangkat, badan condong", ekspresi="galak"),
    "termenung": dict(kepala=9, lengan_k=-10, ekor=10,
                      ket="Termenung – kepala miring", ekspresi="bingung"),
    "lesu": dict(kepala=10, lengan_k=-14, lengan_n=6, badan=(0, 8, 3), ekor=14,
                 ket="Lesu – bahu turun, kepala tertunduk", ekspresi="ngantuk"),
}


# ---------------------------------------------------------------------------
# 5. Perakitan
# ---------------------------------------------------------------------------
def kepala_svg(K, ekspresi):
    """Isi grup kepala: jiplakan asli, atau kepala polos + wajah ekspresi."""
    e = EKSPRESI[ekspresi]
    if e.get("asli"):
        return svg_bagian("kepala")
    k = Kanvas()
    mata(k, e["mata"])
    mulut(k, e["mulut"])
    efek_wajah(k, e["efek"])
    K.defs += k.defs
    return svg_bagian("kepala_polos") + "".join(k.out)


def efek_gerak(jenis):
    garis = {"lambai": ("M 1290 150 Q 1330 210 1318 280", "M 1350 110 Q 1410 200 1388 300"),
             "lompat": ("M 520 990 L 520 1060", "M 730 1010 L 730 1080", "M 940 990 L 940 1060")}[jenis]
    return "".join(gores(d, 24) + gores(d, 11, LIME) for d in garis), " ".join(garis)


def gambar(pose="siaga", ekspresi=None):
    p = POSE[pose]
    ekspresi = ekspresi or p["ekspresi"]
    K = Kanvas()
    bx, by, bdeg = p.get("badan", (0, 0, 0))

    def seluruh(q):          # transformasi seluruh badan
        q = putar(q, bdeg, PUSAT)
        return (q[0] + bx, q[1] + by)

    urutan = [n for n in URUTAN if n not in p.get("depan", [])] + p.get("depan", [])
    isi = []
    for nama in urutan:
        deg = p.get(nama, 0) if nama in SENDI else 0
        sendi = SENDI.get(nama, PUSAT)
        g = kepala_svg(K, ekspresi) if nama == "kepala" else svg_bagian(nama)
        if nama == "badan":
            g = gores(ALAS, 2 * OL, INK, VIO_SH) + g
        isi.append(f'<g transform="rotate({deg} {sendi[0]} {sendi[1]})">{g}</g>' if deg else g)
        K.lacak(BAGIAN[nama]["siluet"], lambda q: seluruh(putar(q, deg, sendi)))
    efek, kotak = efek_melayang([x for x in EKSPRESI[ekspresi].get("efek", []) if x in EFEK_MELAYANG])
    if p.get("gerak"):
        g, k2 = efek_gerak(p["gerak"])
        efek, kotak = efek + g, kotak + k2
    if kotak:
        K.lacak(kotak, seluruh)
    K.tambah(f'<g transform="translate({bx} {by}) rotate({bdeg} {PUSAT[0]} {PUSAT[1]})">'
             + "".join(isi) + efek + "</g>")
    return K


def kepala_saja(ekspresi):
    K = Kanvas()
    efek, kotak = efek_melayang([x for x in EKSPRESI[ekspresi].get("efek", []) if x in EFEK_MELAYANG])
    # garis keliling siluet menutup tepi potongan leher, yang aslinya tanpa garis tinta
    K.tambah(gores(BAGIAN["kepala"]["siluet"], 2 * OL) + kepala_svg(K, ekspresi) + efek,
             BAGIAN["kepala"]["siluet"] + " " + kotak)
    return K


# ---------------------------------------------------------------------------
# 6. Lembar & CLI
# ---------------------------------------------------------------------------
def lembar(items, kolom, sel=420, bingkai=None):
    """Susun daftar (Kanvas, label) dalam grid. bingkai=(x, y, sisi) menyamakan skala semua sel."""
    lab = 46
    baris = math.ceil(len(items) / kolom)
    W, H = kolom * sel, baris * (sel + lab)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" fill="#F4EFFF"/>']
    for i, (K, label) in enumerate(items):
        x, y = (i % kolom) * sel, (i // kolom) * (sel + lab)
        bx, by, bs = bingkai or K.bingkai(20)
        out.append(f'<svg x="{x}" y="{y}" width="{sel}" height="{sel}" viewBox="{bx:.1f} {by:.1f} {bs:.1f} {bs:.1f}">'
                   f'{K.isi()}</svg>')
        out.append(f'<text x="{x + sel / 2}" y="{y + sel + 26}" text-anchor="middle" '
                   f'font-family="Fredoka, \'Plus Jakarta Sans\', sans-serif" font-size="22" '
                   f'font-weight="600" fill="{INK}">{label}</text>')
    out.append("</svg>\n")
    return "".join(out)


def simpan(path, teks, png=False):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(teks)
    print(f"Tersimpan: {path}")
    if png:
        try:
            import cairosvg
        except ImportError:
            print("  (PNG dilewati – pasang `cairosvg` jika ingin ekspor PNG)")
            return
        p = os.path.splitext(path)[0] + ".png"
        cairosvg.svg2png(bytestring=teks.encode(), write_to=p)
        print(f"Tersimpan: {p}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generator karakter Noia (SVG) dengan pose & ekspresi.")
    ap.add_argument("-p", "--pose", choices=POSE, help="pose / tingkah laku")
    ap.add_argument("-e", "--ekspresi", choices=EKSPRESI,
                    help="ekspresi wajah (bawaan: pasangan pose). Tanpa -p: kepala saja")
    ap.add_argument("-o", "--out", help="file keluaran (dengan -p atau -e)")
    ap.add_argument("--semua", action="store_true", help="buat semua kombinasi pose x ekspresi")
    ap.add_argument("--daftar", action="store_true", help="tampilkan daftar pose & ekspresi")
    ap.add_argument("--png", action="store_true", help="ekspor PNG juga (perlu cairosvg)")
    a = ap.parse_args(argv)

    if a.daftar:
        print("Pose:")
        for k, v in POSE.items():
            print(f"  {k:<10} {v['ket']} (ekspresi bawaan: {v['ekspresi']})")
        print("Ekspresi:")
        for k, v in EKSPRESI.items():
            print(f"  {k:<12} {v['ket']}")
        return

    folder = os.path.join(DI_SINI, "karakter")
    if a.pose:
        e = a.ekspresi or POSE[a.pose]["ekspresi"]
        simpan(a.out or os.path.join(folder, f"{a.pose}_{e}.svg"), gambar(a.pose, e).svg(), a.png)
        return
    if a.ekspresi:
        simpan(a.out or os.path.join(folder, f"kepala_{a.ekspresi}.svg"), kepala_saja(a.ekspresi).svg(), a.png)
        return

    kombinasi = ([(p, e) for p in POSE for e in EKSPRESI] if a.semua
                 else [(p, POSE[p]["ekspresi"]) for p in POSE])
    for p, e in kombinasi:
        simpan(os.path.join(folder, f"{p}_{e}.svg"), gambar(p, e).svg(), a.png)
    simpan(os.path.join(folder, "lembar_pose.svg"),
           lembar([(gambar(p), p) for p in POSE], 3), a.png)
    simpan(os.path.join(folder, "lembar_ekspresi.svg"),
           lembar([(kepala_saja(e), e.replace("_", " ")) for e in EKSPRESI], 5, sel=300,
                  bingkai=(260, -150, 840)), a.png)


if __name__ == "__main__":
    main()
