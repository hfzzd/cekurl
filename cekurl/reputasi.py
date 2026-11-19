"""Skor reputasi domain — seberapa tepercaya sebuah domain.

Skor 0-100 (makin tinggi makin tepercaya), berangkat dari 50 (netral):

-   Daftar putih (domain resmi terverifikasi) -> 100 langsung.
-   Host berupa alamat IP -> 0 (tidak ada reputasi domain).
-   TLD resmi Indonesia (.go.id/.ac.id/.sch.id) +30, .co.id/.or.id/
    .web.id/.id +15, .com/.net/.org +5; TLD yang sering disalahgunakan
    -20.
-   Punycode (xn--) -15; subdomain >= 5 label -10; host > 30 karakter
    -5; tanda hubung >= 4 -5; meniru brand lokal -25; pemendek URL -15.

Tier: >= 70 TERPERCAYA, 40-69 NETRAL, < 40 MERAGUKAN.

Sepenuhnya offline, stdlib-only.
"""

import ipaddress

from cekurl.analisis import PEMENEK_URL, TLD_MENCURIGAKAN
from cekurl.brand import deteksi_brand
from cekurl.putih import cek_daftar_putih

# TLD Indonesia yang menandakan domain terdaftar resmi di Indonesia.
TLD_RESMI_ID = {"go.id", "ac.id", "sch.id"}
TLD_ID_BIASA = {"co.id", "or.id", "web.id", "id"}
TLD_UMUM = {"com", "net", "org"}

BATAS_TERPERCAYA = 70
BATAS_NETRAL = 40


def _tier(skor):
    if skor >= BATAS_TERPERCAYA:
        return "TERPERCAYA"
    if skor >= BATAS_NETRAL:
        return "NETRAL"
    return "MERAGUKAN"


def reputasi_domain(host):
    """Hitung skor reputasi sebuah host/domain.

    Kembalikan dict {"skor" (0-100), "tier", "faktor": [{"alasan",
    "poin"}]}. Melempar ValueError bila host kosong.
    """
    host = (host or "").lower().strip(".")
    if not host:
        raise ValueError("Nama host kosong.")

    faktor = []

    def tambah(alasan, poin):
        faktor.append({"alasan": alasan, "poin": poin})

    # 0. Daftar putih — domain resmi langsung mendapat skor penuh.
    putih = cek_daftar_putih(host)
    if putih:
        return {
            "skor": 100,
            "tier": "TERPERCAYA",
            "faktor": [
                {
                    "alasan": (
                        f"Domain resmi terverifikasi ({putih['sumber']}: "
                        f"{putih['domain']})."
                    ),
                    "poin": 50,
                }
            ],
        }

    # 1. Host berupa alamat IP — tidak ada reputasi domain.
    try:
        ipaddress.ip_address(host)
        return {
            "skor": 0,
            "tier": "MERAGUKAN",
            "faktor": [
                {
                    "alasan": "Host berupa alamat IP — "
                    "tidak ada reputasi domain.",
                    "poin": -50,
                }
            ],
        }
    except ValueError:
        pass

    skor = 50

    # 2. TLD.
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    akhiran = ".".join(host.split(".")[-2:])
    if akhiran in TLD_RESMI_ID:
        tambah(
            f"Domain memakai TLD .{akhiran} (instansi resmi Indonesia).",
            30,
        )
    elif akhiran in TLD_ID_BIASA or tld == "id":
        tambah(f"Domain memakai TLD .{akhiran} (terdaftar di Indonesia).", 15)
    elif tld in TLD_UMUM:
        tambah(f"Domain memakai TLD .{tld} yang umum.", 5)
    if tld in TLD_MENCURIGAKAN:
        tambah(
            f"Domain memakai TLD .{tld} yang sering dipakai penipu.",
            -20,
        )

    # 3. Punycode (karakter non-ASCII yang disamarkan).
    if "xn--" in host:
        tambah(
            "Domain memakai punycode (xn--) — bisa menyamar sebagai "
            "domain lain.",
            -15,
        )

    # 4. Subdomain berlapis-lapis.
    label = host.split(".")
    if len(label) >= 5:
        tambah(
            f"Domain punya {len(label)} bagian (subdomain berlapis) — "
            "sering dipakai untuk menyamar.",
            -10,
        )

    # 5. Nama domain sangat panjang.
    if len(host) > 30:
        tambah(
            "Nama domain sangat panjang — sering dipakai untuk menyamar.",
            -5,
        )

    # 6. Terlalu banyak tanda hubung.
    if host.count("-") >= 4:
        tambah(
            "Nama domain memakai banyak tanda hubung — pola tautan menipu.",
            -5,
        )

    # 7. Domain meniru brand lokal.
    tiruan = deteksi_brand(host)
    if tiruan:
        tambah(
            f"Domain meniru brand {tiruan['brand']} — {tiruan['alasan']} "
            f"(resmi: {', '.join(tiruan['domain_resmi'])}).",
            -25,
        )

    # 8. Pemendek URL.
    if host in PEMENEK_URL or host.endswith(
        tuple("." + p for p in PEMENEK_URL)
    ):
        tambah(
            f"Pemendek URL ({host}) menyembunyikan tujuan asli tautan.",
            -15,
        )

    skor = max(0, min(100, skor + sum(f["poin"] for f in faktor)))
    return {"skor": skor, "tier": _tier(skor), "faktor": faktor}


def format_reputasi(reputasi, host=None):
    """Format skor reputasi untuk layar (Bahasa Indonesia)."""
    baris = []
    if host:
        baris.append(f"Domain   : {host}")
    baris.append(
        f"Reputasi : {reputasi['skor']}/100 — {reputasi['tier']}"
    )
    if reputasi["faktor"]:
        baris.append("Faktor:")
        for f in reputasi["faktor"]:
            poin = f"+{f['poin']}" if f["poin"] > 0 else str(f["poin"])
            baris.append(f"  - {f['alasan']} ({poin})")
    else:
        baris.append("Tidak ada faktor penambah atau pengurang.")
    return "\n".join(baris)
