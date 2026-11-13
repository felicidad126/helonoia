# Helonoia

Halaman perkenalan brand **Helonoia** beserta aset mereknya: maskot, logo, dan ikon.

| Folder / file | Isi |
| --- | --- |
| [`HTML/`](HTML/) | Halaman brand (`index.html`, `favicon.svg`, `logo.png`). Berdiri sendiri, tinggal disalin ke server. |
| [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md) | Panduan deploy ke server sendiri (aaPanel, Nginx manual, cPanel). |
| [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | Deploy otomatis `HTML/` ke server setiap push ke `main`. Cara menyiapkannya: [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md#update-otomatis-cicd). |
| [`helonoia/`](helonoia/) | Generator maskot dan logo (`helonoia_monster.py`) beserta hasilnya, dan generator gambar promosi (`generate.py`). |
| [`helonoia/karakter/`](helonoia/karakter/) | Karakter Noia (gaya kartun bercakar) dalam beberapa pose dan ekspresi, dari `helonoia_karakter.py`. |
| [`helonoia/ikon/`](helonoia/ikon/) | Ikon untuk bagian "Empat kebiasaan kami". |

## Halaman brand

Halaman di folder [`HTML/`](HTML/) mengenalkan brand **Helonoia** sebelum ada produk: arti nama (HELO dari "halo", NOIA dari "paranoia"), maskot monster ungu dan cerita tiap bagian tubuhnya, dan empat kebiasaan brand. Versi resminya ada di https://helonoia.com/ (aaPanel, lihat [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md)).

- Animasi penuh (abaikan setting reduced-motion): `HTML/?motion=full`
- Maskot dan tulisan HELONOIA di halaman ini dibuat dari [`helonoia/helonoia_monster.py`](helonoia/helonoia_monster.py), jadi bentuknya sama persis dengan logo. Bila logo berubah, potongan SVG di awal `<body>` perlu dibuat ulang dari generator itu.
- Semua warna diambil dari logo: Malam `#120B1E`, Ungu Noia `#B26BFF`, Ungu Tua `#7C3FD6`, Lilac `#CDA6FF`, Lime `#C6FF3D`, Putih Halo `#F4EFFF`. Palet dan huruf sengaja tidak ditampilkan di halaman publik; tempatnya di dokumen brand.
- Interaksi: mata maskot mengikuti kursor (di HP ia melirik ke sana kemari sendiri), tombol "Sapa balik" membuat maskot melambai dan menjawab.
- `canonical`, `og:url`, dan `og:image` mengarah ke `https://helonoia.com/`.
- Kontak (WhatsApp, Instagram, email) diisi di objek `KONTAK` pada skrip di bagian bawah `HTML/index.html`. Selama kosong, tombol kontak tidak ditampilkan.
- Bagian "Yang sudah bisa dilihat" menautkan ke katalog undangan digital di https://invitation.helonoia.net/.
- Font Fredoka (huruf logo) dan Plus Jakarta Sans dimuat dari Google Fonts, berlisensi SIL Open Font License 1.1.

## Maskot & logo

Jalankan dari dalam folder `helonoia/`:

```bash
cd helonoia && python3 helonoia_monster.py
```

| File | Isi |
| --- | --- |
| `helonoia_monster.svg` | Maskot, latar transparan |
| `helonoia_monster_bg.svg` / `.png` | Maskot, latar gelap `#120B1E` |
| `helonoia_logo.svg` / `.png` | Logo lengkap (maskot + tulisan), latar gelap |
| `helonoia_logo_transparent.svg` | Logo lengkap, latar transparan |

## Karakter Noia: pose & ekspresi

[`helonoia/helonoia_karakter.py`](helonoia/helonoia_karakter.py) menyusun karakter Noia sebagai SVG vektor dari bagian-bagian tubuh (kepala, kedua lengan, badan, kaki, ekor) yang dijiplak dari gambar sumber [`helonoia/sumber/noia.webp`](helonoia/sumber/noia.webp). Pose `siaga` dengan ekspresi `galak` sama dengan gambar sumber. Pose lain dibuat dengan memutar bagian-bagian itu di sendinya, dan ekspresi lain digambar di atas kepala yang wajahnya dikosongkan. Cukup Python 3.

```bash
cd helonoia && python3 helonoia_karakter.py            # 6 pose + lembar_pose.svg + lembar_ekspresi.svg
python3 helonoia_karakter.py -p melambai -e malu        # satu kombinasi
python3 helonoia_karakter.py -e kaget                   # kepala saja
python3 helonoia_karakter.py --semua                    # semua 60 kombinasi pose x ekspresi
python3 helonoia_karakter.py --daftar                   # daftar pose & ekspresi
```

| Pose (`-p`) | Tingkah laku | Ekspresi bawaan |
| --- | --- | --- |
| `siaga` | Kuda-kuda, cakar terbuka (gambar sumber) | `galak` |
| `melambai` | Lengan kanan terangkat, menyapa | `senang` |
| `sorak` | Kedua cakar terangkat sambil melompat | `tertawa` |
| `menerkam` | Cakar terangkat, badan condong | `galak` |
| `termenung` | Kepala miring | `bingung` |
| `lesu` | Bahu turun, kepala tertunduk | `ngantuk` |

Ekspresi (`-e`): `galak` (wajah asli sumber), `senang`, `curiga`, `kaget`, `sedih`, `ngantuk`, `tertawa`, `malu`, `bingung`, `jatuh_cinta`. Semua pose bisa dipasangkan dengan semua ekspresi. `-o file.svg` menentukan nama file, `--png` ikut mengekspor PNG (perlu `pip install cairosvg`).

Pose baru ditambah di `POSE` sebagai sudut putar tiap bagian, ekspresi baru di `EKSPRESI` sebagai bentuk mata, alis, mulut, dan efek. Karena tiap bagian kaku dan hanya diputar, pose terbatas pada gerakan lengan, kepala, ekor, dan seluruh badan; kaki kanan menyatu dengan badan.

| File | Isi |
| --- | --- |
| `helonoia/sumber/noia.webp` | Gambar sumber karakter |
| `helonoia/jiplak_noia.py` | Menjiplak gambar sumber menjadi `noia_bagian.json`. Hanya dijalankan ulang kalau gambar sumber diganti (perlu `pip install opencv-python-headless scipy numpy`) |
| `helonoia/noia_bagian.json` | Path vektor tiap bagian tubuh |
| `helonoia/karakter/` | Hasil: 6 pose dan dua lembar |

## Generator gambar vektor

[`helonoia/generate.py`](helonoia/generate.py) membuat gambar SVG siap pakai dari aset brand (maskot, tulisan HELONOIA, palet) plus judul bebas. Cukup Python 3, tanpa library tambahan. Hasil masuk ke `helonoia/hasil/` (tidak ikut di-commit).

```bash
cd helonoia && python3 generate.py -j "Halo, kami Helonoia" -s "Teliti sampai rewel"
```

| Format (`-f`) | Ukuran | Untuk |
| --- | --- | --- |
| `persegi` | 1080 × 1080 | Post Instagram 1:1 |
| `potret` | 1080 × 1350 | Post Instagram 4:5 |
| `story` | 1080 × 1920 | Story / Reels / status WhatsApp |
| `og` | 1200 × 630 | Pratinjau tautan (`og:image`) |
| `banner` | 1500 × 500 | Header X / banner web |
| `ikon` | 512 × 512 | Ikon aplikasi / foto profil (hanya maskot) |

Tanpa `-f` semua format dibuat. Opsi lain:

- `--ukuran 1600x900`: ukuran bebas (format melebar: teks kiri, maskot kanan; selain itu bertumpuk rata tengah).
- `-l gelap|terang|ungu|transparan`: warna latar (bawaan `gelap`).
- `-o file.svg`: nama file keluaran (untuk satu gambar).
- `--tanpa-maskot`, `--tanpa-logo`, `--tanpa-dekor`, `--seed N` (posisi kilau).
- `--font Fredoka.ttf`: ubah judul dan subjudul menjadi path supaya tampil sama tanpa font terpasang (perlu `pip install fonttools`). Tanpa opsi ini teks ditulis sebagai `<text>` Fredoka / Plus Jakarta Sans.
- `--png`: ekspor PNG juga (perlu `pip install cairosvg`).

Bentuk maskot dan tulisan HELONOIA diambil langsung dari `helonoia_monster.py`, jadi selalu sama dengan logo.

## Ikon kebiasaan

Grid 32×32, garis 2.4 dengan ujung dan sambungan membulat, dan `currentColor`, jadi warnanya mengikuti CSS induknya.

| File | Kebiasaan |
| --- | --- |
| `helonoia/ikon/menyapa-duluan.svg` | Menyapa duluan (pintu terbuka) |
| `helonoia/ikon/teliti-sampai-rewel.svg` | Teliti sampai rewel (tiga kali centang) |
| `helonoia/ikon/janji-kecil-saja.svg` | Janji kecil saja (kecil tapi pasti) |
| `helonoia/ikon/sedikit-aneh.svg` | Sedikit aneh (wajah monster) |
