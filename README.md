# Helonoia

Halaman perkenalan brand **Helonoia** beserta aset mereknya: maskot, logo, dan ikon.

| Folder / file | Isi |
| --- | --- |
| [`HTML/`](HTML/) | Halaman brand (`index.html`, `maskot.webp`, `favicon.png`, `logo.png`). Berdiri sendiri, tinggal disalin ke server. |
| [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md) | Panduan deploy ke server sendiri (aaPanel, Nginx manual, cPanel). |
| [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | Deploy otomatis `HTML/` ke server setiap push ke `main`. Cara menyiapkannya: [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md#update-otomatis-cicd). |
| [`helonoia/`](helonoia/) | Gambar asli maskot (`helonoia_maskot.webp`), serta generator tulisan logo dan maskot versi lama (`helonoia_monster.py`) beserta hasilnya. |
| [`helonoia/ikon/`](helonoia/ikon/) | Ikon untuk bagian "Empat kebiasaan kami". |
| [`.claude/skills/web-artifacts-builder/`](.claude/skills/web-artifacts-builder/) | Skill Claude Code untuk membuat artifact React + Tailwind + shadcn/ui. Salinan dari skill bawaan Anthropic yang langkah bundle-nya sudah diperbaiki; otomatis dipakai saat Claude Code membuka repo ini. |

## Halaman brand

Halaman di folder [`HTML/`](HTML/) mengenalkan brand **Helonoia** sebelum ada produk: arti nama (HELO dari "halo", NOIA dari "paranoia"), maskot monster ungu dan cerita tiap bagian tubuhnya, dan empat kebiasaan brand. Versi resminya ada di https://helonoia.com/ (aaPanel, lihat [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md)).

- Animasi penuh (abaikan setting reduced-motion): `HTML/?motion=full`
- Maskot di halaman ini adalah `HTML/maskot.webp`, potongan dari gambar asli [`helonoia/helonoia_maskot.webp`](helonoia/helonoia_maskot.webp) (latar transparan). `HTML/favicon.png` (kepala maskot dalam lingkaran, dipakai juga di header) dan `HTML/logo.png` (maskot + tulisan HELONOIA) dibuat dari gambar yang sama. Penanda bernomor di bagian "Kenalan dengan si monster ungu" memakai koordinat piksel `maskot.webp`, jadi perlu digeser bila gambarnya diganti.
- Tulisan HELONOIA dibuat dari [`helonoia/helonoia_monster.py`](helonoia/helonoia_monster.py). Bila hurufnya berubah, potongan SVG di awal `<body>` perlu dibuat ulang dari generator itu.
- Semua warna diambil dari logo: Malam `#120B1E`, Ungu Noia `#B26BFF`, Ungu Tua `#7C3FD6`, Lilac `#CDA6FF`, Lime `#C6FF3D`, Putih Halo `#F4EFFF`. Palet dan huruf sengaja tidak ditampilkan di halaman publik; tempatnya di dokumen brand.
- Interaksi: maskot condong ke arah kursor (di HP ia condong ke sana kemari sendiri), tombol "Sapa balik" atau ketukan pada maskot membuatnya melompat kecil dan menjawab.
- `canonical`, `og:url`, dan `og:image` mengarah ke `https://helonoia.com/`.
- Kontak (WhatsApp, Instagram, email) diisi di objek `KONTAK` pada skrip di bagian bawah `HTML/index.html`. Selama kosong, tombol kontak tidak ditampilkan.
- Bagian "Yang sudah bisa dilihat" menautkan ke katalog undangan digital di https://invitation.helonoia.net/.
- Font Fredoka (huruf logo) dan Plus Jakarta Sans dimuat dari Google Fonts, berlisensi SIL Open Font License 1.1.

## Maskot & logo

Maskot yang dipakai sekarang adalah `helonoia/helonoia_maskot.webp`. Generator di bawah ini masih membuat maskot versi lama (monster yang melambai) dan tulisan HELONOIA.

Jalankan dari dalam folder `helonoia/`:

```bash
cd helonoia && python3 helonoia_monster.py
```

| File | Isi |
| --- | --- |
| `helonoia_maskot.webp` | Maskot sekarang, gambar asli dengan latar transparan (bukan hasil generator) |
| `helonoia_monster.svg` | Maskot lama, latar transparan |
| `helonoia_monster_bg.svg` / `.png` | Maskot lama, latar gelap `#120B1E` |
| `helonoia_logo.svg` / `.png` | Logo lama lengkap (maskot + tulisan), latar gelap |
| `helonoia_logo_transparent.svg` | Logo lama lengkap, latar transparan |

## Ikon kebiasaan

Grid 32×32, garis 2.4 dengan ujung dan sambungan membulat, dan `currentColor`, jadi warnanya mengikuti CSS induknya.

| File | Kebiasaan |
| --- | --- |
| `helonoia/ikon/menyapa-duluan.svg` | Menyapa duluan (pintu terbuka) |
| `helonoia/ikon/teliti-sampai-rewel.svg` | Teliti sampai rewel (tiga kali centang) |
| `helonoia/ikon/janji-kecil-saja.svg` | Janji kecil saja (kecil tapi pasti) |
| `helonoia/ikon/sedikit-aneh.svg` | Sedikit aneh (wajah monster) |
