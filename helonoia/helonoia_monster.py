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
    Tulisan  : "HELONOIA", font Fredoka Bold 72, letter spacing 40 (= 0.04 em), rata tengah,
               kotak teks W 460, X 20, Y 371.0 (garis dasar huruf di y = 448)
               "HELO" = #F4EFFF (dari "halo", sapaan), "NOIA" = #B26BFF (dari "paranoia")
    Latar    : #120B1E

Di file logo, tulisan sudah diubah menjadi path (outline Fredoka Bold, lisensi SIL OFL 1.1),
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
# Tulisan "HELONOIA" – outline Fredoka Bold (SIL OFL 1.1), satuan font 1000/em.
# Disimpan sebagai path supaya logo tampil benar tanpa font terpasang.
# ---------------------------------------------------------------------------
GLYPHS = {
    "H": (650, "M530 -8Q485 -8 466 6Q447 19 443 40Q439 62 439 84V600Q439 622 443 643Q447 664 466 678Q485 691 531 691Q577 691 596 678Q614 664 618 643Q622 622 622 599V83Q622 61 618 40Q614 19 595 6Q576 -8 530 -8ZM119 -8Q74 -8 55 6Q36 19 32 40Q28 62 28 84V600Q28 622 32 643Q36 664 55 678Q74 691 120 691Q166 691 184 678Q203 664 207 643Q211 622 211 599V83Q211 61 207 40Q203 19 184 6Q165 -8 119 -8ZM195 263V419H455V263Z"),
    "E": (603, "M129 -9Q84 -9 65 4Q46 18 42 40Q38 61 38 83V600Q38 652 58 672Q79 691 132 691H498Q521 691 542 687Q562 683 576 664Q589 645 589 599Q589 554 576 535Q562 516 541 512Q520 508 497 508H221V419H406Q429 419 447 416Q465 412 476 396Q487 380 487 340Q487 302 476 286Q465 269 446 266Q427 263 404 263H221V174H498Q521 174 542 170Q562 166 576 147Q589 128 589 82Q589 37 576 18Q562 -1 541 -5Q520 -9 497 -9Z"),
    "L": (569, "M141 -9Q96 -9 77 4Q58 18 54 40Q50 61 50 83V600Q50 622 54 643Q58 664 77 678Q96 691 142 691Q188 691 206 678Q225 664 229 643Q233 622 233 599V147H477Q496 147 514 144Q531 141 542 124Q554 108 554 69Q554 31 542 14Q530 -2 512 -6Q495 -9 476 -9Z"),
    "O": (721, "M365 -20Q292 -20 228 8Q165 35 117 84Q69 133 42 198Q14 262 14 335Q14 411 40 477Q67 543 114 593Q161 643 224 671Q286 699 357 699Q430 699 494 672Q557 644 605 595Q653 546 680 480Q707 415 707 339Q707 265 680 200Q654 135 606 86Q559 36 498 8Q436 -20 365 -20ZM360 163Q394 163 424 176Q454 190 476 214Q499 237 512 270Q524 302 524 339Q524 376 511 408Q498 440 476 464Q453 489 424 502Q394 516 361 516Q327 516 298 502Q268 489 246 464Q223 440 210 408Q197 376 197 339Q197 303 210 271Q223 239 246 214Q268 190 298 176Q327 163 360 163Z"),
    "N": (670, "M118 -9Q74 -9 55 4Q36 18 32 39Q28 60 28 83V602Q28 624 32 644Q36 664 56 677Q75 690 120 690Q164 690 180 679Q196 668 209 651L459 315V602Q459 624 464 644Q468 664 487 677Q506 690 551 690Q597 690 616 676Q634 663 638 642Q642 621 642 598V82Q642 60 638 39Q634 18 615 4Q596 -9 550 -9Q516 -9 498 -4Q481 2 469 18L210 360V82Q210 60 206 39Q202 18 183 4Q164 -9 118 -9Z"),
    "I": (239, "M119 -9Q74 -9 55 4Q36 18 32 40Q28 61 28 83V600Q28 622 32 643Q36 664 55 678Q74 691 120 691Q166 691 184 678Q203 664 207 643Q211 622 211 599V82Q211 60 207 39Q203 18 184 4Q165 -9 119 -9Z"),
    "A": (711, "M690 118Q705 88 706 67Q707 46 693 30Q679 14 648 -2Q600 -25 574 -16Q548 -8 525 41L355 389L187 40Q163 -7 137 -16Q111 -24 64 -1Q33 14 18 30Q4 46 5 67Q6 88 21 118L272 638Q284 662 308 676Q331 691 356 691Q374 691 390 684Q405 678 418 666Q431 654 439 637ZM197 136 273 292H438L514 136Z"),
}
WORD_SIZE = 72          # ukuran huruf (px)
WORD_TRACK = 0.04       # letter spacing Canva 40 = 0.04 em
WORD_BASELINE = 448     # garis dasar huruf (kotak teks Canva Y 371.0, line-height 1.4)
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
