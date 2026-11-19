# Jadwal Hari-H Pindah Domain Katalog

Jadwal pelaksanaan untuk memindahkan katalog dari `invitation.helonoia.net` ke `invitation.helonoia.com`, mengikuti [Rencana Pindah Domain Helonoia](RENCANA-PINDAH-DOMAIN.md).

- **Untuk:** pemilik Helonoia
- **Disusun:** 19 November 2026
- **Cara redirect:** opsi A, diputuskan 19 November 2026. DNS helonoia.net dipindah ke Cloudflare, lalu redirect memakai Redirect Rule.
- **Zona waktu:** semua jam dalam WIB.

## Memilih tanggal hari-H

Pilih **Selasa atau Rabu malam**, dan pastikan **tidak ada acara pelanggan dalam 2 hari setelahnya**. Alasannya, tamu paling ramai membuka undangan menjelang akhir pekan. Selain itu, rollback masih mungkin dilakukan sampai 24 jam setelah redirect dipasang, dan jendela itu sebaiknya tidak jatuh di hari acara.

Jadwal di bawah ditulis relatif terhadap hari-H (H). Tanggalnya tinggal diisi setelah hari-H dipilih. Sebagai contoh, bila hari-H **Rabu, 2 Desember 2026**:

| Hari | Contoh tanggal | Pekerjaan |
| --- | --- | --- |
| H-7 | Rabu, 25 November | Fase 0 dan pindah nameserver helonoia.net |
| H-6 s.d. H-3 | 26–29 November | Menunggu zona Active, lalu cek harian |
| H-2 | Senin, 30 November | Fase 1: alamat `.com` dan persiapan file |
| H-1 | Selasa, 1 Desember | Fase 2: uji menyeluruh, lalu keputusan lanjut atau tunda |
| **H** | **Rabu, 2 Desember** | **Fase 3 dan 4, mulai 21.30** |
| H+1 s.d. H+3 | 3–5 Desember | Pemantauan harian. Batas rollback: Kamis, 3 Desember pukul 22.45 |
| H+7 s.d. H+14 | 9–16 Desember | Ganti link di bio, template, dan profil |
| H+30 | 1 Januari 2027 | Tinjauan akhir |

Contoh ini masuk akal karena halaman 404 sudah aktif sejak 19 November, jadi sudah berjalan 6 hari sebelum H-7. Pindah nameserver juga dilakukan di tengah pekan, bukan menjelang akhir pekan.

## Siapa mengerjakan apa

- **Pemilik:** semua yang hanya bisa dikerjakan dari akun pemilik: dashboard Cloudflare, registrar helonoia.net, dan Google Search Console.
- **Claude:** perubahan di repo lewat PR (katalog dan helonoia.com), serta menjalankan skrip uji. Merge tetap atas persetujuan pemilik.

## H-7: Fase 0 dan pindah nameserver

| Jam | Pelaksana | Langkah | Selesai bila |
| --- | --- | --- | --- |
| 09.00 | Pemilik | Cek jadwal acara pelanggan di sekitar hari-H. Bila ada acara di H s.d. H+2, geser hari-H | Hari-H dikonfirmasi |
| 09.15 | Pemilik | Di Cloudflare, pastikan proyek Pages `felicidad126-github-io` dan zona helonoia.com ada di **akun yang sama** | Tercatat: satu akun / beda akun |
| 09.30 | Pemilik | Buka Pages → `felicidad126-github-io` → Deployments. Catat ID deployment produksi yang aktif (titik rollback) | ID tercatat |
| 09.45 | Pemilik | Cek tanggal kedaluwarsa helonoia.net dan helonoia.com. Perpanjang helonoia.net minimal 12 bulan dan nyalakan perpanjangan otomatis | Masa aktif `.net` lebih dari 12 bulan dari hari-H |
| 10.00 | Pemilik | Di Cloudflare: **Add a domain** → `helonoia.net`, pilih paket Free | Cloudflare memberi dua nameserver |
| 10.15 | Pemilik | Bandingkan record hasil pindaian dengan panel NeoDNS. Minimal ada `invitation` CNAME → `felicidad126-github-io.pages.dev` (Proxied, awan oranye) dan `www` CNAME → `helonoia.net`. Tambahkan record yang kurang | Semua record di NeoDNS juga ada di Cloudflare |
| 10.30 | Pemilik | Di panel registrar helonoia.net, ganti nameserver `satu.neodns.id` dan `dua.neodns.id` ke dua nameserver dari Cloudflare | Nameserver tersimpan |
| 10.45 | Claude | Uji `invitation.helonoia.net` setelah penggantian: beranda, satu tema dengan `?to=`, dan halaman 404 | Semua normal |
| 11.00 | Claude | Siapkan daftar URL final dari repo katalog untuk uji Fase 2 dan 4, termasuk link tamu yang sudah pernah dikirim (contohnya diminta dari pemilik) | Daftar uji final |
| 11.00 | Pemilik | Mulai **bekukan perubahan isi katalog** sampai H+1 | Disepakati |

## H-6 s.d. H-3: tunggu zona Active

| Kapan | Pelaksana | Langkah | Selesai bila |
| --- | --- | --- | --- |
| Pagi dan sore setiap hari | Pemilik | Cek status zona helonoia.net di Cloudflare | Status **Active** (biasanya beberapa jam, paling lama sekitar 48 jam) |
| Setelah Active | Pemilik | Pastikan custom domain `invitation.helonoia.net` di Pages tetap **Active**, dan record `invitation` tetap Proxied | Keduanya Active |
| Setelah Active | Claude | Uji ulang `.net`: beranda, 10 tema, demo, 404, dan HTTPS tanpa peringatan | Tidak ada yang berubah |
| Setelah Active | Pemilik | Verifikasi `helonoia.net` di Search Console (tipe Domain, record TXT di Cloudflare). Ini dibutuhkan untuk Change of Address | Terverifikasi |

**Bila zona belum Active di H-3 pukul 17.00, geser hari-H.** Redirect Rule hanya bisa dipasang setelah zona Active.

## H-2: Fase 1, siapkan alamat baru

| Jam | Pelaksana | Langkah | Selesai bila |
| --- | --- | --- | --- |
| 10.00 | Pemilik | Pages → `felicidad126-github-io` → **Custom domains** → Set up a custom domain → `invitation.helonoia.com`. Bila beda akun, buat CNAME `invitation` → `felicidad126-github-io.pages.dev` di zona helonoia.com, **setelah** domain ditambahkan di Pages | Status custom domain Active |
| 10.30 | Claude | Uji `https://invitation.helonoia.com`: HTTPS tanpa peringatan, beranda dan satu tema terbuka | Lolos |
| 10.30 | Claude | Buat PR katalog untuk Fase 3, tanpa di-merge: canonical, `og:url`, dan `og:image` ke `.com` di 15 `index.html`, ditambah `robots.txt`, `sitemap.xml`, dan bagian Domain di README | PR terbuka, preview Cloudflare hijau |
| 11.30 | Claude | Buat PR helonoia untuk Fase 3, tanpa di-merge: kartu "Yang sudah bisa dilihat" di `HTML/index.html` dan baris katalog di `README.md` diganti ke `https://invitation.helonoia.com/` | PR terbuka |
| 13.00 | Pemilik | Di zona helonoia.net: **Rules → Redirect Rules → Create rule**, lalu simpan **dalam keadaan nonaktif**. Isiannya ada di bawah. Bila panel tidak menyediakan opsi simpan nonaktif, salin isiannya ke catatan dan buat rule-nya di hari-H | Rule siap tapi belum aktif |

Isian Redirect Rule:

- **When incoming requests match:** Hostname equals `invitation.helonoia.net`
- **Then:** URL redirect, Type **Dynamic**
  - Expression: `concat("https://invitation.helonoia.com", http.request.uri.path)`
  - Status code: **301**
  - **Preserve query string:** dicentang

## H-1: Fase 2, uji menyeluruh

| Jam | Pelaksana | Langkah | Selesai bila |
| --- | --- | --- | --- |
| 09.00 | Claude | Jalankan **Skrip uji B** (di bawah) terhadap `.com`: semua URL mengembalikan 200, dan alamat acak mengembalikan 404 | Semua OK |
| 09.30 | Claude | Uji di browser ponsel: beranda, 10 tema, dan demo setiap tema. Cocokkan judul dan isinya dengan `.net` | Sama persis |
| 11.00 | Pemilik | Uji di HP sendiri: 3 link `/<tema>/?to=`, 1 link `/demo/?tema=…&to=…`, dan 1 link `/?to=` (harus berakhir di `/lengkung-sage/?to=…`). Pastikan nama tamu di sampul benar | Nama tamu benar di semua link |
| 11.30 | Pemilik | Coba RSVP, ucapan, galeri, peta, amplop, musik, dan tombol WhatsApp (nomor dan isi pesan) di `.com` | Semua jalan |
| 13.00 | Claude | Buka preview PR katalog. Pastikan tidak ada lagi `helonoia.net` di canonical, `og:`, `robots.txt`, dan `sitemap.xml` | Bersih |
| 16.00 | Pemilik | **Keputusan lanjut atau tunda.** Lanjut hanya bila semua langkah H-1 lolos, zona helonoia.net Active, rule siap, dan tidak ada acara pelanggan di H s.d. H+2 | Diputuskan dan dicatat |

## Hari-H: Fase 3 dan 4

| Jam | Pelaksana | Langkah | Selesai bila |
| --- | --- | --- | --- |
| 21.30 | Berdua | Persiapan: buka dashboard Cloudflare (zona helonoia.net, zona helonoia.com, Pages), kedua PR, dan Search Console. Siapkan ID deployment rollback dari H-7 | Semua siap |
| 22.00 | Pemilik | **Fase 3a:** merge PR katalog | Cloudflare Pages selesai deploy (1–2 menit) |
| 22.05 | Claude | Cek di `.com` dan `.net`: canonical dan `og:url` sudah `.com`, `og:image` terbuka, dan `robots.txt` serta `sitemap.xml` berisi `.com` | Lolos |
| 22.15 | Pemilik | **Fase 3b:** merge PR helonoia | GitHub Actions "Deploy helonoia.com" hijau |
| 22.25 | Claude | Cek kartu katalog di helonoia.com mengarah ke `https://invitation.helonoia.com/` | Lolos |
| 22.30 | Pemilik | Search Console, properti Domain `helonoia.com`: kirim `https://invitation.helonoia.com/sitemap.xml` | Status Success atau Pending |
| 22.45 | Pemilik | **Fase 4:** aktifkan Redirect Rule di zona helonoia.net. **Catat jamnya:** jendela rollback 24 jam dimulai di sini | Rule aktif |
| 22.50 | Claude | Jalankan **Skrip uji A** terhadap `.net`: setiap URL harus 301 dalam satu lompatan ke pasangan `.com`-nya | Semua OK |
| 23.00 | Pemilik | Uji ulang di HP lewat alamat **`.net`**: 3 link tema dengan `?to=`, 1 link demo, dan 1 link `/?to=`. Nama tamu harus tetap tampil | Nama tamu benar di semua link |
| 23.10 | Claude | Cek tidak ada loop: buka `.com` dan `.net` bergantian. `.com` tidak pernah mengarah ke `.net`, dan alamat acak di `.com` mendapat 404 Noi | Lolos |
| 23.20 | Pemilik | **Keputusan akhir:** lanjut, atau rollback (lihat di bawah) | Dicatat |
| 23.30 | Berdua | Selesai. Catat jam go-live dan hasil uji | Catatan tersimpan |

## H+1 s.d. H+3: pemantauan

| Kapan | Pelaksana | Langkah |
| --- | --- | --- |
| H+1, 09.00 | Claude | Jalankan Skrip uji A dan B lagi |
| H+1, 09.30 | Pemilik | Search Console: pakai **Change of Address** dari `helonoia.net` bila ditawarkan untuk pasangan properti ini. Bila tidak ditawarkan, lewati: 301 dan sitemap sudah cukup |
| H+1, 22.45 | Pemilik | **Batas rollback.** Bila sampai jam ini ditemukan link tamu rusak, nama tamu hilang, atau error SSL yang meluas, rollback dulu dan perbaiki kemudian |
| H+1 s.d. H+3, 09.00 | Claude dan pemilik | Ulangi Skrip uji A, cek laporan halaman tidak ditemukan (404) di Search Console, dan tanyakan ke pelanggan yang acaranya dekat apakah ada tamu yang mengeluh |
| H+2 | Pemilik | Cabut pembekuan perubahan isi katalog bila tidak ada masalah |

## Sesudahnya

| Kapan | Pelaksana | Langkah |
| --- | --- | --- |
| H+7 s.d. H+14 | Pemilik | Ganti link `.net` ke `.com` di bio dan sorotan Instagram, template pesan WhatsApp, dan Google Business Profile bila ada |
| H+30 | Pemilik | Tinjau trafik dan posisi pencarian di Search Console. Domain `.net` dan Redirect Rule **tetap dipertahankan** |
| H+12 bulan | Pemilik | Perpanjang helonoia.net lagi selama masih ada acara pelanggan yang link `.net`-nya beredar |

## Rollback cepat

Dipakai bila keputusan akhir di hari-H atau batas rollback H+1 menyatakan rollback.

1. **Redirect:** zona helonoia.net → Rules → Redirect Rules → matikan rule. Katalog `.net` langsung melayani lagi.
2. **Canonical dan og:** Pages → Deployments → rollback ke ID deployment yang dicatat di H-7.
3. **helonoia.com:** revert commit merge PR helonoia di `main`. Workflow akan men-deploy versi lama.
4. Custom domain `.com` boleh tetap terpasang, karena canonical sudah kembali ke `.net`.
5. Catat penyebabnya, perbaiki tanpa terburu-buru, lalu ulangi dari H-1 dengan tanggal baru.

## Skrip uji

Jalankan dari terminal mana pun. Setiap baris mencetak `OK` atau `GAGAL` beserta alasannya.

**Skrip uji A: redirect dari `.net`** (hari-H pukul 22.50, lalu H+1 s.d. H+3)

```bash
B=https://invitation.helonoia.net; N=https://invitation.helonoia.com
for p in "/" "/?to=Tes+Tamu" "/demo/?tema=biru-kabut&to=Tes%20Tamu" "/kaca-patri/?to=Tes%20Tamu" "/brand/" "/HTML/" "/robots.txt" "/sitemap.xml" "/katalog/og.jpg" "/foto/cover.jpg" "/toko.js" "/helonoia/noi.webp" /amplop-linen/ /biru-kabut/ /edisi-monokrom/ /garis-editorial/ /kaca-patri/ /kelopak-mimpi/ /lengkung-sage/ /parallax-sway/ /riviera-kobalt/ /truntum-terakota/; do
  r=$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" "$B$p")
  [ "$r" = "301 $N$p" ] && echo "OK    $p" || echo "GAGAL $p -> $r"
done
```

**Skrip uji B: alamat `.com` terbuka** (H-1 pukul 09.00, lalu H+1)

```bash
N=https://invitation.helonoia.com
for p in "/" "/?to=Tes+Tamu" "/demo/?tema=biru-kabut&to=Tes%20Tamu" "/kaca-patri/?to=Tes%20Tamu" "/brand/" "/HTML/" "/robots.txt" "/sitemap.xml" "/katalog/og.jpg" "/foto/cover.jpg" "/toko.js" "/helonoia/noi.webp" /amplop-linen/ /biru-kabut/ /edisi-monokrom/ /garis-editorial/ /kaca-patri/ /kelopak-mimpi/ /lengkung-sage/ /parallax-sway/ /riviera-kobalt/ /truntum-terakota/; do
  r=$(curl -s -o /dev/null -w "%{http_code}" "$N$p")
  [ "$r" = "200" ] && echo "OK    $p" || echo "GAGAL $p -> $r"
done
r=$(curl -s -o /dev/null -w "%{http_code}" "$N/alamat-yang-tidak-ada"); [ "$r" = "404" ] && echo "OK    404" || echo "GAGAL 404 -> $r"
```

Daftar URL di kedua skrip diambil dari katalog per 19 November 2026. Tambahkan contoh link tamu sungguhan yang dikumpulkan di H-7.
