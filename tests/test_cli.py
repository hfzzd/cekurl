"""Unit test CLI CekURL (end-to-end lewat subprocess di /tmp)."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERINTAH = [sys.executable, "-m", "cekurl.cli"]


def jalankan(*args, input_teks=None, env=None):
    lingkungan = dict(os.environ)
    if env:
        lingkungan.update(env)
    return subprocess.run(
        PERINTAH + list(args),
        input=input_teks,
        capture_output=True,
        text=True,
        timeout=30,
        env=lingkungan,
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

    def test_cek_json_memuat_reputasi(self):
        hasil = jalankan("cek", "https://www.google.com", "--json")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn('"reputasi"', hasil.stdout)
        self.assertIn('"skor": 100', hasil.stdout)
        self.assertIn('"tier": "TERPERCAYA"', hasil.stdout)

    def test_cek_menampilkan_baris_reputasi(self):
        hasil = jalankan("cek", "https://www.google.com")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Reputasi: 100/100 — TERPERCAYA", hasil.stdout)
        hasil = jalankan("cek", "https://bit.ly/paket-tertunda")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Reputasi: 35/100 — MERAGUKAN", hasil.stdout)

    def test_cek_input_salah_exit_bukan_nol(self):
        hasil = jalankan("cek", "ftp://contoh.com/berkas")
        self.assertNotEqual(hasil.returncode, 0)
        self.assertIn("Error", hasil.stderr)

    def test_version_tampil_0_1_0(self):
        hasil = jalankan("--version")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("cekurl 0.1.0", hasil.stdout)


class TestPerintahPutih(unittest.TestCase):
    def test_putih_cek_terdaftar_exit_0(self):
        hasil = jalankan("putih", "cek", "bca.co.id")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("ada di daftar putih", hasil.stdout)

    def test_putih_cek_tidak_terdaftar_exit_1(self):
        hasil = jalankan("putih", "cek", "danau.com")
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("tidak ada di daftar putih", hasil.stderr)

    def test_putih_tambah_hapus_daftar(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"CEKURL_PUTIH": str(Path(tmp) / "putih.json")}
            hasil = jalankan(
                "putih", "tambah", "contohku.com", env=env
            )
            self.assertEqual(hasil.returncode, 0)
            self.assertIn("ditambahkan", hasil.stdout)

            hasil = jalankan("putih", "cek", "www.contohku.com", env=env)
            self.assertEqual(hasil.returncode, 0)

            # Duplikat ditolak.
            hasil = jalankan(
                "putih", "tambah", "contohku.com", env=env
            )
            self.assertEqual(hasil.returncode, 1)
            self.assertIn("sudah ada", hasil.stderr)

            hasil = jalankan("putih", "daftar", env=env)
            self.assertEqual(hasil.returncode, 0)
            self.assertIn("contohku.com", hasil.stdout)

            hasil = jalankan("putih", "hapus", "contohku.com", env=env)
            self.assertEqual(hasil.returncode, 0)
            self.assertIn("dihapus", hasil.stdout)

            hasil = jalankan("putih", "cek", "contohku.com", env=env)
            self.assertEqual(hasil.returncode, 1)


class TestPerintahReputasi(unittest.TestCase):
    def test_reputasi_google_100_terpercaya(self):
        hasil = jalankan("reputasi", "https://www.google.com")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Reputasi : 100/100 — TERPERCAYA", hasil.stdout)
        self.assertIn("Domain resmi terverifikasi", hasil.stdout)
        self.assertIn("(+50)", hasil.stdout)

    def test_reputasi_bitly_meragukan(self):
        hasil = jalankan("reputasi", "https://bit.ly/paket-tertunda")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Reputasi : 35/100 — MERAGUKAN", hasil.stdout)
        self.assertIn("Pemendek URL", hasil.stdout)
        self.assertIn("(-15)", hasil.stdout)

    def test_reputasi_ip_nol(self):
        hasil = jalankan("reputasi", "http://203.0.113.5/login-gratis")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Reputasi : 0/100 — MERAGUKAN", hasil.stdout)
        self.assertIn("alamat IP", hasil.stdout)

    def test_reputasi_url_tak_valid_exit_1(self):
        hasil = jalankan("reputasi", "ftp://contoh.com/berkas")
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("Error", hasil.stderr)


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
