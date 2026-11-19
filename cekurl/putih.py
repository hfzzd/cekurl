"""Daftar putih domain resmi — domain yang sudah dikenal aman.

Dua sumber:

-   Daftar bawaan: domain resmi brand lokal (dari cekurl.brand), layanan
    global yang sudah dikenal, dan akhiran resmi Indonesia (.go.id,
    .ac.id, .sch.id — hanya instansi pemerintah/pendidikan yang bisa
    mendaftarkannya).
-   Daftar kustom pengguna: domain yang ditambahkan sendiri, tersimpan di
    berkas JSON ``~/.config/cekurl/putih.json`` (lokasi bisa diganti lewat
    environment variable ``CEKURL_PUTIH``, dipakai untuk test).

Domain di daftar putih dinilai AMAN apa pun isi tautannya: penipu tidak
bisa memakai domain resmi itu — yang mereka pakai adalah domain mirip
(typo-squat, TLD berbeda), dan itu tetap tertangkap deteksi brand.

Sepenuhnya offline, stdlib-only.
"""

import json
import os
import re
from pathlib import Path

from cekurl.brand import BRAND_RESMI, registered_domain

# Layanan global yang domain resminya sudah dikenal luas.
DOMAIN_RESMI_GLOBAL = {
    "google.com",
    "google.co.id",
    "youtube.com",
    "gmail.com",
    "wikipedia.org",
    "github.com",
    "microsoft.com",
    "apple.com",
    "whatsapp.com",
    "instagram.com",
    "facebook.com",
    "linkedin.com",
    "x.com",
    "twitter.com",
    "telegram.org",
    "zoom.us",
    "dropbox.com",
    "amazon.com",
    "cloudflare.com",
    "stackoverflow.com",
}

# Akhiran domain yang hanya bisa didaftarkan instansi resmi Indonesia.
AKHIRAN_RESMI = {"go.id", "ac.id", "sch.id"}

# Pola nama domain yang sah: label huruf/angka/tanda hubung, dipisah
# titik, minimal satu titik, TLD minimal 2 huruf.
POLA_DOMAIN = re.compile(
    r"^(?!-)[a-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[a-z0-9-]{1,63}(?<!-))*\.[a-z]{2,63}$"
)


def _domain_bawaan():
    """Semua domain resmi bawaan: brand lokal + layanan global."""
    bawaan = set(DOMAIN_RESMI_GLOBAL)
    for resmi in BRAND_RESMI.values():
        bawaan.update(resmi)
    return bawaan


def daftar_putih_bawaan():
    """Daftar domain resmi bawaan, terurut (untuk perintah `putih daftar`)."""
    return sorted(_domain_bawaan())


def _jalur_putih_kustom():
    """Lokasi berkas daftar putih kustom."""
    dari_env = os.environ.get("CEKURL_PUTIH")
    if dari_env:
        return Path(dari_env)
    return Path.home() / ".config" / "cekurl" / "putih.json"


def _normalisasi_domain(domain):
    """Rapikan domain: huruf kecil, buang spasi dan titik di ujung."""
    return (domain or "").strip().lower().rstrip(".")


def validasi_domain(domain):
    """Periksa bentuk domain; kembalikan domain yang sudah dirapikan.

    Melempar ValueError dengan pesan ramah bila bentuknya tidak sah.
    """
    domain = _normalisasi_domain(domain)
    if not domain:
        raise ValueError("Nama domain kosong.")
    if len(domain) > 253:
        raise ValueError(
            f"Nama domain '{domain}' terlalu panjang (maksimal 253 karakter)."
        )
    if not POLA_DOMAIN.match(domain):
        raise ValueError(
            f"Nama domain '{domain}' tidak sah — tulis domain lengkap, "
            "misal: kampusku.ac.id."
        )
    return domain


def muat_putih_kustom():
    """Muat daftar putih kustom dari berkas (list kosong bila belum ada)."""
    jalur = _jalur_putih_kustom()
    try:
        data = json.loads(jalur.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    bersih = []
    for domain in data:
        try:
            domain = validasi_domain(domain)
        except ValueError:
            continue
        if domain not in bersih:
            bersih.append(domain)
    return sorted(bersih)


def simpan_putih_kustom(daftar):
    """Simpan daftar putih kustom ke berkas."""
    jalur = _jalur_putih_kustom()
    jalur.parent.mkdir(parents=True, exist_ok=True)
    jalur.write_text(
        json.dumps(sorted(daftar), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def tambah_putih_kustom(domain):
    """Tambahkan domain ke daftar putih kustom.

    Melempar ValueError bila domain tidak sah, sudah ada di daftar
    kustom, atau sudah ada di daftar bawaan.
    """
    domain = validasi_domain(domain)
    if domain in _domain_bawaan():
        raise ValueError(
            f"Domain '{domain}' sudah ada di daftar putih bawaan."
        )
    daftar = muat_putih_kustom()
    if domain in daftar:
        raise ValueError(
            f"Domain '{domain}' sudah ada di daftar putih kustom."
        )
    daftar.append(domain)
    simpan_putih_kustom(daftar)
    return domain


def hapus_putih_kustom(domain):
    """Hapus domain dari daftar putih kustom.

    Melempar ValueError bila domain tidak ada di daftar kustom.
    """
    domain = validasi_domain(domain)
    daftar = muat_putih_kustom()
    if domain not in daftar:
        raise ValueError(
            f"Domain '{domain}' tidak ada di daftar putih kustom."
        )
    daftar.remove(domain)
    simpan_putih_kustom(daftar)
    return domain


def cek_daftar_putih(host):
    """Periksa apakah host ada di daftar putih.

    Kembalikan dict {"domain", "sumber"} bila cocok, atau None.
    Subdomain dari domain yang terdaftar ikut dihitung (mis.
    www.bca.co.id cocok dengan bca.co.id). Akhiran resmi (.go.id,
    .ac.id, .sch.id) dipercaya apa pun nama depannya.
    """
    host = _normalisasi_domain(host)
    if not host:
        return None

    # 1. Daftar kustom pengguna.
    for domain in muat_putih_kustom():
        if host == domain or host.endswith("." + domain):
            return {"domain": domain, "sumber": "daftar putih kustom"}

    # 2. Daftar bawaan (brand lokal + layanan global).
    reg = registered_domain(host)
    for domain in _domain_bawaan():
        if host == domain or host.endswith("." + domain):
            return {"domain": domain, "sumber": "daftar putih bawaan"}
    # Registered domain juga dicocokkan, supaya subdomain berlapis
    # dari domain resmi tetap dikenali walau host-nya panjang.
    if reg in _domain_bawaan():
        return {"domain": reg, "sumber": "daftar putih bawaan"}

    # 3. Akhiran resmi Indonesia.
    for akhiran in AKHIRAN_RESMI:
        if host == akhiran or host.endswith("." + akhiran):
            return {
                "domain": host,
                "sumber": f"akhiran resmi .{akhiran}",
            }

    return None
