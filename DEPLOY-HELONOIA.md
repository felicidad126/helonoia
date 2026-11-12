# Deploy Halaman Helonoia ke Server Sendiri

Halaman brand Helonoia adalah situs statis. Seluruhnya hanya 3 file di folder [`HTML/`](HTML/):

| File | Isi |
|---|---|
| `index.html` | Halamannya (maskot, tulisan logo, CSS, dan JavaScript sudah di dalam file ini) |
| `favicon.svg` | Ikon di tab browser |
| `logo.png` | Ikon saat halaman disimpan ke layar utama HP |

Tidak butuh PHP, database, Node.js, atau proses build. Huruf (Fredoka dan Plus Jakarta Sans) dimuat dari Google Fonts oleh browser pengunjung.

## Pilih jalur

| Jalur | Cocok untuk |
|---|---|
| **[A. aaPanel](#jalur-a-aapanel)** | Satu server untuk **banyak website**, semuanya dikelola lewat dasbor di browser (website, SSL, file) |
| [B. Nginx manual](#jalur-b-nginx-manual) | Server khusus untuk satu atau dua website, tanpa panel |
| [C. cPanel](#jalur-c-shared-hosting-cpanel) | Shared hosting yang sudah menyediakan cPanel |

Contoh di panduan ini (ganti dengan milikmu bila berbeda):

- **Server:** VPS Ubuntu 22.04 (versi yang disarankan aaPanel), bisa SSH dengan akses `sudo`
- **Domain:** `helonoia.net` dan `www.helonoia.net`

> ⚠️ Pilih **satu** jalur per server. Jangan memasang Nginx dari Jalur B di server yang akan dipasangi aaPanel, karena aaPanel memasang dan mengatur Nginx-nya sendiri.

---

## Langkah 0: Siapkan (semua jalur)

- **IP publik server**, misalnya `203.0.113.10`. Di panduan ini ditulis `IP-SERVER`.
- **Akses ke pengaturan DNS domain**, yaitu tempat domain helonoia.net dikelola (kemungkinan Cloudflare, karena invitation.helonoia.net ada di Cloudflare Pages).
- **Untuk aaPanel:** sebaiknya server baru yang masih kosong, minimal 1 core CPU dan 512 MB RAM (disarankan 1 GB). Kalau akan dipakai untuk banyak website, ambil RAM lebih besar.

---

## Langkah 1: Arahkan domain ke server (semua jalur)

Di pengaturan DNS domain, buat (atau ubah) dua record ini:

| Type | Name | Content / Target |
|---|---|---|
| `A` | `@` (artinya `helonoia.net`) | `IP-SERVER` |
| `A` | `www` | `IP-SERVER` |

> ⚠️ **Jangan ubah atau hapus record `invitation`.** Record itu yang menjalankan katalog undangan di invitation.helonoia.net.

Kalau DNS-nya di **Cloudflare**, set *Proxy status* kedua record di atas ke **DNS only** (awan abu-abu) dulu. Proxy bisa dinyalakan lagi setelah HTTPS berhasil dipasang.

Website lain yang akan ditaruh di server yang sama diarahkan dengan cara yang sama: record `A` domainnya menuju `IP-SERVER`.

Cek dari komputermu. Hasilnya harus IP server (perubahan DNS bisa butuh beberapa menit sampai beberapa jam):

```bash
nslookup helonoia.net
```

---

## Jalur A: aaPanel

aaPanel adalah panel gratis untuk mengelola banyak website di satu server. Langkah ini mengikuti dokumentasi resmi di [aapanel.com/docs](https://www.aapanel.com/docs/guide/quickstart.html) (aaPanel 8.0.7, November 2026). Nama menu bisa sedikit berbeda di versi lain.

### A1. Instal aaPanel

Masuk ke server dan jadi root (installer aaPanel wajib dijalankan sebagai root):

```bash
ssh namauser@IP-SERVER
```

```bash
sudo -i
```

Unduh installer resmi, lalu jalankan:

```bash
curl -fsSLO https://www.aapanel.com/script/install_panel_en.sh
```

```bash
bash install_panel_en.sh
```

- Saat ditanya `Do you want to install aaPanel to the /www directory now?(y/n)`, ketik `y` lalu Enter.
- Kalau muncul `Web service is already installed` dan diminta mengetik `yes`, berarti server ini sudah punya web server lain (misalnya dari Jalur B). **Jangan ketik `yes` dulu.** Lihat baris pertama tabel [Kalau ada masalah](#kalau-ada-masalah).
- Instalasi butuh beberapa menit.

Di akhir instalasi muncul kira-kira seperti ini. **Simpan alamat, username, dan password-nya:**

```
aaPanel Internet Address: https://IP-SERVER:PORT/xxxxxxxx
username: xxxxxxxx
password: xxxxxxxx
```

- `PORT` dipilih **acak** saat instalasi (angka 10000 sampai 65534). Bagian `/xxxxxxxx` di ujung alamat adalah "pintu masuk" panel, jadi rahasiakan alamat lengkapnya.
- Lupa mencatat? Jalankan `bt default` di server. Lupa password? Jalankan `bt 5` untuk menggantinya.

Catatan: perintah di situs aaPanel mengunduh installer dengan `curl -k`, yang mematikan pemeriksaan sertifikat HTTPS. Perintah di atas tetap memeriksa sertifikat, dan hasilnya file yang sama.

### A2. Buka port di firewall penyedia VPS

Installer sudah membuka port di firewall **dalam** server (UFW). Tapi kalau penyedia VPS punya firewall/security group sendiri di panelnya, buka juga di sana:

| Port | Untuk |
|---|---|
| `PORT` panel (dari A1) | Membuka dasbor aaPanel |
| `80` dan `443` | Website (HTTP dan HTTPS) |
| `22` | SSH |

aaPanel juga menyarankan port 20, 21 (FTP) dan 888 (phpMyAdmin). Buka hanya kalau kamu memakainya.

### A3. Masuk ke panel dan pasang Nginx

1. Buka alamat dari A1 di browser. Browser akan memberi peringatan sertifikat karena aaPanel memakai sertifikat buatan sendiri. Itu normal, jadi lanjutkan.
2. Login dengan username dan password dari A1, lalu segera ganti password di pengaturan panel.
3. Saat pertama masuk, aaPanel menawarkan paket software. Pilih **LNMP** (paket yang memakai Nginx), sesuai saran dokumentasi aaPanel.
   - Untuk Helonoia, cukup **Nginx** karena halamannya statis.
   - PHP dan MySQL hanya perlu kalau website lainmu memakainya (misalnya WordPress). Bisa dipasang belakangan dari **App Store**.
4. Tunggu sampai instalasi selesai. Prosesnya terlihat di daftar tugas panel.

### A4. Tambah website Helonoia

Buka **Website → Add site → Create single site**, lalu isi:

| Isian | Nilai |
|---|---|
| Domain name | `helonoia.net` dan `www.helonoia.net` (satu domain per baris) |
| Website Path | `/www/wwwroot/helonoia.net` (biarkan sesuai isian otomatis) |
| FTP | Tidak dibuat |
| Database | Tidak dibuat |
| PHP version | Pilih opsi statis (biasanya tertulis **Static**), karena halaman ini tidak memakai PHP |

Klik **Submit**.

### A5. Unggah file halaman

Pilih salah satu cara.

**Lewat panel:** buka menu **Files**, masuk ke `/www/wwwroot/helonoia.net`, hapus `index.html` bawaan aaPanel, lalu **Upload** `index.html`, `favicon.svg`, dan `logo.png` dari folder `HTML/` repo ini. Ketiganya diletakkan **langsung** di folder itu, bukan di subfolder `HTML`.

**Lewat SSH (sebagai root):**

```bash
git clone --depth 1 https://github.com/felicidad126/felicidad126.github.io.git ~/helonoia-src
```

```bash
cp -r ~/helonoia-src/HTML/. /www/wwwroot/helonoia.net/
```

```bash
chown -R www:www /www/wwwroot/helonoia.net
```

Perintah `git clone` mengambil branch `main`. Pastikan perubahan terbaru sudah di-merge ke `main`.

Cek: buka `http://helonoia.net`. Halaman Helonoia harus muncul (masih tanpa gembok).

### A6. Pasang HTTPS (gratis, Let's Encrypt)

1. Di **Website**, klik nama situs `helonoia.net` (atau tombol **Conf**), lalu buka bagian **SSL**.
2. Pilih **Let's Encrypt**, metode **File verification**, centang kedua domain (`helonoia.net` dan `www.helonoia.net`), lalu **Apply**.
3. Setelah sertifikat terpasang, nyalakan **Force HTTPS** supaya `http://` otomatis pindah ke `https://`.

Sertifikat diperpanjang otomatis oleh aaPanel.

**Kalau DNS di Cloudflare:** saat meminta sertifikat, record harus masih *DNS only*. Kalau nanti proxy (awan oranye) dinyalakan, buka **SSL/TLS → Overview** di Cloudflare dan pilih **Full (strict)**. Proxy Cloudflare dengan mode *Flexible* ditambah Force HTTPS menghasilkan error *too many redirects*. Dokumentasi aaPanel juga memperingatkan hal ini.

### A7. Menambah website lain di server yang sama

Untuk setiap website berikutnya:

1. Arahkan domainnya ke `IP-SERVER` ([Langkah 1](#langkah-1-arahkan-domain-ke-server-semua-jalur)).
2. Ulangi **A4** (Add site dengan domain itu). Pilih versi PHP yang sesuai kalau situsnya memakai PHP.
3. Unggah file situsnya seperti **A5**, ke folder `/www/wwwroot/<domain>` miliknya.
4. Pasang HTTPS seperti **A6**.

Setiap website punya folder dan pengaturannya sendiri, jadi tidak saling mengganggu.

### Menjaga keamanan panel

Panel kontrol seperti aaPanel adalah sasaran serangan yang umum, dan beberapa kali pernah ditemukan celah keamanan. Karena satu server ini menampung banyak website:

- Perbarui aaPanel setiap ada versi baru (pemberitahuannya muncul di dasbor).
- Rahasiakan alamat panel lengkap (dengan bagian `/xxxxxxxx`-nya) dan pakai password yang kuat.
- Kalau firewall penyedia VPS bisa membatasi alamat IP, izinkan port panel hanya dari IP-mu.
- Aktifkan backup berkala, baik dari panel maupun dari penyedia VPS.

---

## Jalur B: Nginx manual

### B1. Pasang Nginx

Masuk ke server:

```bash
ssh namauser@IP-SERVER
```

```bash
sudo apt update
```

```bash
sudo apt install -y nginx
```

Kalau firewall UFW aktif (cek dengan `sudo ufw status`), buka port web:

```bash
sudo ufw allow 'Nginx Full'
```

Cek: buka `http://IP-SERVER` di browser. Harus muncul halaman **"Welcome to nginx!"**.

### B2. Salin file halaman ke server

**Cara 1: ambil langsung dari GitHub (di server)**

```bash
sudo apt install -y git
```

```bash
git clone --depth 1 https://github.com/felicidad126/felicidad126.github.io.git ~/helonoia-src
```

```bash
sudo mkdir -p /var/www/helonoia
```

```bash
sudo cp -r ~/helonoia-src/HTML/. /var/www/helonoia/
```

Perintah ini mengambil branch `main`. Pastikan perubahan terbaru sudah di-merge ke `main`.

**Cara 2: kirim dari komputermu**

Dari folder repo ini di komputermu (bukan di server):

```bash
scp HTML/index.html HTML/favicon.svg HTML/logo.png namauser@IP-SERVER:~/
```

Lalu di server:

```bash
sudo mkdir -p /var/www/helonoia
```

```bash
sudo mv ~/index.html ~/favicon.svg ~/logo.png /var/www/helonoia/
```

Di Windows, bisa juga memakai WinSCP atau FileZilla untuk mengunggah ketiga file itu.

**Setelah cara 1 atau 2:** pastikan file bisa dibaca web server, lalu cek isinya.

```bash
sudo chmod -R a+rX /var/www/helonoia
```

```bash
ls -l /var/www/helonoia
```

Harus terlihat `index.html`, `favicon.svg`, dan `logo.png`, **langsung** di dalam `/var/www/helonoia` (bukan di subfolder `HTML`).

### B3. Atur Nginx untuk domain

Buat file konfigurasi. Kalau domainmu bukan helonoia.net, **ganti dulu** baris `server_name` sebelum menempel perintah ini:

```bash
sudo tee /etc/nginx/sites-available/helonoia > /dev/null <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name helonoia.net www.helonoia.net;

    root /var/www/helonoia;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # Gambar boleh disimpan browser selama 7 hari
    location ~* \.(?:svg|png)$ {
        expires 7d;
        add_header Cache-Control "public";
    }

    gzip on;
    gzip_types image/svg+xml;
}
EOF
```

Aktifkan:

```bash
sudo ln -s /etc/nginx/sites-available/helonoia /etc/nginx/sites-enabled/
```

Kalau server ini **hanya** untuk Helonoia (tidak ada situs lain), matikan halaman bawaan Nginx:

```bash
sudo rm /etc/nginx/sites-enabled/default
```

Uji konfigurasi. Harus muncul `syntax is ok` dan `test is successful`:

```bash
sudo nginx -t
```

Terapkan:

```bash
sudo systemctl reload nginx
```

Cek: buka `http://helonoia.net`. Halaman Helonoia harus muncul (masih tanpa gembok, itu dipasang di langkah berikutnya).

Untuk website lain di server yang sama, buat satu file konfigurasi lagi per domain dengan `server_name` dan `root` miliknya.

### B4. Pasang HTTPS (gratis, Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
```

```bash
sudo certbot --nginx -d helonoia.net -d www.helonoia.net
```

Certbot akan menanyakan email dan persetujuan syarat layanan. Setelah itu ia memasang sertifikat dan mengubah konfigurasi Nginx sendiri. Kalau ditanya soal *redirect*, pilih supaya `http://` dialihkan ke `https://`.

Sertifikat berlaku 90 hari dan diperpanjang otomatis. Cek bahwa perpanjangannya jalan:

```bash
sudo certbot renew --dry-run
```

**Kalau DNS di Cloudflare** dan kamu mau menyalakan proxy (awan oranye) lagi: nyalakan, lalu di Cloudflare buka **SSL/TLS → Overview** dan pilih **Full (strict)**. Jangan pilih *Flexible*, karena akan membuat halaman terus-menerus dialihkan (*too many redirects*).

---

## Jalur C: Shared hosting (cPanel)

1. Arahkan domain ke hosting sesuai petunjuk penyedia (biasanya lewat *nameserver* atau record `A`). Jangan ubah record `invitation`.
2. Buka **cPanel → File Manager → `public_html`** (atau folder milik domain itu).
3. Unggah `index.html`, `favicon.svg`, dan `logo.png` **langsung ke dalam** `public_html`, bukan ke subfolder `HTML`. Kalau sudah ada `index.html` atau `index.php` bawaan hosting, ganti atau hapus dulu.
4. Pasang HTTPS di **cPanel → SSL/TLS Status → Run AutoSSL** (di beberapa hosting namanya menu "Let's Encrypt").
5. Buka `https://domainmu`.

---

## Periksa hasilnya (semua jalur)

- [ ] `https://helonoia.net` membuka halaman Helonoia, dengan gembok di address bar
- [ ] `http://helonoia.net` dan `https://www.helonoia.net` ikut pindah ke halaman yang sama
- [ ] Ikon tab berupa monster ungu
- [ ] Maskot bergerak dan matanya mengikuti kursor
- [ ] Tombol "Sapa balik" membuat maskot melambai dan menjawab
- [ ] https://invitation.helonoia.net tetap membuka katalog undangan

---

## Memperbarui halaman nanti

Kalau `HTML/index.html` di repo berubah:

**aaPanel (sebagai root):**

```bash
git -C ~/helonoia-src pull
```

```bash
cp -r ~/helonoia-src/HTML/. /www/wwwroot/helonoia.net/
```

Atau unggah ulang ketiga file lewat menu **Files**.

**Nginx manual:**

```bash
git -C ~/helonoia-src pull
```

```bash
sudo cp -r ~/helonoia-src/HTML/. /var/www/helonoia/
```

**cPanel:** unggah ulang ketiga file.

Web server tidak perlu di-restart. Kalau browser masih menampilkan versi lama, tekan Ctrl+F5 (atau Cmd+Shift+R di Mac).

---

## Gambar pratinjau saat link dibagikan

Baris `og:image` di `HTML/index.html` mengarah ke `https://helonoia.com/logo.png`. Gambar ini hanya muncul kalau `logo.png` di server berisi gambar sungguhan. Cek ukurannya di menu **Files**: harus sekitar 60 KB, bukan 0 B.

---

## Kalau ada masalah

| Gejala | Penyebab dan perbaikan |
|---|---|
| Installer aaPanel berhenti dengan `Web service is already installed` | Server sudah punya Nginx, Apache, PHP, atau MySQL dari luar aaPanel (misalnya dari Jalur B). Pakai server baru, **atau** kalau server itu belum menjalankan situs apa pun, hapus Nginx lama dengan `sudo apt purge -y nginx nginx-common` lalu jalankan installer lagi. |
| Dasbor aaPanel tidak bisa dibuka | Port panel belum dibuka di firewall penyedia VPS (lihat A2), atau alamatnya kurang bagian `/xxxxxxxx` di ujungnya. Jalankan `bt default` untuk melihat alamat lengkapnya. |
| Lupa password aaPanel | Jalankan `bt 5` di server (sebagai root). |
| Situs masih menampilkan halaman bawaan aaPanel | `index.html` bawaan belum diganti, atau file terunggah ke subfolder. Cek isi `/www/wwwroot/helonoia.net` di menu **Files**. |
| `nginx -t` gagal dengan pesan `Address family not supported` (Jalur B) | Server tidak mendukung IPv6. Hapus baris `listen [::]:80;` di `/etc/nginx/sites-available/helonoia`, lalu `sudo nginx -t` lagi. |
| Domain masih menampilkan "Welcome to nginx!" (Jalur B) | Situs bawaan masih aktif atau `server_name` salah ketik. Cek isi `/etc/nginx/sites-enabled/`, lalu `sudo systemctl reload nginx`. |
| `403 Forbidden` | File tidak terbaca atau `index.html` tidak ada. Jalur B: `sudo chmod -R a+rX /var/www/helonoia`. aaPanel: `chown -R www:www /www/wwwroot/helonoia.net`. |
| `404 Not Found` di halaman utama | File tersalin ke subfolder `HTML/`, bukan langsung ke folder situs. Pindahkan isinya satu folder ke atas. |
| Sertifikat Let's Encrypt gagal | DNS belum mengarah ke server (cek `nslookup helonoia.net`), port 80 tertutup di firewall penyedia VPS, atau proxy Cloudflare masih menyala. Set ke *DNS only*, lalu ulangi. |
| `Too many redirects` | Mode SSL Cloudflare masih *Flexible*. Ubah ke **Full (strict)**. |
| Ikon tab tidak muncul | `favicon.svg` belum ikut diunggah, atau ukurannya 0 B (unduhan gagal, unggah ulang). Browser juga sering menyimpan ikon lama, jadi coba di jendela privat. |
