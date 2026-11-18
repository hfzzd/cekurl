"""Analisis keamanan tautan (URL) — pola statis, sepenuhnya offline.

Setiap sinyal mencurigakan menambah poin risiko (0-100):

-   0-29  AMAN
-  30-59  WASPADA
-  60-100 BAHAYA
"""

import ipaddress
import re
from urllib.parse import urlparse

# Pemendek URL populer — menyembunyikan tujuan asli tautan.
PEMENEK_URL = {
    "bit.ly", "tinyurl.com", "s.id", "gg.gg", "t.co", "goo.gl",
    "cutt.ly", "shorturl.at", "rb.gy", "is.gd", "buff.ly", "ow.ly",
    "rebrand.ly", "bl.ink", "tiny.cc", "shorte.st", "adf.ly",
    "bitly.is", "t.ly", "v.gd", "qr.ae", "clck.ru", "shorturl.com",
}

# TLD yang murah/gratis dan sering dipakai untuk tautan menipu.
TLD_MENCURIGAKAN = {
    "xyz", "top", "click", "link", "buzz", "online", "site", "fun",
    "icu", "monster", "work", "live", "cc", "tk", "ml", "ga", "cf",
    "gq", "zip", "mov", "quest", "lol", "sbs", "bond", "cfd",
}

# Kata kunci yang sering muncul di tautan phishing berbahasa Indonesia.
KATA_KUNCI_PHISHING = {
    "verifikasi", "verif", "login", "masuk", "aman", "hadiah",
    "gratis", "bonus", "menang", "klaim", "aktivasi", "blokir",
    "tertunda", "paket", "undangan", "pernikahan", "apk", "unduh",
    "download", "promo", "diskon", "giveaway", "pemenang", "bantuan",
    "subsidi", "bansos", "saldo", "transfer", "pin", "otp",
}

BATAS_AMAN = 29
BATAS_WASPADA = 59


def _verdict(skor):
    if skor <= BATAS_AMAN:
        return "AMAN"
    if skor <= BATAS_WASPADA:
        return "WASPADA"
    return "BAHAYA"


def normalisasi_url(url):
    """Lengkapi skema bila tidak ada, dan buang spasi di ujung."""
    url = url.strip()
    if not url:
        raise ValueError("URL kosong.")
    if "://" not in url:
        url = "https://" + url
    return url


def analisis_url(url):
    """Analisis satu URL, kembalikan dict skor + verdict + sinyal.

    Melempar ValueError bila URL tidak bisa dipahami.
    """
    url = normalisasi_url(url)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Skema '{parsed.scheme}' tidak dikenal — pakai tautan http atau https."
        )
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL tidak punya nama host.")

    sinyal = []

    def tambah(alasan, poin):
        sinyal.append({"alasan": alasan, "poin": poin})

    # 1. Skema tidak terenkripsi.
    if parsed.scheme == "http":
        tambah("Tautan tidak terenkripsi (http, bukan https).", 10)

    # 2. Host berupa alamat IP, bukan nama domain.
    try:
        ipaddress.ip_address(host)
        tambah("Host memakai alamat IP langsung, bukan nama domain.", 30)
        is_ip = True
    except ValueError:
        is_ip = False

    if not is_ip:
        # 3. Pemendek URL.
        if host in PEMENEK_URL or host.endswith(
            tuple("." + p for p in PEMENEK_URL)
        ):
            tambah(
                f"Pemendek URL ({host}) menyembunyikan tujuan asli tautan.", 15
            )

        # 4. TLD yang sering disalahgunakan.
        tld = host.rsplit(".", 1)[-1] if "." in host else ""
        if tld in TLD_MENCURIGAKAN:
            tambah(f"Domain memakai TLD .{tld} yang sering dipakai penipu.", 10)

        # 5. Punycode (karakter non-ASCII yang disamarkan).
        if "xn--" in host:
            tambah(
                "Domain memakai punycode (xn--) — bisa menyamar sebagai domain lain.",
                15,
            )

        # 6. Subdomain berlapis-lapis.
        label = host.split(".")
        if len(label) >= 5:
            tambah(
                f"Domain punya {len(label)} bagian (subdomain berlapis) — "
                "sering dipakai untuk menyamar.",
                10,
            )

        # 7. Nama domain sangat panjang.
        if len(host) > 30:
            tambah("Nama domain sangat panjang — sering dipakai untuk menyamar.", 5)

        # 8. Terlalu banyak tanda hubung.
        if host.count("-") >= 4:
            tambah("Nama domain memakai banyak tanda hubung — pola tautan menipu.", 5)

    # 9. Trik '@' — bagian sebelum @ diabaikan browser.
    if "@" in (parsed.netloc or ""):
        tambah(
            "Tautan memakai '@' — bagian sebelum @ diabaikan, tujuan aslinya "
            "bisa berbeda.",
            25,
        )

    # 10. Port tidak standar.
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port and port not in (80, 443):
        tambah(f"Tautan memakai port tidak standar ({port}).", 5)

    # 11. Kata kunci phishing di seluruh URL.
    url_rendah = url.lower()
    ketemu = sorted(k for k in KATA_KUNCI_PHISHING if k in url_rendah)
    # Buang kata yang merupakan bagian dari kata lain yang juga ketemu
    # (mis. "verif" di dalam "verifikasi") supaya tidak dihitung ganda.
    ketemu = [
        k
        for k in ketemu
        if not any(k != lain and k in lain for lain in ketemu)
    ]
    if ketemu:
        tambah(
            "Kata mencurigakan di tautan: " + ", ".join(ketemu) + ".",
            min(10 * len(ketemu), 20),
        )

    skor = min(sum(s["poin"] for s in sinyal), 100)
    return {
        "url": url,
        "host": host,
        "skor": skor,
        "verdict": _verdict(skor),
        "sinyal": sinyal,
    }


def format_hasil(hasil):
    """Format hasil analisis untuk layar (Bahasa Indonesia)."""
    baris = [
        f"Tautan : {hasil['url']}",
        f"Skor   : {hasil['skor']}/100 — {hasil['verdict']}",
    ]
    if not hasil["sinyal"]:
        baris.append("Tidak ditemukan sinyal mencurigakan.")
    else:
        baris.append("Sinyal:")
        for s in hasil["sinyal"]:
            baris.append(f"  - {s['alasan']} (+{s['poin']})")
    return "\n".join(baris)
