# Deploy Halaman Helonoia ke Server Sendiri

Halaman brand Helonoia adalah situs statis. Seluruhnya hanya 3 file di folder [`HTML/`](HTML/):

| File | Isi |
|---|---|
| `index.html` | Halamannya (maskot, tulisan logo, CSS, dan JavaScript sudah di dalam file ini) |
| `favicon.svg` | Ikon di tab browser |
| `logo.png` | Ikon saat halaman disimpan ke layar utama HP |

Tidak butuh PHP, database, Node.js, atau proses build. Huruf (Fredoka dan Plus Jakarta Sans) dimuat dari Google Fonts oleh browser pengunjung.

Panduan ini memakai contoh berikut. Ganti dengan milikmu bila berbeda:

- **Server:** VPS Ubuntu 22.04 / 24.04 (Debian juga sama), bisa SSH dengan akses `sudo`
- **Domain:** `helonoia.net` dan `www.helonoia.net`
- **Web server:** Nginx, dengan HTTPS gratis dari Let's Encrypt

Kalau yang kamu punya hosting cPanel (bukan VPS), langsung ke bagian [Kalau pakai shared hosting (cPanel)](#kalau-pakai-shared-hosting-cpanel).

---

## Langkah 0: Siapkan

- **IP publik server**, misalnya `203.0.113.10`. Di panduan ini ditulis `IP-SERVER`.
- **Akses ke pengaturan DNS domain**, yaitu tempat domain helonoia.net dikelola (kemungkinan Cloudflare, karena invitation.helonoia.net ada di Cloudflare Pages).
- **Port 80 dan 443 terbuka.** Selain firewall di dalam server, cek juga firewall/security group di panel penyedia VPS.

---

## Langkah 1: Arahkan domain ke server

Di pengaturan DNS domain, buat (atau ubah) dua record ini:

| Type | Name | Content / Target |
|---|---|---|
| `A` | `@` (artinya `helonoia.net`) | `IP-SERVER` |
| `A` | `www` | `IP-SERVER` |

> ⚠️ **Jangan ubah atau hapus record `invitation`.** Record itu yang menjalankan katalog undangan di invitation.helonoia.net.

Kalau DNS-nya di **Cloudflare**, set *Proxy status* kedua record di atas ke **DNS only** (awan abu-abu) dulu. Proxy bisa dinyalakan lagi setelah HTTPS di Langkah 5 berhasil.

Cek dari komputermu. Hasilnya harus IP server (perubahan DNS bisa butuh beberapa menit sampai beberapa jam):

```bash
nslookup helonoia.net
```

---

## Langkah 2: Masuk ke server dan pasang Nginx

Masuk ke server:

```bash
ssh namauser@IP-SERVER
```

Pasang Nginx:

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

---

## Langkah 3: Salin file halaman ke server

Pilih salah satu cara.

### Cara A: ambil langsung dari GitHub (di server)

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

### Cara B: kirim dari komputermu

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

### Setelah memakai cara A atau B

Pastikan file bisa dibaca web server, lalu cek isinya:

```bash
sudo chmod -R a+rX /var/www/helonoia
```

```bash
ls -l /var/www/helonoia
```

Harus terlihat `index.html`, `favicon.svg`, dan `logo.png`, **langsung** di dalam `/var/www/helonoia` (bukan di subfolder `HTML`).

---

## Langkah 4: Atur Nginx untuk domain

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

---

## Langkah 5: Pasang HTTPS (gratis, Let's Encrypt)

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

## Langkah 6: Periksa hasilnya

- [ ] `https://helonoia.net` membuka halaman Helonoia, dengan gembok di address bar
- [ ] `http://helonoia.net` dan `https://www.helonoia.net` ikut pindah ke halaman yang sama
- [ ] Ikon tab berupa monster ungu
- [ ] Maskot bergerak dan matanya mengikuti kursor
- [ ] Tombol "Sapa balik" membuat maskot melambai dan menjawab
- [ ] https://invitation.helonoia.net tetap membuka katalog undangan

---

## Memperbarui halaman nanti

Kalau `HTML/index.html` di repo berubah:

**Cara A (GitHub):**

```bash
git -C ~/helonoia-src pull
```

```bash
sudo cp -r ~/helonoia-src/HTML/. /var/www/helonoia/
```

**Cara B:** ulangi Langkah 3 Cara B.

Tidak perlu me-reload Nginx. Kalau browser masih menampilkan versi lama, tekan Ctrl+F5 (atau Cmd+Shift+R di Mac).

---

## (Opsional) Gambar pratinjau saat link dibagikan

Saat link dibagikan di WhatsApp atau media sosial, gambar pratinjaunya diambil dari baris `og:image` di `HTML/index.html`. Sekarang baris itu mengarah ke `https://invitation.helonoia.net/helonoia/helonoia_logo.png`, dan itu sudah berfungsi.

Kalau ingin memakai domain sendiri, ubah baris itu **di repo** (supaya tidak tertimpa saat update) menjadi:

```html
<meta property="og:image" content="https://helonoia.net/logo.png">
```

---

## Kalau pakai shared hosting (cPanel)

1. Arahkan domain ke hosting sesuai petunjuk penyedia (biasanya lewat *nameserver* atau record `A`). Jangan ubah record `invitation`.
2. Buka **cPanel → File Manager → `public_html`** (atau folder milik domain itu).
3. Unggah `index.html`, `favicon.svg`, dan `logo.png` **langsung ke dalam** `public_html`, bukan ke subfolder `HTML`. Kalau sudah ada `index.html` atau `index.php` bawaan hosting, ganti atau hapus dulu.
4. Pasang HTTPS di **cPanel → SSL/TLS Status → Run AutoSSL** (di beberapa hosting namanya menu "Let's Encrypt").
5. Buka `https://domainmu`.

---

## Kalau ada masalah

| Gejala | Penyebab dan perbaikan |
|---|---|
| `nginx -t` gagal dengan pesan `Address family not supported` | Server tidak mendukung IPv6. Hapus baris `listen [::]:80;` di `/etc/nginx/sites-available/helonoia`, lalu `sudo nginx -t` lagi. |
| Domain masih menampilkan "Welcome to nginx!" | Situs bawaan masih aktif atau `server_name` salah ketik. Cek isi `/etc/nginx/sites-enabled/`, lalu `sudo systemctl reload nginx`. |
| `403 Forbidden` | File tidak terbaca atau `index.html` tidak ada. Jalankan `ls -l /var/www/helonoia` dan `sudo chmod -R a+rX /var/www/helonoia`. |
| `404 Not Found` di halaman utama | File tersalin ke `/var/www/helonoia/HTML/`, bukan langsung ke `/var/www/helonoia/`. Pindahkan isinya satu folder ke atas. |
| Certbot gagal | DNS belum mengarah ke server (cek `nslookup helonoia.net`), port 80 tertutup di firewall penyedia VPS, atau proxy Cloudflare masih menyala. Set ke *DNS only*, lalu ulangi. |
| `Too many redirects` | Mode SSL Cloudflare masih *Flexible*. Ubah ke **Full (strict)**. |
| Ikon tab tidak muncul | `favicon.svg` belum ikut diunggah. Browser juga sering menyimpan ikon lama, jadi coba di jendela privat. |
