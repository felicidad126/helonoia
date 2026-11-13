# Helonoia Vectorizer

Script CLI internal untuk mengubah **logo dan ilustrasi flat** (PNG, JPG, WebP, GIF, BMP, TIFF) menjadi SVG. Tool ini dibuat untuk file "kotor" yang biasa dikirim klien, seperti screenshot, JPEG kecil, atau foto dari WhatsApp. Hasilnya tetap berupa bidang warna yang bersih, dengan jumlah path dan warna sesedikit mungkin.

![Perbandingan: input JPEG, VTracer saja, dan Helonoia Vectorizer](contoh.png)

Bukan untuk foto atau gambar bergradasi: semua warna dijadikan bidang rata.

## Instalasi

Butuh Python 3.10 atau lebih baru.

```bash
pip install -r vectorizer/requirements.txt
```

`cairosvg` membutuhkan library Cairo di sistem. Di Ubuntu/Debian biasanya sudah terpasang (kalau belum: `apt install libcairo2`), di macOS pakai `brew install cairo`. Tanpa Cairo, output SVG tetap jalan, tetapi PDF/EPS/PNG dan skor kemiripan di laporan tidak tersedia.

## Pemakaian

```bash
python3 vectorizer/vectorize.py logo.jpg
```

Hasilnya `logo.svg` di sebelah file input, plus laporan singkat:

```
✓ logo.jpg → logo.svg
  ukuran 300×300, diproses 1200×1200
  palet 6 warna: #11091E 77.6% #B06BFC 13.4% #F5EEFE 3.1% #CDA6FF 2.8% #9C56EC 1.8% #C5FD38 1.2%
  70 path · 50 KB · PSNR 28.8 dB · ΔE rata-rata 2.8 · 1.4 s
```

PSNR makin tinggi makin mirip dengan input (di atas 30 dB sudah sangat mirip). ΔE adalah rata-rata selisih warna; di bawah 2 hampir tak terlihat mata.

Contoh lain:

```bash
# Satu folder sekaligus, hasil SVG + PDF ke folder lain
python3 vectorizer/vectorize.py masuk/ -o keluar/ -f svg,pdf

# Kunci warna ke palet brand Helonoia dan buang latarnya
python3 vectorizer/vectorize.py logo.png -p helonoia --remove-bg

# Logo teks: lubang huruf O/A ikut transparan
python3 vectorizer/vectorize.py wordmark.png --remove-bg semua

# Kunci ke warna brand klien
python3 vectorizer/vectorize.py logo.jpg -p "#1D3557,#E63946,#FFFFFF"

# Paksa tepat 3 warna
python3 vectorizer/vectorize.py logo.jpg -c 3
```

## Opsi

| Opsi | Fungsi |
| --- | --- |
| `-o`, `--output` | File `.svg` (untuk satu input) atau folder. Default: di sebelah file input. |
| `-c`, `--colors N` | Jumlah warna tetap. Default: ditentukan otomatis. |
| `-p`, `--palette` | Kunci warna ke palet: `helonoia` atau daftar hex dipisah koma. Setiap piksel diberi warna palet yang paling mirip. |
| `--max-colors N` | Batas warna untuk mode otomatis (default 16). |
| `-d`, `--detail` | `low`, `medium` (default), atau `high`. Lihat tabel di bawah. |
| `--stacking` | `stacked` (default): bentuk bertumpuk, aman dari celah tipis. `cutout`: bentuk saling memotong dan tidak bertumpuk, cocok untuk cutting/engraving. |
| `--remove-bg` | Buat latar transparan. Latar = warna yang menguasai pinggir gambar. Default (`tepi`): hanya area yang tersambung ke pinggir yang dibuang, jadi warna yang sama di dalam objek (mis. mulut maskot) tetap ada. `--remove-bg semua`: semua area berwarna latar dibuang, termasuk lubang huruf seperti O dan A. |
| `-f`, `--format` | `svg`, `pdf`, `eps`, `png`, boleh lebih dari satu (`svg,pdf`). |
| `--debug` | Simpan juga `*.debug.png`: gambar berwarna rata yang dilacak. Berguna untuk melihat dari mana sebuah warna atau bentuk berasal. |
| `-q`, `--quiet` | Tanpa laporan per file. |

| Detail | Cocok untuk |
| --- | --- |
| `low` | Input sangat kotor atau buram. Lebih sedikit warna, bentuk lebih halus, detail kecil hilang. |
| `medium` | Kebanyakan logo. |
| `high` | Input bersih dengan detail halus: garis tipis, warna yang mirip satu sama lain, sudut tajam. |

## Kalau hasilnya kurang pas

| Masalah | Coba |
| --- | --- |
| Muncul warna yang tidak ada di desain asli | `-c N` dengan jumlah warna yang benar, atau `-p` dengan warna asli |
| Detail kecil (pupil, garis tipis) hilang | `-d high` |
| Tepi masih bergerigi atau bernoda | `-d low` |
| Dua warna yang mirip tergabung | `-d high`, atau `-p` dengan kedua warna itu |
| Ada celah tipis antar bentuk di Illustrator | Pastikan `--stacking stacked` (default) |
| Lubang huruf (O, A, B) masih berwarna latar setelah `--remove-bg` | `--remove-bg semua` |

## Cara kerja

1. **Ukuran kerja.** Gambar kecil diperbesar (maksimal 4×) dan gambar besar diperkecil, supaya sisi terpanjang sekitar 2000 px.
2. **Denoise.** Non-local means membersihkan artefak JPEG tanpa mengaburkan tepi.
3. **Palet.**
   - Warna diambil dari bagian dalam area yang rata, bukan dari tepinya: dipecah jadi banyak cluster (k-means di ruang warna Lab), lalu yang hampir sama digabung.
   - Warna yang terlewat, misalnya garis tipis, ditambahkan bila bukan campuran anti-aliasing dua warna yang sudah ada.
4. **Buang artefak tepi.** Warna yang hanya muncul sebagai pita tipis di tepi dan mirip warna lain (ringing atau chroma bleed JPEG), atau merupakan campuran dua warna lain, dilebur ke warna yang paling mirip.
5. **Warna akhir dari gambar asli.** Bila sebagian besar piksel bernilai persis sama (PNG bersih), hex itu yang dipakai, jadi `#B26BFF` tetap `#B26BFF`.
6. **Haluskan tepi.** Setiap piksel ikut warna yang paling dominan di sekitarnya.
7. **Lacak dengan [VTracer](https://github.com/visioncortex/vtracer)**, lalu kunci setiap `fill` ke palet dan kembalikan ukuran SVG ke ukuran asli (koordinat memakai `viewBox` ukuran kerja).

Latar belakang riset dan perbandingan dengan kompetitor ada di [`riset/RISET-VEKTORISASI.md`](riset/RISET-VEKTORISASI.md).

## Batasan

- Belum ada **centerline** (garis jadi satu stroke). Garis selalu jadi bidang tipis.
- Belum ada **deteksi bentuk**: lingkaran dan persegi tetap berupa path, bukan `<circle>` atau `<rect>`.
- Garis yang sangat tipis (sekitar 1,5 px atau kurang) pada JPEG kecil bisa berubah warna, karena JPEG menyimpan warna dengan resolusi setengah. Pakai `-p` atau `-c` untuk memperbaikinya.
- Foto dan gradasi akan jadi bidang-bidang warna (posterize).

## Test

```bash
python3 -m pytest vectorizer/tests -q
```

Test memakai gambar sintetis dengan warna yang diketahui pasti ([`tests/samples.py`](tests/samples.py)) dan logo Helonoia. Yang diperiksa: warna yang ditemukan, kemiripan hasil render dengan input, ketahanan terhadap JPEG, setiap opsi, dan CLI.
