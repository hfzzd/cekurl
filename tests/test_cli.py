"""Unit test CLI CekURL (end-to-end lewat subprocess di /tmp)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERINTAH = [sys.executable, "-m", "cekurl.cli"]


def jalankan(*args, input_teks=None):
    return subprocess.run(
        PERINTAH + list(args),
        input=input_teks,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestPerintahCek(unittest.TestCase):
    def test_cek_domain_bersih(self):
        hasil = jalankan("cek", "https://www.google.com")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Skor   : 0/100 — AMAN", hasil.stdout)

    def test_cek_tautan_waspada(self):
        hasil = jalankan("cek", "https://bit.ly/paket-tertunda")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Skor   : 35/100 — WASPADA", hasil.stdout)

    def test_cek_format_json(self):
        hasil = jalankan("cek", "https://www.google.com", "--json")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn('"skor": 0', hasil.stdout)
        self.assertIn('"verdict": "AMAN"', hasil.stdout)

    def test_cek_input_salah_exit_bukan_nol(self):
        hasil = jalankan("cek", "ftp://contoh.com/berkas")
        self.assertNotEqual(hasil.returncode, 0)
        self.assertIn("Error", hasil.stderr)

    def test_version_tampil_0_1_0(self):
        hasil = jalankan("--version")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("cekurl 0.1.0", hasil.stdout)


class TestPerintahPesan(unittest.TestCase):
    PESAN = (
        "Halo! Paket kamu tertunda, klaim di https://bit.ly/paket-tertunda "
        "ya. Info resmi: https://www.bca.co.id"
    )

    def test_pesan_dari_argumen(self):
        hasil = jalankan("pesan", self.PESAN)
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("WASPADA", hasil.stdout)
        self.assertIn("AMAN", hasil.stdout)
        self.assertIn("Ringkasan: 2 tautan", hasil.stdout)

    def test_pesan_dari_stdin(self):
        hasil = jalankan("pesan", input_teks=self.PESAN)
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Ringkasan: 2 tautan", hasil.stdout)

    def test_pesan_tanpa_tautan_exit_bukan_nol(self):
        hasil = jalankan("pesan", "Halo, apa kabar?")
        self.assertNotEqual(hasil.returncode, 0)


class TestPerintahBatch(unittest.TestCase):
    def test_batch_dari_berkas_di_tmp(self):
        with tempfile.TemporaryDirectory() as tmp:
            berkas = Path(tmp) / "daftar.txt"
            berkas.write_text(
                "# komentar dilewati\n"
                "https://www.google.com\n"
                "https://bit.ly/paket-tertunda\n"
                "http://203.0.113.5/login-gratis\n",
                encoding="utf-8",
            )
            hasil = jalankan("batch", "--berkas", str(berkas))
        self.assertEqual(hasil.returncode, 0)
        self.assertIn(
            "Ringkasan: 3 tautan — AMAN 1, WASPADA 1, BAHAYA 1",
            hasil.stdout,
        )

    def test_batch_berkas_tidak_ada_exit_bukan_nol(self):
        hasil = jalankan("batch", "--berkas", "/tmp/cekurl-tidak-ada.txt")
        self.assertNotEqual(hasil.returncode, 0)
        self.assertIn("tidak ditemukan", hasil.stderr)
        self.assertIn("Periksa lagi nama dan lokasi berkasnya", hasil.stderr)


if __name__ == "__main__":
    unittest.main()
