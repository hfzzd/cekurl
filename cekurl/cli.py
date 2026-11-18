"""CLI CekURL — pemeriksa keamanan tautan berbahasa Indonesia."""

import argparse
import json
import re
import sys

from cekurl import __version__
from cekurl.analisis import analisis_url, format_hasil

# URL di dalam teks: http(s):// lalu karakter apa pun kecuali spasi dan
# tanda yang jelas bukan bagian URL (kurung sudut, tanda kutip).
POLA_URL = re.compile(r"https?://[^\s<>\"']+")


def ekstrak_url(teks):
    """Ambil semua URL dari sebuah teks (mis. pesan WhatsApp/SMS).

    Tanda baca di ujung URL (titik, koma, tanda seru, kurung tutup)
    dibuang karena biasanya itu pemisah kalimat, bukan bagian URL.
    """
    return [cocok.rstrip(".,;:!?)}]'\"") for cocok in POLA_URL.findall(teks)]


def baca_daftar_berkas(nama_berkas):
    """Baca daftar URL dari berkas: satu URL per baris.

    Baris kosong dan baris komentar (diawali #) dilewati.
    """
    with open(nama_berkas, encoding="utf-8") as f:
        return [
            baris.strip()
            for baris in f
            if baris.strip() and not baris.strip().startswith("#")
        ]


def _parser():
    parser = argparse.ArgumentParser(
        prog="cekurl",
        description="Periksa apakah sebuah tautan aman diklik atau patut dicurigai.",
    )
    parser.add_argument(
        "--version", action="version", version=f"cekurl {__version__}"
    )
    sub = parser.add_subparsers(dest="perintah", required=True)

    cek = sub.add_parser(
        "cek", help="Cek satu tautan dan tampilkan skor risikonya."
    )
    cek.add_argument("url", help="Tautan yang mau diperiksa")
    cek.add_argument(
        "--json", action="store_true", help="Tampilkan hasil sebagai JSON"
    )

    pesan = sub.add_parser(
        "pesan",
        help="Cek semua tautan di dalam sebuah teks pesan (argumen atau stdin).",
    )
    pesan.add_argument(
        "teks",
        nargs="?",
        default=None,
        help="Isi pesan (bila kosong, dibaca dari stdin)",
    )

    batch = sub.add_parser(
        "batch", help="Cek banyak tautan sekaligus dari sebuah berkas."
    )
    batch.add_argument(
        "--berkas",
        required=True,
        help="Berkas daftar tautan (satu URL per baris, # untuk komentar)",
    )
    return parser


def _tampilkan_banyak(daftar_url):
    """Analisis tiap URL, tampilkan ringkasan per tautan + rekap akhir."""
    hitung = {"AMAN": 0, "WASPADA": 0, "BAHAYA": 0}
    gagal = 0
    for i, url in enumerate(daftar_url, start=1):
        try:
            hasil = analisis_url(url)
        except ValueError as e:
            print(f"{i}. {url}")
            print(f"   Error: {e}")
            gagal += 1
            continue
        hitung[hasil["verdict"]] += 1
        print(f"{i}. {hasil['url']}")
        print(f"   Skor: {hasil['skor']}/100 — {hasil['verdict']}")
        if hasil["sinyal"]:
            print(
                "   Sinyal: "
                + "; ".join(s["alasan"] for s in hasil["sinyal"])
            )
    total = len(daftar_url)
    rekap = (
        f"Ringkasan: {total} tautan — "
        f"AMAN {hitung['AMAN']}, WASPADA {hitung['WASPADA']}, "
        f"BAHAYA {hitung['BAHAYA']}"
    )
    if gagal:
        rekap += f", gagal dibaca {gagal}"
    print(rekap)
    return 0


def _perintah_pesan(args):
    teks = args.teks
    if teks is None:
        teks = sys.stdin.read()
    if not teks.strip():
        print(
            "Error: tidak ada teks pesan. Tempel teks sebagai argumen "
            "atau lewat stdin.",
            file=sys.stderr,
        )
        return 1
    daftar_url = ekstrak_url(teks)
    if not daftar_url:
        print("Tidak ditemukan tautan di dalam teks.", file=sys.stderr)
        return 1
    return _tampilkan_banyak(daftar_url)


def _perintah_batch(args):
    try:
        daftar_url = baca_daftar_berkas(args.berkas)
    except OSError as e:
        print(f"Error: tidak bisa membaca berkas '{args.berkas}': {e}.",
              file=sys.stderr)
        return 1
    if not daftar_url:
        print(
            f"Error: berkas '{args.berkas}' tidak berisi tautan "
            "(baris kosong dan komentar # dilewati).",
            file=sys.stderr,
        )
        return 1
    return _tampilkan_banyak(daftar_url)


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    if args.perintah == "cek":
        try:
            hasil = analisis_url(args.url)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(hasil, indent=2, ensure_ascii=False))
        else:
            print(format_hasil(hasil))
        return 0
    if args.perintah == "pesan":
        return _perintah_pesan(args)
    if args.perintah == "batch":
        return _perintah_batch(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
