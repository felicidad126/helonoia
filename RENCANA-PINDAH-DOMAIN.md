# Rencana Pindah Domain Helonoia

Memindahkan katalog undangan dari `invitation.helonoia.net` ke `invitation.helonoia.com`, supaya katalog dan situs utama berada di satu akar domain yang sama.

- **Untuk:** pemilik Helonoia
- **Tanggal rencana:** 19 November 2026
- **Diperbarui:** 19 November 2026, setelah dicocokkan dengan DNS publik, katalog live, dan repo `helonoia`. Opsi A dipilih, dan halaman 404 katalog sudah aktif.
- **Jadwal pelaksanaan:** [`JADWAL-PINDAH-DOMAIN.md`](JADWAL-PINDAH-DOMAIN.md)
- **Status:** Dokumen perencanaan. Tidak ada perubahan DNS, hosting, atau website yang dilakukan bersama dokumen ini.

## Yang berubah di versi ini

- **DNS helonoia.net ternyata tidak di Cloudflare** (nameserver-nya NeoDNS). Redirect Rule Cloudflare tidak bisa langsung dipasang, jadi bagian redirect ditulis ulang dengan dua opsi, dan ada satu keputusan baru.
- **Katalog berjalan di Cloudflare Pages.** Alamat baru cukup ditambahkan sebagai custom domain di proyek yang sama. Tidak ada file yang disalin, dan keputusan soal hosting tidak diperlukan lagi.
- **Peta URL disesuaikan dengan pola sebenarnya:** `/<tema>/`, `/demo/?tema=…&to=…`, dan `/?to=…` (yang ternyata masih aktif).
- **Katalog belum punya halaman 404, `robots.txt`, dan `sitemap.xml`.** Ketiganya dipasang sebagai pekerjaan pendahulu, dan sudah aktif di `invitation.helonoia.net` sejak 19 November 2026.
- **Repo katalog sudah dicek.** Daftar file yang perlu diubah di Fase 1 kini lengkap, termasuk `/brand/` dan `/HTML/` yang sebelumnya belum tercatat.
- **Koreksi kondisi:** helonoia.com ternyata sudah menautkan ke katalog, dan analytics belum terpasang di kedua situs.

## Ringkasan

|  | Alamat |
| --- | --- |
| Saat ini | `invitation.helonoia.net`: katalog aktif di Cloudflare Pages (proyek `felicidad126-github-io`). 10 desain undangan digital, nama tamu personal di cover, RSVP, galeri, peta, dan amplop digital |
| Target | `invitation.helonoia.com`: subdomain dari helonoia.com, dilayani proyek Pages yang sama. Isi dan fungsi sama persis, hanya alamatnya yang pindah |

Pindahan ini aman dilakukan tanpa downtime dengan satu prinsip: **siapkan alamat baru sampai benar-benar jadi dulu, baru pasang pengalihan dari alamat lama.**

Urutannya:

1. Tambahkan alamat baru sebagai custom domain di proyek Pages. DNS dan sertifikat SSL dibuat oleh Cloudflare.
2. Uji semua halaman dan link nama tamu di alamat baru.
3. Ganti canonical dan pratinjau link ke `.com`.
4. Pasang redirect permanen (301) dari setiap URL `.net` ke URL `.com` yang sama persis, termasuk parameter seperti `?to=` dan `?tema=`.

Domain lama tidak dimatikan. Ia tetap hidup sebagai pengalih selama minimal 12 bulan.

Hasil akhir yang diharapkan: pengunjung yang membuka link lama, link yang sudah tersebar di WhatsApp, atau hasil pencarian Google akan sampai di halaman yang sama di alamat baru. Mereka tidak melihat error dan tidak kehilangan nama tamu di cover undangan.

## Kondisi saat ini

Dicek dari luar pada 19 November 2026.

| Domain | DNS dikelola di | Isi |
| --- | --- | --- |
| `helonoia.com` | Cloudflare (`anita` dan `ganz.ns.cloudflare.com`) | Situs brand dengan maskot Noi, di server aaPanel (Nginx). Sumbernya repo `helonoia`, yang deploy otomatis lewat GitHub Actions saat ada push ke `main`. Email @helonoia.com memakai Lark (record `MX`) |
| `invitation.helonoia.net` | NeoDNS (`satu` dan `dua.neodns.id`), **bukan Cloudflare** | CNAME ke `felicidad126-github-io.pages.dev` (Cloudflare Pages). Sumbernya repo `felicidad126/felicidad126.github.io`: HTML statis tanpa proses build, terhubung ke Git (setiap branch mendapat deploy preview) |
| `felicidad126.github.io` | GitHub | Salinan cadangan katalog di GitHub Pages, dari repo yang sama |
| `invitation.helonoia.com` | Cloudflare (zona helonoia.com) | Belum ada record DNS. Subdomain ini yang akan disiapkan |

- **Zona helonoia.net.** Record yang terlihat dari luar hanya dua:
  - `invitation`, CNAME ke Pages.
  - `www`, CNAME ke `helonoia.net`. Karena `helonoia.net` sendiri tidak punya record A, `www.helonoia.net` saat ini tidak membuka apa pun.

  Tidak ada `MX` dan DNSSEC tidak aktif. Daftar lengkapnya dicek di panel NeoDNS pada Fase 0.
- **Link antarsitus.** helonoia.com **sudah** menautkan ke katalog: kartu "Yang sudah bisa dilihat" mengarah ke `https://invitation.helonoia.net/` (`HTML/index.html` di repo `helonoia`). Yang belum ada adalah link balik dari katalog ke helonoia.com.
- **Google memisahkan keduanya.** Karena akar domainnya berbeda (`.com` dan `.net`), Google memperlakukan keduanya sebagai situs yang terpisah.
- **Halaman yang terindeks.** Yang bisa diindeks hanya beranda katalog dan `/brand/`, yaitu halaman brand Helonoia versi lama yang isinya mirip helonoia.com. Ke-10 halaman tema memakai `noindex, nofollow`, sedangkan `/demo/` dan `/HTML/` (penerus ke `/brand/`) memakai `noindex`.
- **Analytics.** Belum ada tag analytics di kedua situs.
- **Fitur halaman tema.** RSVP dan ucapan di halaman tema disimpan di browser tamu (`localStorage`), tidak dikirim ke server. Peta memakai tautan Google Maps biasa tanpa kunci API. Jadi tidak ada layanan pihak ketiga yang terikat ke nama domain.
- **Sampai 19 November 2026 katalog belum punya halaman 404, `robots.txt`, dan `sitemap.xml`.** Sekarang sudah ada (lihat pekerjaan pendahulu). Sebelumnya setiap alamat yang tidak ada, termasuk `/robots.txt` dan `/sitemap.xml`, mengembalikan beranda dengan status 200. Akibatnya waktu itu:
  - Link yang rusak tidak pernah terlihat sebagai error.
  - Alamat tak dikenal yang membawa `?to=` dan diakhiri garis miring (misalnya `/x/?to=Nama`) terjebak dalam pengalihan tanpa henti. Penyebabnya, script di beranda meneruskan ke path relatif `lengkung-sage/`.

### Tujuan dan bukan tujuan

**Tujuan:**

- Satu akar domain untuk brand, katalog, dan halaman berikutnya.
- Otoritas SEO yang tidak terpecah.
- Satu properti analytics yang bisa membaca alur pengunjung dari situs utama ke katalog sampai klik WhatsApp. Ini pemasangan baru, karena saat ini belum ada analytics.
- Alamat yang lebih mudah diingat dan dipercaya calon pembeli.

**Bukan tujuan dokumen ini:** mengubah desain katalog, mengubah 10 desain undangan, atau mengubah isi helonoia.com.

Perubahan file katalog yang tetap perlu hanya yang menyangkut alamat: canonical, `og:url`, `og:image`, `robots.txt`, dan `sitemap.xml` (lihat Fase 1). Penyamaan header, footer, dan maskot Noi di katalog adalah pekerjaan terpisah setelah pindahan selesai.

## Pekerjaan pendahulu: 404, robots.txt, sitemap.xml

Dipasang di `.net` sebagai perubahan terpisah, lalu dibiarkan berjalan beberapa hari sebelum Fase 0.

**Status:** sudah aktif di `invitation.helonoia.net` sejak 19 November 2026 (PR #35 di repo katalog). Lolos 37 uji di deploy preview Cloudflare, lalu dicek ulang di produksi.

- **`404.html` bergambar Noi.**
  - Pages akan menampilkan halaman ini dengan status 404 untuk alamat yang tidak ada. Ini menggantikan perilaku sekarang (beranda dengan status 200).
  - Alamat tak dikenal yang membawa `?to=`, `?open`, atau `?motion` tetap diteruskan ke `/lengkung-sage/` seperti sekarang. Bedanya, path-nya absolut, sehingga pengalihan tanpa henti di `/x/?to=` hilang.
- **`robots.txt` dan `sitemap.xml`.**
  - `robots.txt` mengizinkan semua halaman dan menunjuk ke sitemap.
  - `sitemap.xml` hanya berisi beranda, karena halaman lain memakai `noindex`.
  - Keduanya memakai alamat `.net` dulu, lalu diganti ke `.com` di Fase 3.

Ini dikerjakan sebelum pindahan karena dua alasan. Pertama, perilaku 404 yang baru sudah teruji di alamat lama sebelum hari-H. Kedua, pemantauan di Fase 5 jadi punya arti: link yang rusak muncul sebagai 404, tidak lagi tersamar sebagai beranda.

## Semua URL lama harus punya pasangan di alamat baru

Aturan pemetaannya sederhana dan tidak boleh ada pengecualian: **path dan query string dipertahankan persis sama**, hanya host-nya yang berganti. Jika satu pola saja terlewat, yang rusak bukan halaman katalog biasa, melainkan link undangan yang sudah dikirim ke tamu.

| URL lama (.net) | URL baru (.com) | Catatan |
| --- | --- | --- |
| `/` | `/` | Beranda katalog, satu-satunya halaman yang terindeks |
| `/<tema>/` | `/<tema>/` | 10 halaman tema: `amplop-linen`, `biru-kabut`, `edisi-monokrom`, `garis-editorial`, `kaca-patri`, `kelopak-mimpi`, `lengkung-sage`, `parallax-sway`, `riviera-kobalt`, `truntum-terakota` |
| `/<tema>/?to=Nama+Tamu` | `/<tema>/?to=Nama+Tamu` | Kritis: nama tamu di cover |
| `/demo/?tema=<tema>&to=Nama%20Tamu` | `/demo/?tema=<tema>&to=Nama%20Tamu` | Tombol demo di katalog. Kedua parameter harus utuh |
| `/brand/` | `/brand/` | Halaman brand Helonoia versi lama |
| `/HTML/` | `/HTML/`, lalu script meneruskan ke `/brand/` | Alamat lama halaman brand |
| `/?to=Nama+Tamu` (juga `?open`, `?motion`) | `/?to=Nama+Tamu`, lalu script beranda meneruskan ke `/lengkung-sage/?to=…` | Format lama Lengkung Sage yang masih aktif. Satu 301 di server, lalu satu pengalihan di browser |
| `/katalog/og.jpg`, `/foto/cover.jpg`, `/toko.js`, `/helonoia/…`, aset lain | Path yang sama | Jangan sampai 404 di aset |
| `/robots.txt`, `/sitemap.xml` | Path yang sama | Ikut dialihkan seperti URL lain |

Tabel di atas diambil dari katalog live per 19 November 2026. Inventaris di Fase 0 tetap wajib: cek repo katalog untuk halaman yang tidak ditautkan dari beranda (misalnya undangan pelanggan) dan path lama yang pernah dibagikan.

## Fase pelaksanaan

### Fase 0: Inventaris dan bekukan perubahan

Estimasi: setengah hari, ditambah waktu tunggu pindah nameserver.

- Repo sumber dan cara deploy sudah terkonfirmasi. Repo-nya `felicidad126/felicidad126.github.io`, terhubung ke Git: merge ke `main` masuk ke produksi, dan branch lain mendapat deploy preview. Artinya opsi B juga bisa dipakai.
- Lengkapi daftar URL: tabel di atas, ditambah halaman yang tidak ditautkan dari beranda, ditambah contoh link `?to=` yang benar-benar sudah dikirim ke tamu.
- Catat di mana saja link `.net` sudah tersebar: bio Instagram, status dan broadcast WhatsApp, Google Business Profile bila ada, dan template pesan ke pelanggan.
- Catat akses:
  - Akun Cloudflare yang memegang proyek Pages dan akun yang memegang zona helonoia.com. Kalau satu akun, record DNS di Fase 1 dibuat otomatis.
  - Panel registrar dan NeoDNS helonoia.net.
  - Tanggal kedaluwarsa kedua domain.
- Sepakati jendela bekukan: selama Fase 1–4 tidak ada perubahan isi katalog selain perubahan pindahan itu sendiri.
- Catat ID deployment produksi Pages yang sedang aktif sebagai titik rollback. Pages bisa kembali ke deployment lama dari menu Deployments. Simpan juga tangkapan layar beranda dan beberapa halaman tema.
- **Pindahkan DNS helonoia.net ke Cloudflare** (opsi A) di fase ini, minimal 2 hari sebelum Fase 3. Langkahnya ada di bagian redirect.

### Fase 1: Siapkan alamat baru

Estimasi: 1–2 jam, termasuk menunggu SSL.

- Di Cloudflare, buka **Workers & Pages → `felicidad126-github-io` → Custom domains → Set up a custom domain**, lalu isi `invitation.helonoia.com`.
  - Kalau zona helonoia.com ada di akun yang sama, record CNAME `invitation` dibuat otomatis.
  - Kalau beda akun, buat manual di zona helonoia.com: CNAME `invitation` → `felicidad126-github-io.pages.dev`. Tambahkan domain di Pages **dulu**, baru buat CNAME-nya. Urutan terbalik menghasilkan error 522.
- Tunggu status custom domain menjadi Active dan sertifikat terbit. `https://invitation.helonoia.com` harus terbuka tanpa peringatan. **Redirect belum boleh dipasang sebelum langkah ini lolos.**
- Tidak ada file yang perlu disalin, karena kedua alamat melayani deployment yang sama.
- Soal indeks selama pengujian:
  - Canonical semua halaman masih menunjuk ke `.net`, dan halaman tema sudah `noindex`. Jadi bila Google sempat melihat `.com`, ia memperlakukannya sebagai salinan.
  - Jangan tautkan `.com` dari mana pun, dan jangan kirim sitemap `.com` sebelum Fase 3.
  - Bila ingin lebih ketat: buat Transform Rule di zona helonoia.com yang menambah header `X-Robots-Tag: noindex` untuk host `invitation.helonoia.com`, lalu hapus di Fase 3.
- Siapkan perubahan file untuk Fase 3 di branch terpisah (belum di-merge). Semuanya dari `.net` ke `.com`, dan daftar ini lengkap per 19 November 2026:
  - `index.html`: canonical, `og:url`, dan `og:image` (`/katalog/og.jpg`).
  - `demo/index.html`: `og:image` (`/katalog/og.jpg`).
  - `brand/index.html`: `og:image` (`/helonoia/helonoia_logo.png`).
  - `HTML/index.html`: canonical (`/brand/`).
  - Ke-10 halaman tema: `og:image` (`/foto/cover.jpg`).
  - `robots.txt` dan `sitemap.xml`: alamat sitemap dan URL beranda.
  - Bagian "Domain" di `README.md` repo katalog.
  - Sebelum merge, cari ulang `helonoia.net` di seluruh repo supaya perubahan setelah tanggal ini tidak terlewat.

### Fase 2: Uji alamat baru secara menyeluruh

Estimasi: setengah sampai 1 hari.

- Buka satu per satu di `.com`: beranda, ke-10 halaman tema, dan demo setiap tema. Cocokkan judul dan isinya dengan versi `.net`, jangan hanya melihat status 200.
- Uji link nama tamu, dan pastikan nama yang tampil di cover benar:
  - Minimal 3 contoh `/<tema>/?to=`.
  - 1 contoh `/demo/?tema=…&to=…`.
  - 1 contoh `/?to=`, yang harus berakhir di `/lengkung-sage/?to=…`.
- Uji di tampilan ponsel: RSVP, ucapan, galeri foto, peta lokasi, amplop digital, dan musik bila ada.
  - RSVP dan ucapan disimpan di browser tamu dan terikat ke domain. Isian yang pernah dibuat di `.net` tidak akan terlihat di `.com`. Ini wajar dan tidak perlu diperbaiki.
- Uji tombol WhatsApp: nomor tujuan dan isi pesan awal tetap benar.
- Uji alamat acak di `.com`: halaman 404 Noi harus muncul dengan status 404.
- Buka preview deployment dari branch perubahan Fase 3. Pastikan tidak ada lagi `helonoia.net` di canonical, `og:`, `robots.txt`, dan `sitemap.xml`.

### Fase 3: Go-live alamat baru

Estimasi: 1–2 jam.

- Merge perubahan file katalog dari Fase 1 sehingga ter-deploy ke produksi. Periksa canonical di `.com` dan `.net`: keduanya sekarang harus menunjuk ke `.com`.
- Hapus Transform Rule `X-Robots-Tag` bila dipakai.
- Perbarui link di helonoia.com: ubah kartu "Yang sudah bisa dilihat" di `HTML/index.html` dan baris katalog di `README.md` ke `https://invitation.helonoia.com/`, lalu merge ke `main`. Deploy berjalan otomatis lewat GitHub Actions.
- Search Console:
  - Kalau properti tipe Domain `helonoia.com` sudah dibuat (sesuai [`DEPLOY-HELONOIA.md`](DEPLOY-HELONOIA.md)), `invitation.helonoia.com` sudah ikut tercakup.
  - Kirim `https://invitation.helonoia.com/sitemap.xml` di properti itu.
- Pilih jam sepi untuk langkah ini, misalnya malam hari. Hindari hari ketika ada undangan pelanggan yang sedang ramai dibuka tamu.

### Fase 4: Pasang redirect 301 dari .net

Estimasi: 1–2 jam, ditambah pengujian.

- Pasang redirect sesuai opsi yang dipilih (lihat bagian berikut). Setiap URL dialihkan ke pasangannya, bukan satu redirect massal ke beranda.
- Uji ulang seluruh daftar URL Fase 0 dari sisi `.net`. Setiap URL harus mendarat di pasangan `.com`-nya dalam satu lompatan:

  ```bash
  curl -sI "https://invitation.helonoia.net/biru-kabut/?to=Tes+Tamu" | grep -i -E "^HTTP|^location"
  ```

  Hasil yang benar: `HTTP/2 301` dan `location: https://invitation.helonoia.com/biru-kabut/?to=Tes+Tamu`.
- Uji khusus `?to=` dan `?tema=…&to=…` dari `.net` di ponsel: nama tamu harus tetap tampil setelah berpindah alamat.
- Periksa tidak ada loop: aturan redirect hanya berlaku untuk host `invitation.helonoia.net`. `.com` tidak boleh mengarah kembali ke `.net` dalam kondisi apa pun.

### Fase 5: Pantau dan rapikan

Estimasi: 14–30 hari pemantauan.

- **Hari 1–3:** uji ulang daftar URL Fase 0 dari `.net`, dan cek laporan halaman tidak ditemukan (404) di Search Console setiap hari. Karena 404 Noi sudah terpasang, link yang rusak sekarang terlihat sebagai 404.
- **Minggu 1–2:** ganti link di semua tempat yang bisa diganti (bio, template WhatsApp, profil bisnis) ke alamat `.com`. Link lama tetap bekerja lewat redirect, jadi ini tidak mendesak, hanya merapikan.
- **Hari 30:** tinjau apakah trafik dan posisi pencarian sudah berpindah ke `.com`. Domain `.net` dan redirect-nya dipertahankan, tidak dimatikan.

## Spesifikasi redirect 301

Redirect adalah jantung pindahan ini. Syaratnya ada empat:

- Status **301** (permanen, bukan 302).
- **Satu lompatan** langsung ke tujuan akhir.
- **Path dipertahankan.**
- **Query string dipertahankan**, agar parameter nama tamu tidak hilang.

DNS helonoia.net ada di NeoDNS, bukan Cloudflare. Header `server: cloudflare` di katalog berasal dari Cloudflare Pages, bukan dari zona Cloudflare. Karena itu Redirect Rule tidak bisa langsung dipasang untuk helonoia.net, dan ada dua cara yang bisa dipilih.

### Opsi A (dipilih): pindahkan DNS helonoia.net ke Cloudflare, lalu Redirect Rule

Dikerjakan di Fase 0:

1. Di akun Cloudflare yang sama dengan proyek Pages, pilih **Add a domain**, isi `helonoia.net`, dan pilih paket Free.
2. Periksa record hasil pindaian Cloudflare. Minimal harus ada:
   - `invitation`: CNAME → `felicidad126-github-io.pages.dev`, Proxied (awan oranye).
   - `www`: CNAME → `helonoia.net`.

   Bandingkan dengan daftar lengkap di panel NeoDNS, lalu tambahkan record yang kurang.
3. Di panel registrar helonoia.net, ganti nameserver `satu.neodns.id` dan `dua.neodns.id` dengan dua nameserver yang diberikan Cloudflare. DNSSEC tidak aktif, jadi tidak ada yang perlu dimatikan dulu.
4. Tunggu status zona menjadi Active. Biasanya beberapa jam, paling lama sekitar 48 jam. Katalog tetap jalan selama proses ini karena isi record di kedua sisi sama.
5. Setelah zona Active, pastikan dua hal: `invitation.helonoia.net` masih terbuka normal, dan status custom domain-nya di Pages tetap Active.

Dikerjakan di Fase 4, di zona helonoia.net: **Rules → Redirect Rules → Create rule**.

- **When incoming requests match:** Hostname equals `invitation.helonoia.net`
- **Then:** URL redirect, Type **Dynamic**
  - Expression: `concat("https://invitation.helonoia.com", http.request.uri.path)`
  - Status code: **301**
  - **Preserve query string:** dicentang

Kelebihan opsi A:

- Redirect terpisah dari kode katalog, jadi deploy katalog berikutnya tidak bisa menghapusnya.
- Gratis tanpa kuota.
- Rollback cukup satu klik.

Kekurangannya: ada satu langkah tambahan (pindah nameserver) yang harus selesai sebelum hari-H.

### Opsi B: redirect di dalam proyek Pages (Functions)

Tambahkan file `functions/_middleware.js` di repo katalog:

```js
export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.hostname === "invitation.helonoia.net") {
    url.hostname = "invitation.helonoia.com";
    return Response.redirect(url.toString(), 301);
  }
  return next();
}
```

Hanya host yang diganti. Path dan query string ikut utuh, jadi `?to=` dan `?tema=` tetap terbawa.

Kekurangan opsi B:

- Redirect ini harus ikut di setiap deploy. Kalau file ini terhapus, redirect mati.
- Hanya jalan bila proyek Pages di-deploy dari Git atau Wrangler. Unggah manual lewat dashboard tidak menjalankan Functions.
- Setiap request, termasuk gambar dan font, memakai kuota Functions (paket gratis: 100.000 request per hari).

Contoh Nginx di versi sebelumnya dihapus karena katalog tidak berjalan di server sendiri.

Apa pun opsinya, bagian yang tidak boleh terlewat adalah mempertahankan query string. Itu yang menjaga `?to=Nama+Tamu` tetap utuh.

## SEO dan analytics tidak ikut pindah secara otomatis

Situs bisa tampil sempurna di alamat baru sementara Google masih menunjuk ke alamat lama. Bagian SEO dikerjakan bersamaan dengan Fase 3–4, bukan setelahnya.

### Checklist SEO

- [ ] `invitation.helonoia.com` tercakup di Search Console. Properti Domain `helonoia.com` sudah mencakupnya; bila properti itu belum ada, buat sekarang.
- [ ] `helonoia.net` juga terverifikasi di Search Console, lewat record TXT di DNS helonoia.net (di NeoDNS, atau di Cloudflare bila memilih opsi A).
- [ ] Sitemap `.com` dikirim. Sitemap `.net` dari pekerjaan pendahulu dibiarkan sampai Google berhenti mengambilnya.
- [ ] Canonical di semua halaman menunjuk ke URL `.com`.
- [ ] Fitur Change of Address di Search Console dipakai bila ditawarkan untuk pasangan properti ini. Bila tidak ditawarkan, redirect 301 dan sitemap sudah cukup.
- [ ] Judul, deskripsi, dan Open Graph sama dengan versi lama, dengan `og:image` di alamat `.com`, agar pratinjau link di WhatsApp tidak berubah.
- [ ] `robots.txt` di alamat baru tidak memblokir halaman katalog atau aset gambar.
- [ ] Putuskan nasib `/brand/` di katalog. Halaman ini bisa diindeks, tidak punya canonical, dan isinya mirip helonoia.com, sehingga brand bersaing dengan dirinya sendiri di Google. Pilihannya: canonical ke `https://helonoia.com/`, atau teruskan langsung ke sana. Ini keputusan terpisah dan tidak menghalangi pindahan.
- [ ] Salinan cadangan di `felicidad126.github.io` tidak bisa diberi redirect, tetapi tidak perlu: canonical di setiap halaman sudah menunjuk ke `.com`.

### Checklist analytics

Belum ada analytics di kedua situs, jadi ini pemasangan baru, bukan pemindahan. Bagian ini bisa dikerjakan bersamaan dengan pindahan atau sesudahnya tanpa mengubah urutan di atas.

- [ ] Satu measurement ID / tag yang sama dipasang di helonoia.com dan `invitation.helonoia.com`. Karena keduanya satu akar domain, kunjungan dari situs utama ke katalog tercatat sebagai satu sesi tanpa pengaturan lintas domain.
- [ ] Klik WhatsApp tercatat sebagai event, dengan nama tema yang dipilih bila memungkinkan.
- [ ] Uji satu sesi penuh: buka helonoia.com, klik ke katalog `.com`, lalu klik WhatsApp. Ketiganya harus terlihat sebagai satu perjalanan.
- [ ] Bila analytics sudah terpasang sebelum hari-H, beri catatan tanggal pindah agar grafik sesudahnya bisa dibaca dengan benar.

> Harapan yang realistis soal pencarian: fluktuasi posisi Google selama 1–3 minggu setelah pindah adalah hal yang wajar. Dampaknya terbatas karena hanya beranda katalog yang terindeks. Meski begitu, pindahan jangan dilakukan tepat sebelum promosi besar.

### Tempat-tempat yang link-nya perlu diganti

| Tempat | Kapan diganti | Catatan |
| --- | --- | --- |
| helonoia.com (kartu katalog) | Fase 3 | `HTML/index.html` dan `README.md` di repo `helonoia`. Deploy otomatis saat merge ke `main` |
| Bio dan sorotan Instagram | Minggu 1 | Link lama tetap jalan via redirect |
| Template pesan WhatsApp | Minggu 1 | Termasuk pesan penawaran ke calon pembeli |
| Profil bisnis (Google, bila ada) | Minggu 1 | Sekalian cek nomor dan jam yang tampil |
| Link yang sudah terkirim ke tamu | Tidak bisa diganti | Inilah alasan redirect dipertahankan lama |

Baris terakhir adalah yang terpenting: link undangan yang sudah ada di ponsel para tamu tidak bisa ditarik kembali. Selama ada satu pun acara pelanggan yang masih akan berlangsung, redirect dari `.net` harus tetap menyala.

## Risiko utama dan cara menanganinya

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| Parameter `?to=` atau `?tema=` hilang saat redirect | Tinggi | Opsi A: centang Preserve query string. Opsi B: URL diteruskan utuh. Uji 3 link tema, 1 link demo, dan 1 link `/?to=` sebelum dan sesudah Fase 4 |
| SSL `.com` belum siap saat redirect dipasang | Tinggi | Urutan dikunci: SSL lolos uji dulu (Fase 1), redirect terakhir (Fase 4) |
| Redirect loop `.com` ↔ `.net` | Tinggi | Satu aturan redirect saja, di satu tempat, hanya untuk host `.net`. Uji dengan membuka URL lama dan baru bergantian |
| Redirect hilang karena deploy katalog (opsi B) | Tidak berlaku | Opsi A dipilih, jadi redirect tidak bergantung pada deploy katalog |
| `.net` mati saat pindah nameserver (opsi A) | Sedang | Salin semua record dulu dan bandingkan dengan panel NeoDNS. Kerjakan minimal 2 hari sebelum hari-H, lalu cek katalog `.net` tetap terbuka |
| Halaman atau aset 404 di alamat baru | Sedang | Inventaris Fase 0 menjadi daftar uji wajib, bukan contoh. Setelah 404 Noi terpasang, alamat yang hilang terlihat jelas |
| Konten ganda terindeks Google | Sedang | Selama pengujian canonical masih ke `.net` dan `.com` tidak ditautkan. Saat go-live: canonical `.com` + 301 |
| Isian RSVP dan ucapan di `.net` tidak terlihat di `.com` | Rendah | Data itu tersimpan di browser tamu dan terikat ke domain. Wajar untuk demo; beri tahu pelanggan bila undangan mereka memakai cara yang sama |
| Propagasi DNS lambat | Rendah | Record baru dibuat Cloudflare dengan TTL otomatis (5 menit). Pindah nameserver (opsi A) dikerjakan jauh sebelum hari-H |
| Domain `.net` tidak diperpanjang | Tinggi | Perpanjang `.net` minimal 12 bulan dan aktifkan perpanjangan otomatis sebelum go-live |

## Rencana rollback

Rollback sengaja dibuat sederhana. Isi katalog tidak dihapus selama pindahan, dan Pages menyimpan setiap deployment lama, jadi kembali ke kondisi semula hanya soal mematikan pengalihan.

1. Matikan redirect, dan katalog `.net` langsung melayani pengunjung lagi seperti semula:
   - Opsi A: nonaktifkan Redirect Rule di zona helonoia.net.
   - Opsi B: kembalikan deployment Pages ke versi sebelum middleware.
2. Kembalikan canonical dan `og:` ke `.net` dengan rollback deployment Pages ke ID yang dicatat di Fase 0. Versi itu sudah berisi 404, `robots.txt`, dan `sitemap.xml` versi `.net`.
3. Kembalikan link kartu katalog di helonoia.com ke alamat `.net` (revert commit di `main`).
4. Custom domain `.com` boleh tetap terpasang, karena canonical sudah kembali ke `.net`. Atau lepas dari Pages bila ingin benar-benar bersih.
5. Catat penyebab gagalnya, perbaiki tanpa tekanan waktu, lalu ulangi dari Fase 2.

**Batas keputusan rollback:** bila dalam 24 jam setelah Fase 4 ditemukan link tamu yang rusak, nama tamu yang hilang, atau error SSL yang meluas, lakukan rollback dulu dan perbaiki kemudian. Jangan memperbaiki sambil live.

## Estimasi waktu

| Tahap | Estimasi | Keterangan |
| --- | ---: | --- |
| Pekerjaan pendahulu (404, robots, sitemap) | Selesai | Aktif sejak 19 November 2026. Biarkan berjalan beberapa hari sebelum Fase 0 |
| Fase 0: Inventaris | 0,5 hari | Ditambah sampai 48 jam menunggu nameserver bila opsi A |
| Fase 1: Siapkan alamat baru | 1–2 jam | Custom domain + SSL, dan menyiapkan branch perubahan file |
| Fase 2: Pengujian | 0,5–1 hari | 10 tema + demo + link tamu + ponsel |
| Fase 3–4: Go-live dan redirect | 2–4 jam | Di jam sepi, satu sesi kerja |
| Fase 5: Pemantauan | 14–30 hari | Cek berkala, bukan kerja penuh |

Estimasi ini mengasumsikan katalog tetap statis di Cloudflare Pages, serta akses Cloudflare, registrar, dan repo tersedia saat dibutuhkan. Keterlambatan paling umum bukan di pekerjaan teknisnya, melainkan di menunggu akses atau perpindahan nameserver.

## Keputusan dan akses yang dibutuhkan sebelum mulai

Dokumen ini adalah planning saja. Eksekusi baru bisa dijadwalkan setelah hal-hal berikut jelas. Semuanya keputusan atau akses dari pemilik, bukan pekerjaan teknis tambahan.

### Keputusan yang perlu diambil

- **Cara redirect: diputuskan 19 November 2026, opsi A** (pindahkan DNS helonoia.net ke Cloudflare), karena redirect harus bertahan minimal 12 bulan dan tidak boleh ikut terhapus oleh deploy katalog.
- **Tanggal hari-H** dan jam sepi yang dipilih, dengan memperhatikan acara pelanggan yang sedang berjalan. Syarat dan contoh tanggalnya ada di [`JADWAL-PINDAH-DOMAIN.md`](JADWAL-PINDAH-DOMAIN.md).
- **Komitmen mempertahankan helonoia.net:** perpanjang minimal 12 bulan sejak go-live, idealnya selama masih ada acara pelanggan yang link-nya beredar.
- **Analytics:** dipasang bersamaan dengan pindahan atau sesudahnya.
- **Penyamaan header, footer, dan Noi di katalog:** dikerjakan langsung setelah pindah, atau ditunda sebagai proyek terpisah.

Keputusan soal hosting di versi sebelumnya tidak diperlukan lagi, karena alamat baru dilayani oleh proyek Pages yang sama.

### Akses yang perlu disiapkan (dipegang pemilik)

- **Akun Cloudflare** yang memegang proyek Pages `felicidad126-github-io` dan zona helonoia.com. Konfirmasi apakah keduanya satu akun.
- **Panel registrar dan NeoDNS helonoia.net:** untuk ganti nameserver (opsi A) dan verifikasi Search Console.
- **Repo sumber katalog** `felicidad126/felicidad126.github.io`: untuk perubahan file di Fase 1 dan 3.
- **Akun Google Search Console**, dan akun Google untuk analytics bila dipasang.
- **Konfirmasi registrar kedua domain** dan tanggal kedaluwarsanya masing-masing.

Cara berbagi akses yang aman:

- Akses diberikan saat eksekusi dimulai, sebatas yang dibutuhkan tiap fase.
- Kata sandi tidak ditulis di dokumen ini.
- Bila ada langkah yang hanya bisa dilakukan dari akun pemilik, langkah itu dikerjakan pemilik dengan panduan urutan dari rencana ini.

## Checklist ringkas

- [x] 404 Noi, `robots.txt`, dan `sitemap.xml` terpasang di `.net` dan teruji.
- [ ] Inventaris URL, tempat link tersebar, dan akses: selesai dan tercatat.
- [ ] ID deployment produksi Pages saat ini tercatat sebagai titik rollback.
- [ ] (Opsi A) helonoia.net aktif di Cloudflare, dan katalog `.net` tetap terbuka normal.
- [ ] `invitation.helonoia.com` terpasang sebagai custom domain Pages, dan HTTPS terbuka tanpa peringatan.
- [ ] Beranda, 10 tema, demo, RSVP, galeri, peta, dan amplop teruji di ponsel di alamat `.com`.
- [ ] Contoh link `/<tema>/?to=`, `/demo/?tema=…&to=…`, dan `/?to=` menampilkan nama tamu yang benar di `.com`.
- [ ] Canonical, `og:url`, `og:image`, `robots.txt`, dan `sitemap.xml` menunjuk ke `.com`, dan sitemap `.com` terkirim ke Search Console.
- [ ] Link di helonoia.com sudah menunjuk ke `invitation.helonoia.com`.
- [ ] Redirect 301 `.net` ke `.com` aktif: satu lompatan, query string utuh, tanpa loop.
- [ ] Seluruh daftar URL lama diuji ulang dari sisi `.net`.
- [ ] Domain `.net` diperpanjang dan perpanjangan otomatis aktif.
- [ ] Pemantauan hari 1–3, minggu 1–2, dan tinjauan hari ke-30 terjadwal.

Jadwal hari-H per jam ada di [`JADWAL-PINDAH-DOMAIN.md`](JADWAL-PINDAH-DOMAIN.md). Begitu tanggal hari-H dipilih, yang diisi adalah jadwal itu, bukan rencana ini.
