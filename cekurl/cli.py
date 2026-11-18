"""CLI CekURL — pemeriksa keamanan tautan berbahasa Indonesia."""

import argparse
import json
import sys

from cekurl import __version__
from cekurl.analisis import analisis_url, format_hasil


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
    return parser


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
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
