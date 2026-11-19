# Helonoia

Halaman perkenalan brand **Helonoia** beserta aset mereknya: maskot, logo, dan ikon.

| Folder / file | Isi |
| --- | --- |
| [`HTML/`](HTML/) | Halaman brand (`index.html`, `maskot-helonoia.webp`, `favicon.png`, `logo.png`, `robots.txt`, `sitemap.xml`). Berdiri sendiri, tinggal disalin ke server. |
| [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md) | Panduan deploy ke server sendiri (aaPanel, Nginx manual, cPanel). |
| [`RENCANA-PINDAH-DOMAIN.md`](RENCANA-PINDAH-DOMAIN.md) | Rencana memindahkan katalog undangan dari invitation.helonoia.net ke invitation.helonoia.com. |
| [`JADWAL-PINDAH-DOMAIN.md`](JADWAL-PINDAH-DOMAIN.md) | Jadwal pelaksanaan pindah domain per jam, dari H-7 sampai H+30, beserta skrip uji. |
| [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | Deploy otomatis `HTML/` ke server setiap push ke `main`. Cara menyiapkannya: [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md#update-otomatis-cicd). |
| [`helonoia/`](helonoia/) | Gambar asli maskot (`helonoia_maskot.webp`), serta generator tulisan logo dan maskot versi lama (`helonoia_monster.py`) beserta hasilnya. |
| [`helonoia/ikon/`](helonoia/ikon/) | Ikon untuk bagian "Empat kebiasaan kami". |
| [`.claude/skills/web-artifacts-builder/`](.claude/skills/web-artifacts-builder/) | Skill Claude Code untuk membuat artifact React + Tailwind + shadcn/ui. Salinan dari skill bawaan Anthropic yang langkah bundle-nya sudah diperbaiki; otomatis dipakai saat Claude Code membuka repo ini. |

## Halaman brand

Halaman di folder [`HTML/`](HTML/) mengenalkan brand **Helonoia** sebelum ada produk: arti nama (HELO dari "halo", NOIA dari "paranoia"), maskot monster ungu dan cerita tiap bagian tubuhnya, dan empat kebiasaan brand. Versi resminya ada di https://helonoia.com/ (aaPanel, lihat [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md)).

- Animasi selalu jalan penuh, termasuk di HP yang setelan animasinya dimatikan (reduced-motion), supaya tampilannya sama di Android dan iPhone.
- Maskot di halaman ini adalah `HTML/maskot-helonoia.webp`, potongan dari gambar asli [`helonoia/helonoia_maskot.webp`](helonoia/helonoia_maskot.webp) (latar transparan). `HTML/favicon.png` (kepala maskot dalam lingkaran, dipakai juga di header) dan `HTML/logo.png` (maskot + tulisan HELONOIA) dibuat dari gambar asli yang sama.
- Di bagian atas, mata maskot digambar ulang sebagai vektor di atas gambarnya (komponen `mk-*` di `index.html`), dan penanda bernomor di bagian "Kenalan dengan si monster ungu" memakai koordinat piksel gambar. Keduanya perlu disesuaikan bila `maskot-helonoia.webp` diganti.
- Maskot di bagian atas tersusun dari lapisan terpisah (siluet, tanduk, gambar berwarna, mata), dan animasinya hanya mengubah `transform` atau `opacity` lapisan itu, supaya dijalankan GPU dan tetap mulus di HP Android. Jangan pindahkan animasi ke elemen di dalam SVG yang memuat gambar maskot: seluruh gambar akan dilukis ulang setiap frame dan animasinya tersendat.
- Tulisan HELONOIA dibuat dari [`helonoia/helonoia_monster.py`](helonoia/helonoia_monster.py). Bila hurufnya berubah, potongan SVG di awal `<body>` perlu dibuat ulang dari generator itu.
- Semua warna diambil dari logo: Malam `#120B1E`, Ungu Noia `#B26BFF`, Ungu Tua `#7C3FD6`, Lilac `#CDA6FF`, Lime `#C6FF3D`, Putih Halo `#F4EFFF`. Palet dan huruf sengaja tidak ditampilkan di halaman publik; tempatnya di dokumen brand.
- Interaksi di bagian atas: maskot muncul lewat animasi perkenalan (siluet, mata terbuka, melirik, tanduk menyala, lalu tampil penuh dan menyapa). Setelah itu matanya mengikuti kursor (di HP ia melirik ke sana kemari sendiri) dan sesekali berkedip. Tombol "Sapa balik" atau ketukan pada maskot membuatnya kaget sebentar lalu menjawab.
- Maskot di bagian anatomi dan penutup condong ke arah kursor. Ketukan atau tombol "Sapa balik" di bagian penutup membuatnya melompat kecil dan menjawab.
- `canonical`, `og:url`, dan `og:image` mengarah ke `https://helonoia.com/`.
- Untuk mesin pencari: judul `<h1>` berisi teks "Helonoia" (tersembunyi di balik logo SVG, kelas `sr-only`), data terstruktur JSON-LD (`WebSite` dan `Organization`) di `<head>`, serta `robots.txt` dan `sitemap.xml`. Begitu ada akun media sosial resmi, tambahkan tautannya sebagai `sameAs` di `Organization`. Pendaftaran ke Google Search Console ada di [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md#supaya-muncul-di-google).
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
