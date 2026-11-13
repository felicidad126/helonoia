"""
HELONOIA – generator karakter "Noia" (gaya kartun bergaris tebal) dengan ekspresi & pose
======================================================================================

Menggambar karakter monster ungu bercakar besar, bertanduk lime, dan berekor sebagai
SVG vektor murni. Bentuk dibangun dari kerangka (sendi bahu-siku-pergelangan, pinggul-
lutut-pergelangan kaki), jadi setiap pose cukup ditulis sebagai posisi sendi, dan setiap
ekspresi cukup ditulis sebagai bentuk mata, alis, mulut, dan efek.

Tidak butuh library tambahan: cukup Python 3.

    python3 helonoia_karakter.py                      # semua pose + lembar ekspresi
    python3 helonoia_karakter.py -p siaga -e galak    # satu kombinasi
    python3 helonoia_karakter.py -p melambai -e senang -o noia.svg
    python3 helonoia_karakter.py --daftar             # lihat pose & ekspresi yang ada
    python3 helonoia_karakter.py --png                # + PNG (perlu `pip install cairosvg`)

Hasil (bawaan) di folder karakter/:
    <pose>_<ekspresi>.svg   satu karakter, latar transparan
    lembar_pose.svg         semua pose dengan ekspresi pasangannya
    lembar_ekspresi.svg     semua ekspresi (kepala saja)

Teknik gambar:
  * Garis luar: setiap "lapisan" digambar dua kali – dulu goresan hitam tebal, lalu isinya.
    Bentuk dalam satu lapisan menyatu tanpa garis sambungan (mis. lengan + telapak + jari),
    sedangkan lapisan yang bertumpuk tetap punya garis pemisah, seperti gambar kartun.
  * Bayangan: warna gelap diisi penuh, lalu warna dasar yang digeser ke kiri-atas dipotong
    (clip) oleh bentuk aslinya, sehingga tersisa sabit bayangan di sisi kanan-bawah.
"""

import argparse
import math
import os
import sys

# ---------------------------------------------------------------------------
# Palet (sama dengan logo, ditambah warna cakar & aksen ekspresi)
# ---------------------------------------------------------------------------
INK    = "#120B1E"   # garis luar
VIO    = "#A35BFA"   # badan
VIO_SH = "#7C3FD6"   # bayangan badan
BELLY  = "#D9B8FF"   # perut
BEL_SH = "#C29BF5"
LIME   = "#C6FF3D"   # tanduk, garis ekor
LIM_SH = "#93CC1A"
CLAW   = "#F6EEFF"   # cakar
CLW_SH = "#C7AEF0"
WHITE  = "#FFFFFF"   # bola mata
MOUTH  = "#3B1258"   # rongga mulut
TONGUE = "#FF7FB0"
BLUSH  = "#FF7FB0"
ANGER  = "#FF4F7B"
TEAR   = "#8FD8FF"

OL = 5.5   # tebal garis luar


# ---------------------------------------------------------------------------
# Geometri dasar
# ---------------------------------------------------------------------------
def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def ang(deg):
    r = math.radians(deg)
    return (math.cos(r), math.sin(r))


def rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def fmt(pts, closed=True):
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return d + (" Z" if closed else "")


def catmull(pts, n=10):
    """Titik-titik halus (Catmull-Rom) yang melewati semua `pts`. Mengembalikan (titik, segmen, t)."""
    if len(pts) == 2:
        return [(add(pts[0], mul((pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]), i / n)), 0, i / n)
                for i in range(n + 1)]
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n + (1 if i == len(P) - 3 else 0)):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append((tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t
                                     + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                     + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
                             for k in (0, 1)), i - 1, t))
    return out


def tube(pts, ws, n=10, cap=8):
    """Bentuk pipa halus melewati `pts` dengan setengah-lebar `ws` di tiap titik (ujung membulat)."""
    s = catmull(pts, n)
    c = [p for p, _, _ in s]
    w = [ws[i] + (ws[min(i + 1, len(ws) - 1)] - ws[i]) * t for _, i, t in s]
    L, R = [], []
    for k in range(len(c)):
        a, b = c[max(k - 1, 0)], c[min(k + 1, len(c) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1
        nx, ny = -ty / ln, tx / ln
        L.append((c[k][0] + nx * w[k], c[k][1] + ny * w[k]))
        R.append((c[k][0] - nx * w[k], c[k][1] - ny * w[k]))

    def capr(center, frm, r):
        a0 = math.atan2(frm[1] - center[1], frm[0] - center[0])
        return [(center[0] + math.cos(a0 - math.pi * k / cap) * r,
                 center[1] + math.sin(a0 - math.pi * k / cap) * r) for k in range(1, cap)]

    end = capr(c[-1], L[-1], w[-1]) if w[-1] > 0.5 else []
    start = capr(c[0], R[0], w[0]) if w[0] > 0.5 else []
    return fmt(L + end + R[::-1] + start)


def arc_line(base, deg, length, turn, n=16):
    """Garis tengah melengkung: mulai di `base` ke arah `deg`, berbelok total `turn` derajat."""
    pts, p = [base], base
    for i in range(n):
        a = deg + turn * (i + 0.5) / n
        p = add(p, mul(ang(a), length / n))
        pts.append(p)
    return pts


def horn(base, deg, length, w, turn):
    """Tanduk / cakar: pipa melengkung yang meruncing sampai ujung."""
    pts = arc_line(base, deg, length, turn, 8)
    ws = [w * (1 - i / 8) ** 0.8 for i in range(9)]
    return tube(pts, ws, n=4)


def blob(cx, cy, rx, ry_top, ry_bot, squeeze=0.0, n=48):
    """Bulatan dengan tinggi atas/bawah berbeda; `squeeze` menyempitkan bagian bawah (dagu)."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        s = math.sin(t)
        ry = ry_bot if s > 0 else ry_top
        x = rx * math.cos(t) * (1 - squeeze * max(s, 0) ** 2)
        pts.append((cx + x, cy + ry * s))
    return fmt(pts)


def spike(p1, p2, tip, bend=0.0):
    """Duri / telinga: segitiga dengan sisi melengkung dari alas p1-p2 ke ujung `tip`."""
    m1 = add(mul(add(p1, tip), 0.5), (bend, -abs(bend) * 0.3))
    m2 = add(mul(add(p2, tip), 0.5), (bend, -abs(bend) * 0.3))
    return (f"M {p1[0]:.1f} {p1[1]:.1f} Q {m1[0]:.1f} {m1[1]:.1f} {tip[0]:.1f} {tip[1]:.1f} "
            f"Q {m2[0]:.1f} {m2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f} Z")


# ---------------------------------------------------------------------------
# Kanvas: lapisan bergaris, bayangan, batas gambar
# ---------------------------------------------------------------------------
class Kanvas:
    def __init__(self):
        self.out = []
        self.defs = []
        self.nid = 0
        self.box = [1e9, 1e9, -1e9, -1e9]

    def track(self, d, tf=(0, 0)):
        nums = [float(v) for v in d.replace("M", " ").replace("L", " ").replace("Q", " ")
                .replace("Z", " ").replace("C", " ").split()]
        for i in range(0, len(nums) - 1, 2):
            x, y = nums[i] + tf[0], nums[i + 1] + tf[1]
            b = self.box
            b[0], b[1], b[2], b[3] = min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)

    def clip(self, d):
        self.nid += 1
        cid = f"k{self.nid}"
        self.defs.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        return cid

    def lapisan(self, shapes, tf=(0, 0), garis=OL):
        """shapes: daftar dict {d, fill, shade?, geser?, dalam?: [(d, warna)]}.
        Semua bentuk dalam satu lapisan menyatu: garis luar hanya di tepi gabungannya."""
        g = []
        if garis:
            g.append(f'<g fill="{INK}" stroke="{INK}" stroke-width="{2 * garis}" stroke-linejoin="round">'
                     + "".join(f'<path d="{s["d"]}"/>' for s in shapes) + "</g>")
        for s in shapes:
            self.track(s["d"], tf)
            d, fill, sh = s["d"], s["fill"], s.get("shade")
            if not sh and not s.get("dalam"):
                g.append(f'<path d="{d}" fill="{fill}"/>')
                continue
            cid = self.clip(d)
            if sh:
                dx, dy = s.get("geser", (-7, -7))
                g.append(f'<path d="{d}" fill="{sh}"/><g clip-path="url(#{cid})">'
                         f'<path d="{d}" fill="{fill}" transform="translate({dx} {dy})"/></g>')
            else:
                g.append(f'<path d="{d}" fill="{fill}"/>')
            for dd, warna in s.get("dalam", []):
                g.append(f'<g clip-path="url(#{cid})"><path d="{dd}" fill="{warna}"/></g>')
        self.out.append("".join(g))

    def raw(self, svg, d_track=None, tf=(0, 0)):
        if d_track:
            self.track(d_track, tf)
        self.out.append(svg)

    def svg(self, pad=24, ukuran=None):
        x0, y0, x1, y1 = self.box
        x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        w, h = x1 - x0, y1 - y0
        s = max(w, h)
        x0 -= (s - w) / 2
        y0 -= (s - h) / 2
        px = ukuran or 1000
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {s:.1f} {s:.1f}" '
                f'width="{px}" height="{px}"><defs>{"".join(self.defs)}</defs>{"".join(self.out)}</svg>\n')

    def isi(self):
        return f'<defs>{"".join(self.defs)}</defs>{"".join(self.out)}'


# ---------------------------------------------------------------------------
# Bagian tubuh
# ---------------------------------------------------------------------------
def cakar_set(K, ujung, arah, curl, panjang=34, lebar=19, belok=70):
    """Cakar-cakar putih di ujung jari. ujung: daftar (titik, arah jari).
    curl = arah lengkung: +1 searah jarum jam, -1 berlawanan."""
    shapes = []
    for (p, a) in ujung:
        # pangkal sedikit masuk ke jari, mulai agak melebar keluar lalu melengkung
        d = horn(add(p, mul(ang(a), -lebar * 0.45)), a - curl * belok * 0.3, panjang, lebar / 2, curl * belok)
        shapes.append({"d": d, "fill": CLAW, "shade": CLW_SH, "geser": (-4, -4)})
    K.lapisan(shapes)


def tangan(sendi, w, arah, spread=30, curl=1, jari=3, panjang_jari=20, cakar=34):
    """Lengan (bahu-siku-pergelangan) + telapak + jari. Mengembalikan (shapes, ujung_jari)."""
    u = ang(arah)
    v = (-u[1], u[0])
    W = sendi[-1]
    shapes = [{"d": tube(sendi, w), "fill": VIO, "shade": VIO_SH}]
    palm_end = add(W, mul(u, w[-1] * 0.7))
    shapes.append({"d": tube([W, palm_end], [w[-1], w[-1] * 1.15]), "fill": VIO, "shade": VIO_SH})
    ujung = []
    offs = [(-1 + 2 * i / (jari - 1)) if jari > 1 else 0 for i in range(jari)]
    for o in offs:
        a = arah + o * spread
        base = add(add(palm_end, mul(v, o * w[-1] * 0.8)), mul(u, -4))
        tip = add(base, mul(ang(a), panjang_jari))
        shapes.append({"d": tube([base, tip], [w[-1] * 0.5, w[-1] * 0.44]), "fill": VIO, "shade": VIO_SH,
                       "geser": (-4, -4)})
        ujung.append((tip, a))
    return shapes, ujung


def anggota(K, sendi, w, arah, spread, curl, cakar_len, jari=3, panjang_jari=20, lebar_cakar=19, belok=70):
    shapes, ujung = tangan(sendi, w, arah, spread, curl, jari, panjang_jari)
    K.lapisan(shapes)
    cakar_set(K, ujung, arah, curl, cakar_len, lebar_cakar, belok)   # cakar di atas ujung jari


def ekor(K, pts, ws):
    d = tube(pts, ws, n=10)
    # garis lime di sisi dalam ekor: pipa yang sama, digeser ke satu sisi
    geser = [(p[0] + 10, p[1] + 12) for p in pts]
    lime = tube(geser, [x * 0.75 for x in ws], n=10)
    K.lapisan([{"d": d, "fill": VIO, "shade": VIO_SH, "dalam": [(lime, LIME)]}])


def badan(K, hip, chest):
    bawah = add(hip, (0, 26))
    d = tube([bawah, hip, add(mul(add(hip, chest), 0.5), (0, 0)), chest], [50, 64, 58, 46], n=10)
    perut = blob(hip[0] + 4, (hip[1] + chest[1]) / 2 + 16, 40, 48, 44)
    K.lapisan([{"d": d, "fill": VIO, "shade": VIO_SH, "geser": (-9, -6), "dalam": [(perut, BELLY)]}])


# ---------------------------------------------------------------------------
# Kepala & wajah (koordinat lokal kepala, pusat 0,0)
# ---------------------------------------------------------------------------
HEAD_RX, HEAD_TOP, HEAD_BOT = 108, 92, 84


def kepala(K, c, tilt, ekspresi):
    tf = f"translate({c[0]:.1f} {c[1]:.1f}) rotate({tilt})"
    k2 = Kanvas()
    k2.nid = K.nid
    # tanduk (di belakang kepala)
    k2.lapisan([
        {"d": horn((-52, -60), -150, 150, 27, 120), "fill": LIME, "shade": LIM_SH, "geser": (-6, -6)},
        {"d": horn((52, -60), -30, 150, 27, -120), "fill": LIME, "shade": LIM_SH, "geser": (-6, -6)},
    ])
    hd = blob(0, 0, HEAD_RX, HEAD_TOP, HEAD_BOT, squeeze=0.22)
    shapes = [
        # telinga runcing di sisi kepala
        {"d": spike((-96, -34), (-104, 4), (-150, -66), bend=-4), "fill": VIO, "shade": VIO_SH},
        {"d": spike((96, -34), (104, 4), (150, -66), bend=4), "fill": VIO, "shade": VIO_SH},
        # bulu pipi bergerigi
        {"d": spike((-96, 18), (-80, 52), (-132, 52)), "fill": VIO},
        {"d": spike((96, 18), (80, 52), (132, 52)), "fill": VIO, "shade": VIO_SH},
        # jambul di ubun-ubun
        {"d": spike((-14, -86), (22, -88), (-6, -130), bend=-4), "fill": VIO},
        {"d": hd, "fill": VIO, "shade": VIO_SH, "geser": (-10, -9)},
    ]
    k2.lapisan(shapes)
    wajah(k2, ekspresi)
    K.defs += k2.defs
    K.nid = k2.nid
    K.raw(f'<g transform="{tf}">{"".join(k2.out)}</g>')
    # batas kepala (lokal -> global, kira-kira)
    x0, y0, x1, y1 = k2.box
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        p = add(c, rot((x, y), tilt))
        K.track(f"M {p[0]} {p[1]}")


def stroke(d, w=6, col=INK, fill="none"):
    return (f'<path d="{d}" fill="{fill}" stroke="{col}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


EYE = (42, 6)   # posisi mata kanan (x positif); mata kiri dicerminkan


def mata(K, cfg):
    """cfg: bentuk 'buka' dengan kelopak (lid) & pupil, atau bentuk garis (senang/tidur/tawa)."""
    out = ""
    kind = cfg.get("bentuk", "buka")
    for sx in (-1, 1):
        ex, ey = EYE[0] * sx, EYE[1]
        if kind == "buka":
            rx, ry = cfg.get("rx", 26), cfg.get("ry", 30)
            eye = blob(ex, ey, rx, ry, ry * 0.95)
            cid = K.clip(eye)
            gx, gy = cfg.get("lirik", (0, 4))
            pr = cfg.get("pupil", 14)
            px, py = ex + gx * (1 if cfg.get("lirik_cermin", False) is False else sx), ey + gy
            pup = (f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{pr}" fill="{INK}"/>'
                   f'<circle cx="{px - pr * 0.35:.1f}" cy="{py - pr * 0.4:.1f}" r="{max(3, pr * 0.32):.1f}" fill="{WHITE}"/>')
            if cfg.get("kilau"):
                pup += f'<circle cx="{px + pr * 0.35:.1f}" cy="{py + pr * 0.35:.1f}" r="{pr * 0.18:.1f}" fill="{WHITE}"/>'
            lid = ""
            if "kelopak" in cfg:
                # garis kelopak: (y di sisi luar, y di sisi dalam) – di atasnya tertutup kulit
                yo, yi = ey + cfg["kelopak"][0], ey + cfg["kelopak"][1]
                xo, xi = ex + sx * (rx + 6), ex - sx * (rx + 6)
                lid_d = f"M {xo} {yo} L {xi} {yi} L {xi} {ey - 80} L {xo} {ey - 80} Z"
                lid = (f'<path d="{lid_d}" fill="{VIO}"/>'
                       + stroke(f"M {xo} {yo} L {xi} {yi}", 7))
            out += (f'<path d="{eye}" fill="{WHITE}"/><g clip-path="url(#{cid})">{pup}{lid}</g>'
                    + stroke(eye, OL))
            if cfg.get("bawah"):   # garis kelopak bawah (marah / curiga)
                out += stroke(f"M {ex - sx * 18} {ey + ry * 0.95 + 6} Q {ex} {ey + ry + 12} {ex + sx * 18} {ey + ry * 0.95 + 4}",
                              4.5, VIO_SH)
        elif kind == "senang":     # ^ ^
            out += stroke(f"M {ex - 20} {ey + 8} Q {ex} {ey - 22} {ex + 20} {ey + 8}", 8)
        elif kind == "tidur":      # u u
            out += stroke(f"M {ex - 20} {ey - 2} Q {ex} {ey + 18} {ex + 20} {ey - 2}", 7)
            out += stroke(f"M {ex + sx * 20} {ey - 2} l {sx * 7} -4", 5)
        elif kind == "tawa":       # > <
            out += stroke(f"M {ex - sx * 18} {ey - 14} L {ex + sx * 12} {ey + 2} L {ex - sx * 18} {ey + 16}", 8)
    K.raw(out)


def alis(K, cfg):
    if not cfg:
        return
    out = ""
    for sx in (-1, 1):
        (xo, yo), (xm, ym), (xi, yi) = cfg
        out += stroke(f"M {sx * xo} {yo} Q {sx * xm} {ym} {sx * xi} {yi}", 11)
    K.raw(out)


def taring(x, y, h=12, w=9, arah=-1):
    """Gigi taring kecil; arah -1 = menunjuk ke atas (dari bibir bawah), +1 = ke bawah."""
    d = f"M {x - w / 2} {y} L {x} {y + arah * h} L {x + w / 2} {y} Z"
    return f'<path d="{d}" fill="{WHITE}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'


def mulut(K, jenis):
    y = 50
    if jenis == "cemberut":
        o = stroke(f"M -20 {y + 6} Q 0 {y - 8} 20 {y + 6}", 6)
        o += taring(-12, y + 2, 11, 9, -1) + taring(12, y + 2, 11, 9, -1)
    elif jenis == "seringai":
        o = stroke(f"M -26 {y} Q 2 {y + 12} 28 {y - 10}", 6) + taring(12, y + 4, 13, 10, 1)
    elif jenis in ("senyum", "tawa"):
        lb = 30 if jenis == "senyum" else 34
        dl = 26 if jenis == "senyum" else 30
        d = f"M -{lb} {y - 4} Q 0 {y + 2} {lb} {y - 4} Q {lb - 4} {y + dl} 0 {y + dl + 2} Q -{lb - 4} {y + dl} -{lb} {y - 4} Z"
        cid = K.clip(d)
        lidah = f'<ellipse cx="4" cy="{y + dl}" rx="{lb * 0.6}" ry="{dl * 0.5}" fill="{TONGUE}"/>'
        o = (f'<path d="{d}" fill="{MOUTH}"/><g clip-path="url(#{cid})">{lidah}</g>'
             + stroke(d, 5.5) + taring(-lb * 0.45, y - 1, 12, 10, 1) + taring(lb * 0.45, y - 1, 12, 10, 1))
    elif jenis == "o":
        d = blob(0, y + 6, 13, 17, 15)
        o = f'<path d="{d}" fill="{MOUTH}"/>' + stroke(d, 5.5)
    elif jenis == "sedih":
        o = stroke(f"M -22 {y + 10} Q -10 {y - 4} 0 {y + 2} Q 10 {y - 4} 22 {y + 10}", 6)
    elif jenis == "kecil":
        o = stroke(f"M -8 {y + 4} Q 0 {y + 9} 8 {y + 4}", 5)
    elif jenis == "malu":
        o = stroke(f"M -18 {y + 4} q 6 -6 12 0 q 6 6 12 0 q 6 -6 12 0", 5)
    else:
        o = ""
    K.raw(o)


def tetes(x, y, s, warna):
    d = (f"M {x} {y - 20 * s} C {x + 4 * s} {y - 10 * s} {x + 13 * s} {y} {x + 13 * s} {y + 8 * s} "
         f"C {x + 13 * s} {y + 16 * s} {x + 7 * s} {y + 21 * s} {x} {y + 21 * s} "
         f"C {x - 7 * s} {y + 21 * s} {x - 13 * s} {y + 16 * s} {x - 13 * s} {y + 8 * s} "
         f"C {x - 13 * s} {y} {x - 4 * s} {y - 10 * s} {x} {y - 20 * s} Z")
    return f'<path d="{d}" fill="{warna}" stroke="{INK}" stroke-width="4"/>'


def efek_wajah(K, daftar):
    o = ""
    for e in daftar:
        if e == "merona":
            o += "".join(f'<ellipse cx="{sx * 62}" cy="44" rx="18" ry="9" fill="{BLUSH}" opacity="0.75"/>'
                         for sx in (-1, 1))
        elif e == "keringat":
            o += tetes(98, -52, 1.2, WHITE)
        elif e == "air_mata":
            o += tetes(-58, 50, 0.9, TEAR) + tetes(58, 56, 0.8, TEAR)
        elif e == "urat":   # tanda marah
            o += "".join(stroke(f"M {74 + a} {-74 + b} q {c} {d} {e2} {f}", 6, ANGER)
                         for a, b, c, d, e2, f in ((0, 0, 8, 4, 10, 14), (24, 0, -8, 4, -10, 14),
                                                    (0, 30, 8, -4, 10, -14), (24, 30, -8, -4, -10, -14)))
        elif e == "seru":   # tanda seru
            o += (f'<path d="M 128 -150 L 146 -150 L 141 -100 L 133 -100 Z" fill="{LIME}" stroke="{INK}" '
                  f'stroke-width="4" stroke-linejoin="round"/>'
                  f'<circle cx="137" cy="-84" r="8" fill="{LIME}" stroke="{INK}" stroke-width="4"/>')
        elif e == "zzz":
            for i, (x, y, s) in enumerate(((112, -118, 22), (142, -150, 28), (176, -188, 34))):
                o += stroke(f"M {x} {y} l {s} 0 l {-s} {s} l {s} 0", 6, INK)
                o += stroke(f"M {x} {y} l {s} 0 l {-s} {s} l {s} 0", 3, LIME)
        elif e == "tanya":
            o += stroke("M 120 -128 Q 122 -160 146 -160 Q 170 -160 168 -138 Q 166 -122 146 -116 L 146 -100", 9)
            o += stroke("M 120 -128 Q 122 -160 146 -160 Q 170 -160 168 -138 Q 166 -122 146 -116 L 146 -100", 4, LIME)
            o += f'<circle cx="146" cy="-82" r="7" fill="{LIME}" stroke="{INK}" stroke-width="4"/>'
        elif e == "hati":
            for x, y, s in ((-150, -110, 1.0), (150, -140, 0.8)):
                d = (f"M {x} {y + 14 * s} C {x - 26 * s} {y - 4 * s} {x - 14 * s} {y - 26 * s} {x} {y - 12 * s} "
                     f"C {x + 14 * s} {y - 26 * s} {x + 26 * s} {y - 4 * s} {x} {y + 14 * s} Z")
                o += f'<path d="{d}" fill="{BLUSH}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
    K.raw(o, "M -190 -200 L 190 -200" if o else None)


# ---------------------------------------------------------------------------
# Ekspresi
# ---------------------------------------------------------------------------
EKSPRESI = {
    "galak": dict(
        mata=dict(bentuk="buka", kelopak=(-24, 4), lirik=(4, 8), pupil=14, bawah=True),
        alis=((70, -36), (44, -30), (14, -8)), mulut="cemberut", efek=[],
        ket="Galak – siap menjaga (seperti sketsa)"),
    "senang": dict(
        mata=dict(bentuk="senang"), alis=((64, -40), (44, -50), (20, -42)), mulut="senyum",
        efek=["merona"], ket="Senang – menyapa duluan"),
    "curiga": dict(
        mata=dict(bentuk="buka", kelopak=(-4, -4), lirik=(12, 8), pupil=12, bawah=True),
        alis=((66, -26), (44, -24), (18, -22)), mulut="seringai", efek=["keringat"],
        ket="Curiga – teliti sampai rewel"),
    "kaget": dict(
        mata=dict(bentuk="buka", rx=30, ry=35, lirik=(0, 0), pupil=8),
        alis=((66, -54), (44, -66), (20, -56)), mulut="o", efek=["seru"],
        ket="Kaget"),
    "sedih": dict(
        mata=dict(bentuk="buka", kelopak=(4, -22), lirik=(0, 10), pupil=16, kilau=True),
        alis=((66, -20), (44, -34), (18, -46)), mulut="sedih", efek=["air_mata"],
        ket="Sedih"),
    "ngantuk": dict(
        mata=dict(bentuk="tidur"), alis=((64, -30), (44, -34), (20, -30)), mulut="kecil",
        efek=["zzz"], ket="Ngantuk / tidur"),
    "tertawa": dict(
        mata=dict(bentuk="tawa"), alis=((64, -42), (44, -52), (20, -44)), mulut="tawa",
        efek=["merona"], ket="Tertawa"),
    "malu": dict(
        mata=dict(bentuk="buka", kelopak=(-14, -20), lirik=(-12, 10), pupil=12, kilau=True),
        alis=((64, -32), (44, -40), (20, -34)), mulut="malu", efek=["merona", "keringat"],
        ket="Malu-malu"),
    "bingung": dict(
        mata=dict(bentuk="buka", kelopak=(-10, -30), lirik=(10, -6), pupil=12),
        alis=((66, -34), (44, -44), (18, -36)), mulut="kecil", efek=["tanya"],
        ket="Bingung / berpikir"),
    "jatuh_cinta": dict(
        mata=dict(bentuk="buka", lirik=(0, 2), pupil=16, kilau=True),
        alis=((64, -44), (44, -54), (20, -46)), mulut="senyum", efek=["merona", "hati"],
        ket="Terpesona"),
}


def wajah(K, nama):
    e = EKSPRESI[nama]
    mata(K, e["mata"])
    alis(K, e["alis"])
    mulut(K, e["mulut"])
    efek_wajah(K, e["efek"])


# ---------------------------------------------------------------------------
# Pose (koordinat relatif terhadap pinggul (0, 0); x negatif = kiri layar)
#   lengan: [bahu, siku, pergelangan], tangan: (arah derajat, sebaran jari, curl)
#   kaki  : [pinggul, lutut, pergelangan], telapak: (arah, sebaran, curl)
# ---------------------------------------------------------------------------
POSE = {
    "siaga": dict(
        dada=(0, -70), kepala=(0, -176), miring=-4,
        lengan_k=[(-30, -66), (-100, -48), (-136, -2)], tangan_k=(105, 30, -1),
        lengan_n=[(30, -66), (104, -84), (146, -44)], tangan_n=(70, 30, 1),
        kaki_k=[(-30, 4), (-78, 40), (-88, 96)], telapak_k=(125, 34, -1),
        kaki_n=[(30, 4), (82, 36), (98, 96)], telapak_n=(55, 34, 1),
        ekor=[(26, 22), (104, 46), (150, 10), (164, -50)], depan=[],
        ket="Siaga – kuda-kuda dengan cakar terbuka", ekspresi="galak"),
    "melambai": dict(
        dada=(0, -72), kepala=(-4, -180), miring=-6,
        lengan_k=[(-30, -66), (-80, -30), (-98, 22)], tangan_k=(100, 26, -1),
        lengan_n=[(30, -66), (120, -86), (172, -146)], tangan_n=(-65, 32, -1),
        kaki_k=[(-30, 4), (-42, 50), (-48, 98)], telapak_k=(118, 34, -1),
        kaki_n=[(30, 4), (42, 50), (48, 98)], telapak_n=(62, 34, 1),
        ekor=[(-26, 22), (-100, 40), (-146, 14), (-160, -40)], depan=["n"], gerak="lambai",
        ket="Melambai – menyapa duluan", ekspresi="senang"),
    "lompat": dict(
        dada=(0, -72), kepala=(0, -180), miring=0,
        lengan_k=[(-30, -66), (-112, -104), (-168, -160)], tangan_k=(-125, 32, 1),
        lengan_n=[(30, -66), (112, -104), (168, -160)], tangan_n=(-55, 32, -1),
        kaki_k=[(-30, 4), (-74, 34), (-66, 82)], telapak_k=(140, 30, -1),
        kaki_n=[(30, 4), (74, 34), (66, 82)], telapak_n=(40, 30, 1),
        ekor=[(26, 22), (96, 56), (156, 46), (190, 0)], depan=[], gerak="lompat",
        ket="Lompat kegirangan", ekspresi="tertawa"),
    "berpikir": dict(
        dada=(0, -72), kepala=(-8, -180), miring=-10,
        lengan_k=[(-30, -66), (-80, -30), (-98, 22)], tangan_k=(100, 26, -1),
        lengan_n=[(30, -66), (86, -24), (40, -70)], tangan_n=(-130, 22, -1),
        kaki_k=[(-30, 4), (-42, 50), (-48, 98)], telapak_k=(118, 34, -1),
        kaki_n=[(30, 4), (42, 50), (48, 98)], telapak_n=(62, 34, 1),
        ekor=[(26, 22), (100, 44), (148, 22), (166, -30)], depan=["n"],
        ket="Berpikir – tangan di dagu", ekspresi="bingung"),
    "menunjuk": dict(
        dada=(0, -72), kepala=(6, -180), miring=8,
        lengan_k=[(-30, -66), (-80, -30), (-98, 22)], tangan_k=(100, 26, -1),
        lengan_n=[(30, -66), (110, -82), (184, -92)], tangan_n=(-6, 16, 1),
        kaki_k=[(-30, 4), (-46, 50), (-54, 98)], telapak_k=(122, 34, -1),
        kaki_n=[(30, 4), (46, 50), (54, 98)], telapak_n=(58, 34, 1),
        ekor=[(-26, 22), (-100, 40), (-146, 14), (-160, -40)], depan=[],
        ket="Menunjuk – 'lihat ini!' (cocok untuk promosi)", ekspresi="senang"),
    "duduk": dict(
        dada=(0, -72), kepala=(0, -178), miring=-6,
        lengan_k=[(-30, -66), (-74, -30), (-46, 4)], tangan_k=(40, 26, 1),
        lengan_n=[(30, -66), (74, -30), (46, 4)], tangan_n=(140, 26, -1),
        kaki_k=[(-30, 8), (-80, 34), (-126, 36)], telapak_k=(-115, 30, -1),
        kaki_n=[(30, 8), (80, 34), (126, 36)], telapak_n=(-65, 30, 1),
        ekor=[(20, 30), (100, 60), (190, 60), (226, 28)], depan=["k", "n"],
        ket="Duduk santai", ekspresi="ngantuk"),
}

LENGAN_W = [24, 23, 30]
KAKI_W = [33, 28, 26]


def gerak(K, jenis):
    if jenis == "lambai":
        o = ""
        for d in ("M 240 -236 Q 258 -204 248 -172", "M 270 -254 Q 292 -208 278 -164"):
            o += stroke(d, 10, INK) + stroke(d, 5, LIME)
        K.raw(o, "M 240 -254 L 294 -164")
    elif jenis == "lompat":
        o = ""
        for x in (-60, 0, 60):
            o += stroke(f"M {x} 150 L {x} 190", 10, INK) + stroke(f"M {x} 150 L {x} 190", 5, LIME)
        K.raw(o, "M -70 150 L 70 192")


def gambar(pose, ekspresi=None, K=None):
    p = POSE[pose]
    ekspresi = ekspresi or p["ekspresi"]
    K = K or Kanvas()
    hip = (0, 0)
    chest = p["dada"]

    def lengan(s):
        sendi = p[f"lengan_{s}"]
        a, spr, curl = p[f"tangan_{s}"]
        anggota(K, sendi, LENGAN_W, a, spr, curl, 56, jari=3, panjang_jari=16, lebar_cakar=26, belok=70)

    # urutan dari belakang ke depan: ekor, lengan, kaki, badan, kepala, lengan "depan"
    ekor(K, p["ekor"], [26, 21, 13, 0])
    for s in ("k", "n"):
        if s not in p["depan"]:
            lengan(s)
    for s in ("k", "n"):
        sendi = p[f"kaki_{s}"]
        a, spr, curl = p[f"telapak_{s}"]
        anggota(K, sendi, KAKI_W, a, spr, curl, 34, jari=3, panjang_jari=10, lebar_cakar=21, belok=40)
    badan(K, hip, chest)
    kepala(K, p["kepala"], p["miring"], ekspresi)
    for s in p["depan"]:
        lengan(s)
    if p.get("gerak"):
        gerak(K, p["gerak"])
    return K


# ---------------------------------------------------------------------------
# Lembar & CLI
# ---------------------------------------------------------------------------
def lembar(items, kolom, sel=420, judul=True, kotak=None):
    """Susun beberapa gambar (daftar (Kanvas, label)) dalam grid.
    kotak=(x0, y0, x1, y1) memakai bingkai yang sama untuk semua sel (skala seragam)."""
    baris = math.ceil(len(items) / kolom)
    lab = 46 if judul else 0
    W, H = kolom * sel, baris * (sel + lab)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" fill="#F4EFFF"/>']
    for i, (K, label) in enumerate(items):
        x, y = (i % kolom) * sel, (i // kolom) * (sel + lab)
        x0, y0, x1, y1 = kotak or K.box
        pad = 0 if kotak else 20
        x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        s = max(x1 - x0, y1 - y0)
        x0 -= (s - (x1 - x0)) / 2
        y0 -= (s - (y1 - y0)) / 2
        out.append(f'<svg x="{x}" y="{y}" width="{sel}" height="{sel}" viewBox="{x0:.1f} {y0:.1f} {s:.1f} {s:.1f}">'
                   f'{K.isi()}</svg>')
        if judul:
            out.append(f'<text x="{x + sel / 2}" y="{y + sel + 26}" text-anchor="middle" '
                       f'font-family="Fredoka, \'Plus Jakarta Sans\', sans-serif" font-size="22" '
                       f'font-weight="600" fill="{INK}">{label}</text>')
    out.append("</svg>\n")
    return "".join(out)


def kepala_saja(ekspresi):
    K = Kanvas()
    kepala(K, (0, 0), 0, ekspresi)
    return K


class _Unik:
    """Setiap gambar dalam satu lembar butuh id clip yang berbeda."""
    n = 0


def baru():
    K = Kanvas()
    _Unik.n += 1
    K.nid = _Unik.n * 100000
    return K


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
    ap.add_argument("-e", "--ekspresi", choices=EKSPRESI, help="ekspresi wajah (bawaan: pasangan pose)")
    ap.add_argument("-o", "--out", help="file keluaran (dengan -p)")
    ap.add_argument("--semua", action="store_true", help="buat SEMUA kombinasi pose x ekspresi")
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

    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "karakter")
    if a.pose:
        K = gambar(a.pose, a.ekspresi, baru())
        nama = f"{a.pose}_{a.ekspresi or POSE[a.pose]['ekspresi']}.svg"
        simpan(a.out or os.path.join(folder, nama), K.svg(), a.png)
        return
    if a.ekspresi:
        K = kepala_saja(a.ekspresi)
        simpan(a.out or os.path.join(folder, f"kepala_{a.ekspresi}.svg"), K.svg(), a.png)
        return

    kombinasi = ([(p, e) for p in POSE for e in EKSPRESI] if a.semua
                 else [(p, POSE[p]["ekspresi"]) for p in POSE])
    for p, e in kombinasi:
        simpan(os.path.join(folder, f"{p}_{e}.svg"), gambar(p, e, baru()).svg(), a.png)
    simpan(os.path.join(folder, "lembar_pose.svg"),
           lembar([(gambar(p, None, baru()), p) for p in POSE], 3), a.png)
    simpan(os.path.join(folder, "lembar_ekspresi.svg"),
           lembar([(_kepala(e), e.replace("_", " ")) for e in EKSPRESI], 5, sel=300,
                  kotak=(-215, -240, 215, 130)), a.png)


def _kepala(e):
    K = baru()
    kepala(K, (0, 0), 0, e)
    return K


if __name__ == "__main__":
    main()
