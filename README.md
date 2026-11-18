# CekURL — Pemeriksa Keamanan Tautan

CekURL membantu masyarakat Indonesia memeriksa apakah sebuah tautan (URL)
aman diklik atau patut dicurigai — sebelum membuka tautan dari pesan
WhatsApp, SMS, atau email yang mencurigakan.

Tempel tautannya, CekURL memberi **skor risiko 0–100** beserta alasannya
dalam Bahasa Indonesia: `AMAN`, `WASPADA`, atau `BAHAYA`.

## Cara memakai

Tidak perlu instalasi apa pun selain Python 3.10+ (tanpa dependensi tambahan).

```bash
# Cek satu tautan
python -m cekurl.cli cek https://www.google.com

# Keluaran ringkas untuk mesin (JSON)
python -m cekurl.cli cek https://bit.ly/contoh --json

# Lihat versi
python -m cekurl.cli --version

# Cek semua tautan di dalam sebuah pesan (argumen atau stdin)
python -m cekurl.cli pesan "Halo! Klaim hadiahmu di https://bca-login.xyz/hadiah, info resmi di https://www.bca.co.id"
echo "Cek https://dana-promo.com/klaim-bonus ya" | python -m cekurl.cli pesan

# Cek banyak tautan dari berkas (satu URL per baris, # untuk komentar)
python -m cekurl.cli batch --berkas contoh/daftar.txt
```

Atau instal sekali lalu pakai perintah `cekurl`:

```bash
pip install .
cekurl cek https://www.google.com
```

## Yang diperiksa

| Sinyal | Keterangan |
| --- | --- |
| Skema `http` | Tautan tidak terenkripsi |
| Host berupa alamat IP | Tautan memakai angka IP, bukan nama domain |
| Pemendek URL | bit.ly, s.id, tinyurl, dan sejenisnya menyembunyikan tujuan asli |
| TLD rawan disalahgunakan | `.xyz`, `.top`, `.click`, dan sejenisnya |
| Karakter menipu | `@` di tengah URL, `xn--` (punycode), subdomain berlapis |
| Kata kunci phishing | `verifikasi`, `hadiah`, `gratis`, `klaim`, `blokir`, dan sejenisnya |
| Domain meniru brand lokal | BCA, BRI, GoPay, DANA, Shopee, Tokopedia, PLN, dan lainnya |
| Tautan dari teks pesan | Tempel pesan WhatsApp/SMS, semua tautan di dalamnya diperiksa |
| Mode batch | Satu URL per baris dari berkas, lengkap dengan rekap akhir |

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

## Cara kerja skor

Setiap sinyal menambah poin risiko. Total skor menentukan verdict:

- **0–29 — AMAN**: tidak ditemukan sinyal mencurigakan.
- **30–59 — WASPADA**: ada sinyal yang patut diperiksa sebelum diklik.
- **60–100 — BAHAYA**: banyak sinyal berbahaya — jangan dibuka.

> CekURL memeriksa **pola tautannya saja** dan bekerja sepenuhnya offline.
> CekURL tidak membuka tautan dan tidak menjamin sebuah situs aman —
> tautan yang lolos dari pola ini tetap bisa berbahaya. Bila ragu, jangan
> diklik dan konfirmasi lewat kanal resmi.

## Rencana

- [x] Analisis URL dasar + skor risiko + CLI
- [x] Deteksi domain meniru brand lokal (Day-2)
- [x] Cek tautan dari teks pesan + mode batch (Day-2)
- [ ] Unit test + data contoh (Day-2)

## Lisensi

MIT — © 2026 Hafizd Ammar
