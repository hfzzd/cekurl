"""Deteksi domain yang meniru brand lokal Indonesia.

Pola yang dikenali (host harus BUKAN domain resmi brand itu sendiri):

(a) Typo-squat — jarak edit (Levenshtein) <= 2 dari domain resmi pada
    registered domain (mis. bc4.co.id meniru bca.co.id).
(b) Brand sebagai substring — nama brand muncul sebagai token utuh di
    label lain (mis. bca-login.xyz, dana-promo.com).
(c) TLD berbeda — nama brand dipakai dengan TLD yang bukan TLD resmi
    (mis. bca.com padahal resminya bca.co.id).

Sepenuhnya offline, stdlib-only.
"""

import re

# Brand -> domain resmi. Kata kunci deteksi = nama brand huruf kecil,
# kecuali dicatat lain (Mandiri memakai "mandiri", CIMB memakai "cimb",
# Permata memakai "permata", BPJS memakai "bpjs").
BRAND_RESMI = {
    # Bank
    "BCA": {"bca.co.id"},
    "BRI": {"bri.co.id"},
    "Mandiri": {"bankmandiri.co.id"},
    "BNI": {"bni.co.id"},
    "CIMB": {"cimbniaga.co.id"},
    "Danamon": {"danamon.co.id"},
    "Permata": {"permatabank.com"},
    # E-wallet
    "GoPay": {"gopay.co.id"},
    "DANA": {"dana.id"},
    "OVO": {"ovo.id"},
    # E-commerce
    "Shopee": {"shopee.co.id"},
    "Tokopedia": {"tokopedia.com"},
    "Lazada": {"lazada.co.id"},
    "Bukalapak": {"bukalapak.com"},
    "Blibli": {"blibli.com"},
    # Lainnya
    "PLN": {"pln.co.id"},
    "Telkomsel": {"telkomsel.com"},
    "Kominfo": {"kominfo.go.id"},
    "BPJS": {"bpjs-kesehatan.go.id"},
}

# Kata kunci -> brand. Dipakai untuk pola (b) dan (c).
KATA_BRAND = {
    "bca": "BCA",
    "bri": "BRI",
    "mandiri": "Mandiri",
    "bni": "BNI",
    "cimb": "CIMB",
    "danamon": "Danamon",
    "permata": "Permata",
    "gopay": "GoPay",
    "dana": "DANA",
    "ovo": "OVO",
    "shopee": "Shopee",
    "tokopedia": "Tokopedia",
    "lazada": "Lazada",
    "bukalapak": "Bukalapak",
    "blibli": "Blibli",
    "pln": "PLN",
    "telkomsel": "Telkomsel",
    "kominfo": "Kominfo",
    "bpjs": "BPJS",
}

# Second-level domain Indonesia — registered domain memakai 3 label
# untuk akhiran ini (mis. bca.co.id, kominfo.go.id).
SLD_INDONESIA = {
    "co.id", "go.id", "ac.id", "or.id", "sch.id", "web.id",
    "my.id", "net.id", "biz.id", "desa.id",
}

JARAK_MAKS_TYPO = 2


def levenshtein(a, b):
    """Jarak edit minimum antara dua string (algoritma klasik)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    baris = list(range(len(b) + 1))
    for i, ka in enumerate(a, start=1):
        baru = [i]
        for j, kb in enumerate(b, start=1):
            baru.append(
                min(
                    baris[j] + 1,          # hapus
                    baru[j - 1] + 1,       # sisip
                    baris[j - 1] + (ka != kb),  # ganti
                )
            )
        baris = baru
    return baris[-1]


def registered_domain(host):
    """Perkiraan registered domain dari sebuah host.

    Ambil 2 label terakhir, atau 3 bila memakai second-level domain
    Indonesia (mis. kominfo.go.id -> kominfo.go.id, bukan go.id).
    """
    host = host.lower().strip(".")
    label = host.split(".")
    if len(label) <= 2:
        return host
    if ".".join(label[-2:]) in SLD_INDONESIA:
        return ".".join(label[-3:])
    return ".".join(label[-2:])


def _domain_resmi(host):
    """Kembalikan brand bila host adalah domain resmi (atau subdomainnya)."""
    for brand, resmi in BRAND_RESMI.items():
        for domain in resmi:
            if host == domain or host.endswith("." + domain):
                return brand
    return None


def _cek_typo(reg):
    """Pola (a): registered domain mirip domain resmi (jarak <= 2)."""
    for brand, resmi in BRAND_RESMI.items():
        for domain in resmi:
            jarak = levenshtein(reg, domain)
            if 0 < jarak <= JARAK_MAKS_TYPO:
                return brand, (
                    f"domainnya mirip domain resmi {brand} ({domain}) — "
                    f"kemungkinan salah ketik yang disengaja"
                )
    return None


def _cek_tld_berbeda(reg):
    """Pola (c): nama brand dipakai dengan TLD yang bukan TLD resmi."""
    label_pertama = reg.split(".", 1)[0]
    for kata, brand in KATA_BRAND.items():
        if label_pertama == kata:
            resmi = sorted(BRAND_RESMI[brand])
            return brand, (
                f"memakai nama {brand} dengan TLD berbeda dari domain resmi "
                f"({', '.join(resmi)})"
            )
    return None


def _cek_substring(host):
    """Pola (b): nama brand muncul sebagai token di label lain."""
    for label in host.split("."):
        for token in re.split(r"[^a-z0-9]+", label):
            if not token:
                continue
            for kata, brand in KATA_BRAND.items():
                if token == kata:
                    return brand, (
                        f"nama {brand} muncul di bagian domain ({label}) "
                        "padahal bukan domain resmi"
                    )
                # Kata kunci panjang (>= 5 huruf) boleh menempel di awal
                # token (mis. shopeepay) — kata pendek seperti "dana"
                # tidak, supaya "danau.com" tidak ikut tertuduh.
                if len(kata) >= 5 and token.startswith(kata):
                    return brand, (
                        f"nama {brand} menempel di bagian domain ({label}) "
                        "padahal bukan domain resmi"
                    )
    return None


def deteksi_brand(host):
    """Periksa apakah host meniru salah satu brand lokal.

    Kembalikan dict {"brand", "domain_resmi", "alasan"} bila terdeteksi,
    atau None bila host resmi / tidak meniru brand mana pun.
    """
    host = (host or "").lower().strip(".")
    if not host:
        return None
    if _domain_resmi(host):
        return None

    reg = registered_domain(host)
    hasil = _cek_typo(reg) or _cek_tld_berbeda(reg) or _cek_substring(host)
    if not hasil:
        return None
    brand, alasan = hasil
    return {
        "brand": brand,
        "domain_resmi": sorted(BRAND_RESMI[brand]),
        "alasan": alasan,
    }
