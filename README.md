# CekURL — Pemeriksa Keamanan Tautan

CekURL membantu masyarakat Indonesia memeriksa apakah sebuah tautan (URL)
aman diklik atau patut dicurigai — sebelum membuka tautan dari pesan
WhatsApp, SMS, atau email yang mencurigakan.

Tempel tautannya, CekURL memberi **skor risiko 0–100** beserta alasannya
dalam Bahasa Indonesia: `AMAN`, `WASPADA`, atau `BAHAYA`.

Sepenuhnya offline, tanpa dependensi tambahan — cukup Python 3.10+.

## Cara memakai

### Cek satu tautan

```bash
python -m cekurl.cli cek https://www.google.com
```

```
Tautan : https://www.google.com
Skor   : 0/100 — AMAN
Reputasi: 100/100 — TERPERCAYA
Tidak ditemukan sinyal mencurigakan.
```

Tautan tanpa skema otomatis dilengkapi `https://`, dan skema selain
`http`/`https` (mis. `ftp`) ditolak dengan pesan error.

```bash
python -m cekurl.cli cek www.google.com   # sama dengan https://www.google.com
```

### Keluaran JSON

Untuk dipakai program lain, tambahkan `--json`:

```bash
python -m cekurl.cli cek https://www.google.com --json
```

```json
{
  "url": "https://www.google.com",
  "host": "www.google.com",
  "skor": 0,
  "verdict": "AMAN",
  "sinyal": [],
  "reputasi": {
    "skor": 100,
    "tier": "TERPERCAYA",
    "faktor": [
      {
        "alasan": "Domain resmi terverifikasi (daftar putih bawaan: google.com).",
        "poin": 50
      }
    ]
  },
  "catatan": "Domain resmi terverifikasi (daftar putih bawaan: google.com)."
}
```

### Cek tautan dari teks pesan

Tempel pesan WhatsApp/SMS sebagai argumen — atau lewat stdin bila tanpa
argumen — dan semua tautan di dalamnya diperiksa satu per satu:

```bash
python -m cekurl.cli pesan "Halo! Paket kamu tertunda, klaim di https://bit.ly/paket-tertunda ya. Info resmi: https://www.bca.co.id"

echo "Cek https://dana-promo.com/klaim-bonus ya" | python -m cekurl.cli pesan
```

```
1. https://bit.ly/paket-tertunda
   Skor: 35/100 — WASPADA
   Sinyal: Pemendek URL (bit.ly) menyembunyikan tujuan asli tautan.; Kata mencurigakan di tautan: paket, tertunda.
2. https://www.bca.co.id
   Skor: 0/100 — AMAN
Ringkasan: 2 tautan — AMAN 1, WASPADA 1, BAHAYA 0
```

### Cek banyak tautan (batch)

Satu URL per baris; baris kosong dan komentar (`#`) dilewati:

```bash
python -m cekurl.cli batch --berkas contoh/cekurl-contoh.txt
```

```
1. https://www.google.com
   Skor: 0/100 — AMAN
2. https://www.bca.co.id
   Skor: 0/100 — AMAN
3. https://bit.ly/paket-tertunda
   Skor: 35/100 — WASPADA
   Sinyal: Pemendek URL (bit.ly) menyembunyikan tujuan asli tautan.; Kata mencurigakan di tautan: paket, tertunda.
4. http://203.0.113.5/login-gratis
   Skor: 60/100 — BAHAYA
   Sinyal: Tautan tidak terenkripsi (http, bukan https).; Host memakai alamat IP langsung, bukan nama domain.; Kata mencurigakan di tautan: gratis, login.
5. https://bca-co.id/verifikasi-hadiah
   Skor: 45/100 — WASPADA
   Sinyal: Domain meniru brand BCA — domainnya mirip domain resmi BCA (bca.co.id) — kemungkinan salah ketik yang disengaja (resmi: bca.co.id).; Kata mencurigakan di tautan: hadiah, verifikasi.
Ringkasan: 5 tautan — AMAN 2, WASPADA 2, BAHAYA 1
```

Bila berkasnya tidak ada, CekURL memberi pesan yang jelas dan keluar
dengan kode 1:

```
Error: berkas '/tmp/cekurl-tidak-ada.txt' tidak ditemukan. Periksa lagi nama dan lokasi berkasnya.
```

### Instal sekali, pakai perintah `cekurl`

```bash
pip install .
cekurl cek https://www.google.com
cekurl --version   # cekurl 0.1.0
```

## Contoh nyata dengan angka

| Tautan | Skor | Verdict | Reputasi | Sinyal yang terhitung |
| --- | --- | --- | --- | --- |
| `https://www.google.com` | 0 | AMAN | 100 TERPERCAYA | — |
| `https://www.bca.co.id` | 0 | AMAN | 100 TERPERCAYA | — |
| `https://bit.ly/paket-tertunda` | 35 | WASPADA | 35 MERAGUKAN | Pemendek URL +15, kata kunci paket & tertunda +20 |
| `https://dana-promo.com/klaim-bonus` | 45 | WASPADA | 30 MERAGUKAN | Meniru brand DANA +25, kata kunci bonus, klaim & promo +20 |
| `https://bca-co.id/verifikasi-hadiah` | 45 | WASPADA | 40 NETRAL | Meniru brand BCA +25, kata kunci hadiah & verifikasi +20 |
| `http://203.0.113.5/login-gratis` | 60 | BAHAYA | 0 MERAGUKAN | http +10, alamat IP +30, kata kunci gratis & login +20 |

Kolom Reputasi adalah skor reputasi domainnya (lihat perintah `reputasi`
di bawah): domain resmi terverifikasi selalu 100, alamat IP selalu 0.

## Yang diperiksa — sinyal dan poin

| Sinyal | Poin | Keterangan |
| --- | --- | --- |
| Skema `http` | +10 | Tautan tidak terenkripsi |
| Host berupa alamat IP | +30 | Tautan memakai angka IP, bukan nama domain |
| Pemendek URL | +15 | bit.ly, s.id, tinyurl, dan sejenisnya menyembunyikan tujuan asli |
| TLD rawan disalahgunakan | +10 | `.xyz`, `.top`, `.click`, dan sejenisnya |
| Punycode (`xn--`) | +15 | Karakter non-ASCII yang disamarkan |
| Trik `@` di tengah URL | +25 | Bagian sebelum `@` diabaikan browser |
| Domain meniru brand lokal | +25 | Typo-squat, brand di label lain, atau TLD berbeda |
| Subdomain berlapis (≥ 5 bagian) | +10 | Sering dipakai untuk menyamar |
| Nama domain sangat panjang (> 30 karakter) | +5 | Pola tautan menipu |
| Banyak tanda hubung (≥ 4) | +5 | Pola tautan menipu |
| Port tidak standar | +5 | Bukan port 80/443 |
| Kata kunci phishing | +10 per kata, maks +20 | `verifikasi`, `hadiah`, `gratis`, `klaim`, `blokir`, dan sejenisnya |

Kata kunci yang merupakan bagian dari kata kunci lain (mis. `verif` di
dalam `verifikasi`) hanya dihitung sekali.

## Daftar putih domain resmi

Domain resmi yang sudah dikenal — domain brand lokal (BCA, BRI, GoPay,
Shopee, dan seterusnya), layanan global tepercaya (Google, GitHub,
Wikipedia, dan sejenisnya), serta semua domain berakhiran `.go.id`,
`.ac.id`, dan `.sch.id` — langsung dinilai **AMAN (skor 0)** apa pun isi
tautannya. Alasannya sederhana: penipu tidak bisa memakai domain resmi
itu; yang mereka pakai adalah domain *mirip* (typo-squat, TLD berbeda),
dan domain mirip itu tetap tertangkap deteksi brand.

```bash
python -m cekurl.cli cek https://www.bca.co.id
```

```
Tautan : https://www.bca.co.id
Skor   : 0/100 — AMAN
Reputasi: 100/100 — TERPERCAYA
Domain resmi terverifikasi (daftar putih bawaan: bca.co.id).
Tidak ditemukan sinyal mencurigakan.
```

Periksa apakah sebuah domain ada di daftar putih:

```bash
python -m cekurl.cli putih cek bca.co.id        # ada → keluar 0
python -m cekurl.cli putih cek bca-co.id        # tidak ada → keluar 1
```

### Daftar putih kustom (domain kepercayaan sendiri)

Punya domain yang kamu percaya tapi belum ada di daftar bawaan — mis.
situs kampus atau kantor? Tambahkan sendiri; tersimpan di
`~/.config/cekurl/putih.json` dan langsung dipakai perintah `cek`:

```bash
python -m cekurl.cli putih tambah kampusku.ac.id
python -m cekurl.cli putih daftar     # lihat isi daftar putih
python -m cekurl.cli putih hapus kampusku.ac.id
```

Domain yang sudah ada di daftar bawaan tidak bisa ditambahkan lagi, dan
domain kustom yang sudah terdaftar tidak bisa ditambahkan dua kali —
keduanya ditolak dengan pesan yang jelas.

## Deteksi brand lokal

CekURL mengenali 19 brand Indonesia — bank (BCA, BRI, Mandiri, BNI, CIMB,
Danamon, Permata), e-wallet (GoPay, DANA, OVO), e-commerce (Shopee,
Tokopedia, Lazada, Bukalapak, Blibli), serta PLN, Telkomsel, Kominfo, dan
BPJS — lalu menandai domain yang meniru mereka (**+25 poin**):

- **Typo-squat**: domain hanya beda 1–2 huruf dari domain resmi
  (mis. `bc4.co.id` meniru `bca.co.id`).
- **Nama brand di label lain**: brand muncul sebagai bagian domain
  (mis. `bca-login.xyz`, `dana-promo.com`).
- **TLD berbeda**: nama brand dipakai dengan TLD yang bukan TLD resmi
  (mis. `bca.com` padahal resminya `bca.co.id`).

Domain resmi brand itu sendiri (termasuk subdomainnya, mis.
`login.bca.co.id`) tidak ditandai.

## Skor reputasi domain

Selain skor risiko tautan, CekURL menghitung **skor reputasi domain**
(0–100, makin tinggi makin tepercaya) dari nama domainnya saja.
Perintah `cekurl reputasi URL` menampilkannya beserta faktor-faktornya,
dan perintah `cek` juga menampilkan satu baris `Reputasi: X/100 — TIER`.

Cara hitungnya — berangkat dari 50 (netral):

| Faktor | Poin |
| --- | --- |
| Domain resmi terverifikasi (daftar putih) | 100 langsung |
| Host berupa alamat IP | 0 langsung |
| TLD resmi Indonesia (.go.id/.ac.id/.sch.id) | +30 |
| TLD Indonesia (.co.id/.or.id/.web.id/.id) | +15 |
| TLD umum (.com/.net/.org) | +5 |
| TLD yang sering dipakai penipu (.xyz, .top, .click, ...) | −20 |
| Punycode (xn--) | −15 |
| Subdomain berlapis (≥ 5 bagian) | −10 |
| Nama domain sangat panjang (> 30 karakter) | −5 |
| Banyak tanda hubung (≥ 4) | −5 |
| Meniru brand lokal | −25 |
| Pemendek URL (bit.ly, s.id, ...) | −15 |

Skor dijepit 0–100, lalu dipetakan ke tier:

- **≥ 70 — TERPERCAYA**: domain dikenal atau TLD-nya resmi.
- **40–69 — NETRAL**: tidak ada sinyal kuat ke arah mana pun.
- **< 40 — MERAGUKAN**: ada pola yang patut dicurigai.

Contoh angka:

```bash
$ python -m cekurl.cli reputasi https://www.bca.co.id
Domain   : www.bca.co.id
Reputasi : 100/100 — TERPERCAYA
Faktor:
  - Domain resmi terverifikasi (daftar putih bawaan: bca.co.id). (+50)

$ python -m cekurl.cli reputasi https://bit.ly/paket-tertunda
Domain   : bit.ly
Reputasi : 35/100 — MERAGUKAN
Faktor:
  - Pemendek URL (bit.ly) menyembunyikan tujuan asli tautan. (-15)

$ python -m cekurl.cli reputasi http://203.0.113.5/login-gratis
Domain   : 203.0.113.5
Reputasi : 0/100 — MERAGUKAN
Faktor:
  - Host berupa alamat IP — tidak ada reputasi domain. (-50)
```

## Cara kerja skor

Setiap sinyal menambah poin risiko. Total skor menentukan verdict:

- **0–29 — AMAN**: tidak ditemukan sinyal mencurigakan.
- **30–59 — WASPADA**: ada sinyal yang patut diperiksa sebelum diklik.
- **60–100 — BAHAYA**: banyak sinyal berbahaya — jangan dibuka.

> CekURL memeriksa **pola tautannya saja** dan bekerja sepenuhnya offline.
> CekURL tidak membuka tautan dan tidak menjamin sebuah situs aman —
> tautan yang lolos dari pola ini tetap bisa berbahaya. Bila ragu, jangan
> diklik dan konfirmasi lewat kanal resmi.

## Data contoh

Berkas `contoh/cekurl-contoh.txt` berisi 5 tautan contoh (2 aman, 2
waspada, 1 bahaya) beserta contoh pesan WhatsApp dan cara mencobanya:

```bash
python -m cekurl.cli batch --berkas contoh/cekurl-contoh.txt
python -m cekurl.cli pesan "Halo! Paket kamu tertunda, klaim di https://bit.ly/paket-tertunda ya. Info resmi: https://www.bca.co.id"
```

Berkas `contoh/daftar.txt` berisi daftar tautan yang lebih singkat untuk
latihan mode batch.

## Menjalankan test

74 unit test (analisis skor/sinyal, deteksi brand, CLI end-to-end, daftar
putih, dan skor reputasi):

```bash
python3 -m unittest discover -s tests
```

```
Ran 74 tests in 2.1s

OK
```

## Rencana

- [x] Analisis URL dasar + skor risiko + CLI
- [x] Deteksi domain meniru brand lokal
- [x] Cek tautan dari teks pesan + mode batch
- [x] Unit test + data contoh
- [x] README lengkap + polish CLI
- [x] Skor reputasi domain / daftar putih domain resmi (Day-2)

## Lisensi

MIT — © 2026 Hafizd Ammar
