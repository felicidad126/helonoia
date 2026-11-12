"""
HELONOIA – generator karakter monster (versi final: ekspresi "Curiga", cakar talon)
=================================================================================

Script ini menggambar maskot Helonoia sebagai SVG vektor murni.
Tidak butuh library tambahan: cukup Python 3.

    python3 helonoia_monster.py

Hasil:
    helonoia_monster.svg      -> latar transparan (dipakai di Canva)
    helonoia_monster_bg.svg   -> dengan latar gelap #120B1E (untuk preview)
    helonoia_monster.png      -> PNG transparan 1200 px (hanya jika `cairosvg` terpasang)
    helonoia_logo.svg         -> logo lengkap 500 x 500 (monster + tulisan) dengan latar gelap
    helonoia_logo_transparent.svg -> logo lengkap dengan latar transparan

Semua koordinat memakai kanvas kerja 512 x 512. Bagian yang keluar dari kanvas
(garis lambaian di kiri) tetap terlihat karena viewBox diatur di VIEWBOX.

Susunan logo (kanvas 500 x 500 px) – dipakai oleh build_logo() dan di Canva (Page 6):
    Monster  : W 392.4 px, X 28.3, Y 18.3 (layer paling belakang)
    Tulisan  : "HELONOIA", font Syne Bold 46, letter spacing 60 (= 0.06 em), rata tengah,
               kotak teks W 460, X 20, Y 367 (garis dasar huruf di y = 414)
               "HELO" = #F4EFFF (dari "halo", sapaan), "NOIA" = #B26BFF (dari "paranoia")
    Latar    : #120B1E

Di file logo, tulisan sudah diubah menjadi path (outline Syne Bold, lisensi SIL OFL 1.1),
jadi tampil benar tanpa font terpasang.
"""

import math

# ---------------------------------------------------------------------------
# Palet warna
# ---------------------------------------------------------------------------
BG    = "#120B1E"   # latar gelap
VIO   = "#B26BFF"   # ungu badan
SHADE = "#9A57F0"   # bayangan sisi kanan badan
DEEP  = "#7C3FD6"   # ungu tua (kaki, kantung mata, garis kelopak)
BELLY = "#CDA6FF"   # perut
LIME  = "#C6FF3D"   # tanduk & garis lambaian
WHITE = "#F4EFFF"   # mata, gigi, kuku kaki, keringat
INK   = "#0B0712"   # pupil, alis, mulut

# Bingkai SVG (hasil auto-fit saat desain; bounding box karakter + padding 6%)
VIEWBOX = "-78.7 -32.7 591.4 591.4"


def P(x, y):
    """Format satu titik untuk atribut path SVG."""
    return f"{x:.1f} {y:.1f}"


def svg(inner, vb=VIEWBOX, bg=False):
    b = f'<rect x="-500" y="-500" width="2000" height="2000" fill="{BG}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
            f'width="1000" height="1000">{b}{inner}</svg>')


# ---------------------------------------------------------------------------
# Cakar "talon" – melengkung ke dalam (sesuai sketsa di Page 6)
# ---------------------------------------------------------------------------
TALON_THETA = 115   # besar lengkungan tiap cakar (derajat)
TALON_STEPS = 28    # jumlah titik sampel sepanjang cakar


def talon_finger(bx, by, ang, length, w, c, sg=1, theta=None, N=TALON_STEPS):
    """Cakar berbentuk kait: garis tengahnya busur yang berputar `theta` derajat,
    lebarnya menyempit sampai ujung runcing. sg=+1 melengkung searah jarum jam."""
    th = TALON_THETA if theta is None else theta
    ds = length / N
    x, y = bx, by
    L, R = [], []
    for i in range(N + 1):
        t = i / N
        a = math.radians(ang + sg * th * t)
        hw = (w / 2) * (1 - t) ** 0.85
        px, py = -math.sin(a), math.cos(a)
        L.append((x + px * hw, y + py * hw))
        R.append((x - px * hw, y - py * hw))
        am = math.radians(ang + sg * th * (t + 0.5 / N))
        x += math.cos(am) * ds
        y += math.sin(am) * ds
    pts = L + R[::-1]
    return f'<path d="M ' + " L ".join(P(*q) for q in pts) + f' Z" fill="{c}"/>'


def talon_edge(bx, by, ang, length, w, sg, side, tq, N=TALON_STEPS):
    """Satu titik di tepi kiri (side=+1) / kanan (side=-1) cakar pada posisi tq (0..1)."""
    ds = length / N
    x, y = bx, by
    for i in range(N + 1):
        t = i / N
        a = math.radians(ang + sg * TALON_THETA * t)
        if t >= tq:
            hw = (w / 2) * (1 - t) ** 0.85
            px, py = -math.sin(a), math.cos(a)
            return (x + side * px * hw, y + side * py * hw)
        am = math.radians(ang + sg * TALON_THETA * (t + 0.5 / N))
        x += math.cos(am) * ds
        y += math.sin(am) * ds
    return (x, y)


def convex_hull(pts):
    """Convex hull (monotone chain) – dipakai untuk telapak supaya lengan menyatu mulus ke cakar."""
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


# ---------------------------------------------------------------------------
# Tangan: lengan yang melebar langsung menjadi 4 cakar (tanpa bulatan telapak)
# ---------------------------------------------------------------------------
CLAW_LENGTHS = (40, 48, 50, 42)   # panjang dasar 4 cakar (dikali 1.15 saat digambar)
CLAW_W       = 24                 # lebar pangkal cakar
CLAW_R       = 16                 # jarak pangkal cakar dari pusat tangan
CHORD_REL    = (-42, -14, 14, 42) # arah akhir tiap cakar relatif ke arah kipas
POS_REL      = (-56, -20, 20, 56) # posisi pangkal tiap cakar relatif ke arah kipas
ARM_W        = 36                 # lebar lengan
BODY_C       = (256, 290)         # pusat badan: semua cakar melengkung ke arah ini


def body_fingers(fan_dir, hand_c):
    """Susunan 4 cakar untuk satu tangan, simetris terhadap arah kipas `fan_dir`.
    Arah lengkung dipilih sekali per tangan supaya semua cakar melengkung ke arah badan."""
    d = math.radians(fan_dir)
    px, py = -math.sin(d), math.cos(d)
    sg = 1 if px * (BODY_C[0] - hand_c[0]) + py * (BODY_C[1] - hand_c[1]) > 0 else -1
    out = []
    for ln, ch, ps in zip(CLAW_LENGTHS, CHORD_REL, POS_REL):
        # pangkal dimiringkan balik ~42% dari lengkungan agar ujung cakar jatuh di arah kipas
        out.append((fan_dir + ps, fan_dir + ch - sg * TALON_THETA * 0.42, ln, sg))
    return out


def claw_hand(c, shoulder, center, fingers, radius=CLAW_R, fw=CLAW_W, arm_w=ARM_W):
    sx, sy = shoulder
    cx, cy = center
    dx, dy = sx - cx, sy - cy
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    hw = arm_w / 2
    SL = (sx + px * hw, sy + py * hw)
    SR = (sx - px * hw, sy - py * hw)

    claws = ""
    hull_pts = [SL, SR]
    for pos, ang, ln, sg in fingers:
        a = math.radians(pos)
        bx, by = cx + math.cos(a) * radius, cy + math.sin(a) * radius
        claws += talon_finger(bx, by, ang, ln * 1.15, fw, c, sg=sg)
        # telapak = convex hull lengan + pangkal semua cakar -> tidak ada lekukan/tonjolan
        for side in (+1, -1):
            for tq in (0.0, 0.08, 0.16, 0.24):
                hull_pts.append(talon_edge(bx, by, ang, ln * 1.15, fw, sg, side, tq))

    hull = convex_hull(hull_pts)
    palm = "M " + " L ".join(P(*q) for q in hull) + " Z"
    shoulder_joint = f'<circle cx="{sx}" cy="{sy}" r="{hw}" fill="{c}"/>'  # tertutup badan
    return shoulder_joint + f'<path d="{palm}" fill="{c}"/>' + claws


def arm_dir(shoulder, hand_c):
    """Arah lengan (derajat) dari bahu ke pusat tangan."""
    return math.degrees(math.atan2(hand_c[1] - shoulder[1], hand_c[0] - shoulder[0]))


# Kedua tangan memakai bentuk yang persis sama: kipas cakar searah dengan lengan,
# jadi lengan melebar simetris ke cakar terluar. Yang berbeda hanya rotasinya.
WAVE_SHOULDER, WAVE_HAND = (142, 300), (92, 180)
SIDE_SHOULDER, SIDE_HAND = (380, 298), (428, 358)


def wave_hand(c):
    """Tangan kiri yang melambai: lengan terangkat diagonal, cakar melengkung ke arah badan."""
    return claw_hand(c, WAVE_SHOULDER, WAVE_HAND,
                     body_fingers(arm_dir(WAVE_SHOULDER, WAVE_HAND), WAVE_HAND))


def side_hand(c):
    """Tangan kanan yang menggantung."""
    return claw_hand(c, SIDE_SHOULDER, SIDE_HAND,
                     body_fingers(arm_dir(SIDE_SHOULDER, SIDE_HAND), SIDE_HAND))


# ---------------------------------------------------------------------------
# Badan, tanduk, kaki, detail
# ---------------------------------------------------------------------------
def drop(cx, cy, s, c):
    """Tetes keringat."""
    return (f'<path d="M {cx} {cy-34*s} C {cx+6*s} {cy-18*s} {cx+22*s} {cy-2*s} {cx+22*s} {cy+12*s} '
            f'C {cx+22*s} {cy+26*s} {cx+12*s} {cy+34*s} {cx} {cy+34*s} '
            f'C {cx-12*s} {cy+34*s} {cx-22*s} {cy+26*s} {cx-22*s} {cy+12*s} '
            f'C {cx-22*s} {cy-2*s} {cx-6*s} {cy-18*s} {cx} {cy-34*s} Z" fill="{c}"/>')


# Badan bentuk "pir"
BODY = ("M 256 104 C 330 104 378 160 386 236 C 394 300 410 360 400 404 C 392 436 360 448 320 448 "
        "L 192 448 C 152 448 120 436 112 404 C 102 360 118 300 126 236 C 134 160 182 104 256 104 Z")
# Bayangan sisi kanan
SHADE_P = ("M 318 116 C 362 140 382 190 386 236 C 394 300 410 360 400 404 C 392 436 360 448 320 448 "
           "L 300 448 C 344 440 370 418 374 384 C 382 320 366 190 318 116 Z")

# Tanduk: bentuk dari sketsa Page 4 (pangkal tebal, ujung runcing ke luar),
# ditempatkan di posisi tanduk desain awal. Tanduk kanan = cermin tanduk kiri.
HORN_LOCAL = ("M 19 10 C 0 60 -5 150 30 205 C 55 245 100 280 150 276 "
              "C 185 272 192 236 178 214 C 150 168 90 130 50 90 C 32 70 22 40 19 10 Z")
HORN_T = "translate(170 48.7) scale(0.326)"
HORNS = (f'<g transform="{HORN_T}"><path d="{HORN_LOCAL}" fill="{LIME}"/></g>'
         f'<g transform="translate(512 0) scale(-1 1)"><g transform="{HORN_T}">'
         f'<path d="{HORN_LOCAL}" fill="{LIME}"/></g></g>')

TUFT = f'<path d="M 230 112 L 240 82 L 252 106 L 262 76 L 272 104 L 284 84 L 288 114 Z" fill="{VIO}"/>'
BELLY_P = f'<ellipse cx="256" cy="398" rx="86" ry="48" fill="{BELLY}"/>'
FEET = ''.join(
    f'<rect x="{x}" y="424" width="70" height="42" rx="21" fill="{DEEP}"/>'
    + ''.join(f'<path d="M {x+dx-6} 458 L {x+dx} 474 L {x+dx+6} 458 Z" fill="{WHITE}"/>'
              for dx in (16, 35, 54))
    for x in (168, 274))

# Garis gerak lambaian
MOTION = (f'<g fill="none" stroke="{LIME}" stroke-width="13" stroke-linecap="round">'
          f'<path d="M 14 252 Q -6 212 6 170"/><path d="M -24 230 Q -50 184 -34 136"/></g>')


# ---------------------------------------------------------------------------
# Wajah – ekspresi "Curiga"
# ---------------------------------------------------------------------------
def pupils(dx, dy, r):
    return (f'<circle cx="{212+dx}" cy="{226+dy}" r="{r}" fill="{INK}"/>'
            f'<circle cx="{300+dx}" cy="{226+dy}" r="{r}" fill="{INK}"/>'
            f'<circle cx="{212+dx-r*0.35:.1f}" cy="{226+dy-r*0.35:.1f}" r="{max(2.5, r*0.3):.1f}" fill="{WHITE}"/>'
            f'<circle cx="{300+dx-r*0.35:.1f}" cy="{226+dy-r*0.35:.1f}" r="{max(2.5, r*0.3):.1f}" fill="{WHITE}"/>')


EYE_WHITES = (f'<ellipse cx="212" cy="226" rx="36" ry="42" fill="{WHITE}"/>'
              f'<ellipse cx="300" cy="226" rx="36" ry="42" fill="{WHITE}"/>')
# Kelopak mata setengah tertutup (warna badan) + garis kelopak
LIDS = (f'<path d="M 172 226 Q 176 180 212 182 Q 248 180 252 226 Z" fill="{VIO}"/>'
        f'<path d="M 260 226 Q 264 180 300 182 Q 336 180 340 226 Z" fill="{VIO}"/>'
        f'<g stroke="{DEEP}" stroke-width="6" stroke-linecap="round">'
        f'<line x1="176" y1="226" x2="248" y2="226"/><line x1="264" y1="226" x2="336" y2="226"/></g>')
# Kantung mata
BAGS = (f'<g fill="none" stroke="{DEEP}" stroke-width="6" stroke-linecap="round">'
        f'<path d="M 188 276 Q 212 288 236 276"/><path d="M 276 276 Q 300 288 324 276"/></g>')
# Alis datar (kiri & kanan sama, cermin)
BROWS = (f'<g stroke="{INK}" stroke-width="11" stroke-linecap="round" fill="none">'
         f'<path d="M 180 186 Q 206 194 234 192"/><path d="M 278 192 Q 306 194 332 186"/></g>')
# Senyum miring + satu taring
FANG = f'<path d="M 268 318 L 277 344 L 290 314 Z" fill="{WHITE}"/>'
SMIRK = (f'<path d="M 214 324 Q 256 336 298 310" fill="none" stroke="{INK}" '
         f'stroke-width="10" stroke-linecap="round"/>')

FACE_CURIGA = (EYE_WHITES + pupils(20, 16, 12) + LIDS + BAGS + BROWS + FANG + SMIRK
               + drop(372, 156, 0.9, WHITE))


# ---------------------------------------------------------------------------
# Tulisan "HELONOIA" – outline Syne Bold (SIL OFL 1.1), satuan font 1000/em.
# Disimpan sebagai path supaya logo tampil benar tanpa font terpasang.
# ---------------------------------------------------------------------------
GLYPHS = {
    "H": (895, "M194 380H707V269H194ZM685 647H818V0H685ZM77 647H210V0H77Z"),
    "E": (769, "M210 270V111H709V0H77V647H708V536H210V375H618V270Z"),
    "L": (687, "M210 647V111H640V0H77V647Z"),
    "O": (924, "M462 -13Q333 -13 242 28Q150 68 102 143Q53 218 53 323Q53 429 102 504Q150 579 242 620Q333 660 462 660Q592 660 683 620Q774 579 822 504Q871 429 871 323Q871 218 822 143Q774 68 683 28Q592 -13 462 -13ZM462 102Q542 102 602 126Q663 150 698 199Q732 248 732 323Q732 398 698 447Q663 496 602 520Q542 545 462 545Q383 545 321 520Q259 496 224 447Q189 398 189 323Q189 248 224 199Q259 150 321 126Q383 102 462 102Z"),
    "N": (901, "M733 132 691 115V647H824V0H691L168 511L210 528V0H77V647H210Z"),
    "I": (324, "M96 647H229V0H96Z"),
    "A": (789, "M178 141V252H606V141ZM17 0 321 647H465L772 0H627L361 583H425L161 0Z"),
}
WORD_SIZE = 46          # ukuran huruf (px)
WORD_TRACK = 0.06       # letter spacing Canva 60 = 0.06 em
WORD_BASELINE = 414     # garis dasar huruf (kotak teks Canva Y 367, line-height 1.4)
MONSTER_BOX = (28.3, 18.3, 392.4)   # X, Y, W monster di kanvas 500 x 500


def wordmark():
    """Tulisan HELONOIA sebagai path, rata tengah di x = 250."""
    k = WORD_SIZE / 1000
    gap = WORD_TRACK * WORD_SIZE
    total = sum(GLYPHS[ch][0] for ch in "HELONOIA") * k + gap * 7
    x = 250 - total / 2
    out = ""
    for i, ch in enumerate("HELONOIA"):
        adv, d = GLYPHS[ch]
        col = WHITE if i < 4 else VIO
        out += (f'<path transform="translate({x:.2f} {WORD_BASELINE}) scale({k} {-k})" '
                f'd="{d}" fill="{col}"/>')
        x += adv * k + gap
    return out


def build_logo():
    x, y, w = MONSTER_BOX
    monster = (f'<svg x="{x}" y="{y}" width="{w}" height="{w}" viewBox="{VIEWBOX}">'
               f'{build_monster()}</svg>')
    return monster + wordmark()


def logo_svg(bg=False):
    b = f'<rect width="500" height="500" fill="{BG}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" '
            f'width="1000" height="1000">{b}{build_logo()}</svg>')


# ---------------------------------------------------------------------------
# Susun & simpan
# ---------------------------------------------------------------------------
def build_monster():
    return (FEET
            + f'<path d="{BODY}" fill="{VIO}"/>'
            + f'<path d="{SHADE_P}" fill="{SHADE}"/>'
            + BELLY_P + HORNS + TUFT
            + side_hand(VIO) + wave_hand(VIO)
            + MOTION
            + FACE_CURIGA)


if __name__ == "__main__":
    inner = build_monster()
    with open("helonoia_monster.svg", "w") as f:
        f.write(svg(inner))
    with open("helonoia_monster_bg.svg", "w") as f:
        f.write(svg(inner, bg=True))
    with open("helonoia_logo.svg", "w") as f:
        f.write(logo_svg(bg=True))
    with open("helonoia_logo_transparent.svg", "w") as f:
        f.write(logo_svg())
    print("Tersimpan: helonoia_monster.svg, helonoia_monster_bg.svg, "
          "helonoia_logo.svg, helonoia_logo_transparent.svg")
    try:
        import cairosvg  # opsional: pip install cairosvg
        cairosvg.svg2png(url="helonoia_monster.svg", write_to="helonoia_monster.png",
                         output_width=1200, output_height=1200)
        cairosvg.svg2png(url="helonoia_logo.svg", write_to="helonoia_logo.png",
                         output_width=1000, output_height=1000)
        print("Tersimpan: helonoia_monster.png, helonoia_logo.png")
    except ImportError:
        print("(PNG dilewati – pasang `cairosvg` jika ingin ekspor PNG)")
