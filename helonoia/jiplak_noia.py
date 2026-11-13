"""
HELONOIA – penjiplak karakter Noia (gambar sumber -> bagian-bagian vektor)
==========================================================================

Membaca sumber/noia.webp lalu menulis noia_bagian.json: path vektor tiap bagian tubuh
(kepala, lengan, badan, kaki, ekor) yang dipakai helonoia_karakter.py.

Hanya perlu dijalankan ulang kalau gambar sumbernya diganti:

    pip install opencv-python-headless scipy numpy
    python3 jiplak_noia.py            # tulis noia_bagian.json
    python3 jiplak_noia.py --cek      # + simpan gambar pemeriksaan pembagian bagian

Cara kerja
----------
1. Piksel dipilah: latar (transparan), tinta (garis hitam), dan warna.
2. Warna disederhanakan menjadi beberapa warna datar (k-means).
3. Area warna yang dikurung garis tinta jadi "pulau". Tiap pulau dimasukkan ke satu bagian
   tubuh lewat titik benih di BENIH; pulau besar yang memuat beberapa bagian sekaligus
   (kepala + badan + lengan kanan) dipotong dengan garis di POTONG.
4. Garis tinta diberikan ke bagian terdepan yang menyentuhnya.
5. Tiap bagian dijiplak jadi path halus: siluet, area tiap warna, lalu tinta di atasnya.
"""

import argparse
import json
import os

import cv2
import numpy as np
from scipy import ndimage

DI_SINI = os.path.dirname(os.path.abspath(__file__))
SUMBER = os.path.join(DI_SINI, "sumber", "noia.webp")
KELUARAN = os.path.join(DI_SINI, "noia_bagian.json")

JUMLAH_WARNA = 10
BATAS_TINTA = 118       # piksel dengan kanal terterang di bawah ini = tinta
SKALA = 3               # penghalusan: mask diperbesar sebelum dijiplak
EPS = 0.9               # toleransi penyederhanaan titik (piksel sumber)

# Urutan dari depan ke belakang (untuk pembagian tinta). Urutan gambar = kebalikannya.
URUTAN = ["kepala", "lengan_n", "lengan_k", "badan", "kaki_k", "ekor"]

# Titik benih (x, y) di gambar sumber: pulau warna yang memuat titik itu masuk ke bagian tsb.
BENIH = {
    "kepala":   [(700, 300), (840, 160), (490, 210), (724, 402), (552, 431), (783, 336), (700, 469),
                 (622, 480)],
    "lengan_n": [(1130, 482), (980, 459), (1106, 596), (1207, 637)],
    "lengan_k": [(391, 526), (559, 573), (453, 581), (339, 629), (415, 592), (319, 677)],
    "badan":    [(700, 650), (926, 935), (1048, 923), (1107, 911)],
    "kaki_k":   [(546, 786), (373, 870), (427, 883), (503, 887)],
    "ekor":     [(977, 712)],
}

# Pulau utama memuat kepala, badan, dan pangkal lengan kanan tanpa garis pemisah. Potongannya:
#   kepala   = di atas garis rahang (GARIS_RAHANG)
#   lengan_n = cakram di sekitar bahu + semua yang ada di kanan bahu dan di atas ketiak.
#              Potongan berbentuk lingkaran supaya lengan bisa diputar di bahu tanpa celah.
GARIS_RAHANG = [(380, 470), (470, 452), (500, 492), (560, 513), (640, 523), (700, 517), (760, 493),
                (800, 468), (850, 438), (900, 412), (952, 398), (1100, 330)]
BAHU_N = (838, 515)
RADIUS_BAHU = 66
BATAS_LENGAN_N = [(838, 380), (1300, 380), (1300, 640), (905, 640), (838, 585)]

# Area wajah (mata, alis, mulut) yang dikosongkan untuk versi kepala "polos",
# tempat ekspresi lain digambar.
WAJAH = [(506, 360), (560, 372), (640, 350), (700, 328), (790, 296), (838, 310), (834, 380),
         (800, 440), (730, 470), (726, 502), (600, 505), (530, 474), (512, 420)]


def baca():
    im = cv2.imread(SUMBER, cv2.IMREAD_UNCHANGED)
    bgr, alpha = im[:, :, :3], im[:, :, 3]
    depan = alpha > 128
    terang = bgr.max(axis=2).astype(np.float32)
    tinta = depan & (terang < BATAS_TINTA)
    return bgr, depan, tinta


def sederhanakan_warna(bgr, depan, tinta):
    """Kembalikan (peta kelas warna, daftar warna hex). Piksel di tepi garis tinta (anti-alias)
    mengambil kelas piksel bersih terdekat supaya tidak muncul pinggiran gelap."""
    bgr = cv2.medianBlur(bgr, 7)       # buang bintik & gradasi halus sebelum warna dipilah
    warna = depan & ~tinta
    tepi = cv2.dilate(tinta.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & warna
    bersih = warna & ~tepi
    contoh = bgr[bersih].astype(np.float32)
    rng = np.random.RandomState(1)
    contoh = contoh[rng.choice(len(contoh), min(60000, len(contoh)), replace=False)]
    cv2.setRNGSeed(1)
    _, _, pusat = cv2.kmeans(contoh, JUMLAH_WARNA, None,
                             (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.2),
                             5, cv2.KMEANS_PP_CENTERS)
    px = bgr.reshape(-1, 1, 3).astype(np.float32)
    kelas = np.argmin(((px - pusat[None]) ** 2).sum(axis=2), axis=1).reshape(bgr.shape[:2])
    # piksel tepi & tinta -> kelas piksel bersih terdekat
    _, idx = ndimage.distance_transform_edt(~bersih, return_indices=True)
    kelas = kelas[idx[0], idx[1]]
    kelas = cv2.medianBlur(kelas.astype(np.uint8), 9).astype(int)
    hexs = ["#%02X%02X%02X" % (int(c[2]), int(c[1]), int(c[0])) for c in pusat]
    return kelas, hexs


def poligon(shape, pts):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    return m.astype(bool)


def bagi(depan, tinta):
    """Kembalikan peta bagian (indeks ke URUTAN, -1 = bukan apa-apa) untuk piksel warna & tinta."""
    h, w = depan.shape
    warna = depan & ~tinta
    n, pulau = cv2.connectedComponents(warna.astype(np.uint8), connectivity=4)
    peta = np.full((h, w), -1, int)
    utama = pulau[650, 700]
    for i, nama in enumerate(URUTAN):
        for x, y in BENIH[nama]:
            if pulau[y, x] != utama and pulau[y, x] != 0:
                peta[pulau == pulau[y, x]] = i
    # potong pulau utama
    u = pulau == utama
    yy, xx = np.mgrid[0:h, 0:w]
    atas_rahang = poligon((h, w), GARIS_RAHANG + [(1536, 330), (1536, 0), (0, 0), (0, 470)])
    cakram = (xx - BAHU_N[0]) ** 2 + (yy - BAHU_N[1]) ** 2 <= RADIUS_BAHU ** 2
    lengan = (cakram | poligon((h, w), BATAS_LENGAN_N)) & ~atas_rahang
    peta[u] = URUTAN.index("badan")
    peta[u & lengan] = URUTAN.index("lengan_n")
    peta[u & atas_rahang] = URUTAN.index("kepala")
    # pulau kecil tanpa benih -> ikut bagian terdekat
    belum = warna & (peta < 0)
    _, idx = ndimage.distance_transform_edt(~(peta >= 0), return_indices=True)
    peta[belum] = peta[idx[0], idx[1]][belum]
    # tinta -> bagian terdepan yang warnanya ada dalam jarak selebar garis
    peta_tinta = np.full((h, w), -1, int)
    for i in range(len(URUTAN)):
        dekat = ndimage.distance_transform_edt(~(warna & (peta == i))) <= 15
        peta_tinta[tinta & dekat & (peta_tinta < 0)] = i
    sisa = tinta & (peta_tinta < 0)
    _, idx = ndimage.distance_transform_edt(~(peta_tinta >= 0), return_indices=True)
    peta_tinta[sisa] = peta_tinta[idx[0], idx[1]][sisa]
    peta[tinta] = peta_tinta[tinta]
    return peta


# ---------------------------------------------------------------------------
# Jiplak: mask -> path halus
# ---------------------------------------------------------------------------
def halus(pts):
    """Poligon tertutup -> path kurva Bezier; sudut tajam (ujung cakar, tanduk) dipertahankan."""
    n = len(pts)
    if n < 3:
        return ""
    P = np.asarray(pts, float)
    masuk = P - np.roll(P, 1, axis=0)
    keluar = np.roll(P, -1, axis=0) - P
    lm = np.linalg.norm(masuk, axis=1) + 1e-9
    lk = np.linalg.norm(keluar, axis=1) + 1e-9
    um, uk = masuk / lm[:, None], keluar / lk[:, None]
    sudut = np.degrees(np.arccos(np.clip((um * uk).sum(axis=1), -1, 1)))
    t = um + uk
    t /= (np.linalg.norm(t, axis=1) + 1e-9)[:, None]
    tajam = (sudut > 62) & (lm > 2.5) & (lk > 2.5)   # jangan anggap gerigi kecil sebagai sudut
    t_keluar = np.where(tajam[:, None], uk, t)
    t_masuk = np.where(tajam[:, None], um, t)
    d = ["M %.1f %.1f" % tuple(P[0])]
    for i in range(n):
        j = (i + 1) % n
        L = lk[i] / 3
        c1 = P[i] + t_keluar[i] * L
        c2 = P[j] - t_masuk[j] * L
        d.append("C %.1f %.1f %.1f %.1f %.1f %.1f" % (c1[0], c1[1], c2[0], c2[1], P[j][0], P[j][1]))
    return " ".join(d) + " Z"


def jiplak(mask, luas_min=30):
    """Mask (bool / float 0..1) -> path SVG (subpath lubang ikut; pakai fill-rule evenodd)."""
    m = cv2.resize(mask.astype(np.float32), None, fx=SKALA, fy=SKALA, interpolation=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(m, (0, 0), 2.2)
    kontur, _ = cv2.findContours((m > 0.5).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    for k in kontur:
        if cv2.contourArea(k) < luas_min * SKALA * SKALA:
            continue
        k = cv2.approxPolyDP(k, EPS * SKALA, True).reshape(-1, 2)
        out.append(halus((k + 0.5) / SKALA - 0.5))
    return " ".join(x for x in out if x)


def jiplak_bagian(m_bagian, kelas, tinta, hexs, kosongkan=None, m_depan=None):
    """Satu bagian -> dict {siluet, dasar, lapis: [[warna, path]], tinta}.
    m_depan = mask bagian-bagian di depannya: siluet dijorokkan 5 px ke bawahnya supaya
    sambungan tanpa garis tinta (leher, bahu) tidak bercelah."""
    m_tinta = tinta & m_bagian
    m_warna = m_bagian & ~tinta
    if kosongkan is not None:
        m_tinta = m_tinta & ~kosongkan
    luas = [(int((m_warna & (kelas == c)).sum()), c) for c in range(len(hexs))]
    luas = sorted([x for x in luas if x[0] > 30], reverse=True)
    dasar = luas[0][1]
    if kosongkan is not None:
        kelas = kelas.copy()
        kelas[kosongkan] = dasar
    siluet = ndimage.binary_fill_holes(m_bagian)
    siluet_luar = siluet
    if m_depan is not None:
        lebar = cv2.dilate(siluet.astype(np.uint8), np.ones((11, 11), np.uint8)).astype(bool)
        siluet_luar = siluet | (lebar & m_depan)
    lapis = []
    inti = np.ones((3, 3), np.uint8)
    for _, c in luas[1:]:
        m = cv2.dilate((siluet & (kelas == c)).astype(np.uint8), inti)   # melebar 1 px: tak ada celah
        d = jiplak(m.astype(bool) & siluet)
        if d:
            lapis.append([hexs[c], d])
    return {"siluet": jiplak(siluet_luar), "dasar": hexs[dasar], "lapis": lapis, "tinta": jiplak(m_tinta, 6)}


def main():
    ap = argparse.ArgumentParser(description="Jiplak sumber/noia.webp menjadi noia_bagian.json.")
    ap.add_argument("--cek", metavar="FILE", nargs="?", const="cek_bagian.png",
                    help="simpan gambar pemeriksaan pembagian bagian")
    a = ap.parse_args()

    bgr, depan, tinta = baca()
    kelas, hexs = sederhanakan_warna(bgr, depan, tinta)
    peta = bagi(depan, tinta)

    if a.cek:
        rng = np.random.RandomState(4)
        palet = rng.randint(60, 255, (len(URUTAN), 3))
        vis = np.full(bgr.shape, 255, np.uint8)
        for i in range(len(URUTAN)):
            vis[peta == i] = palet[i]
        vis[tinta] = (vis[tinta] * 0.35).astype(np.uint8)
        kuant = np.full(bgr.shape, 255, np.uint8)
        for c, hx in enumerate(hexs):
            kuant[depan & (kelas == c)] = (int(hx[5:7], 16), int(hx[3:5], 16), int(hx[1:3], 16))
        kuant[tinta] = 0
        cv2.imwrite(a.cek, np.hstack([vis[:, 250:1300], kuant[:, 250:1300]]))
        print("Tersimpan:", a.cek)

    h, w = depan.shape
    wajah = poligon((h, w), WAJAH)
    data = {"ukuran": [w, h], "urutan": URUTAN[::-1], "bagian": {}}
    for i, nama in enumerate(URUTAN):
        data["bagian"][nama] = jiplak_bagian(peta == i, kelas, tinta, hexs,
                                             m_depan=(peta >= 0) & (peta < i))
    data["bagian"]["kepala_polos"] = jiplak_bagian(peta == URUTAN.index("kepala"), kelas, tinta, hexs, wajah)
    with open(KELUARAN, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("Tersimpan:", KELUARAN, "(%d KB)" % (os.path.getsize(KELUARAN) // 1024))


if __name__ == "__main__":
    main()
