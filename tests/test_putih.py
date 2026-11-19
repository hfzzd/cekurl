"""Unit test daftar putih (cekurl.putih).

Daftar kustom diuji dengan env CEKURL_PUTIH yang mengarah ke berkas
di /tmp, supaya tidak menyentuh ~/.config/cekurl/putih.json asli.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from cekurl.putih import (
    cek_daftar_putih,
    daftar_putih_bawaan,
    hapus_putih_kustom,
    muat_putih_kustom,
    tambah_putih_kustom,
)


class TestDaftarPutihBawaan(unittest.TestCase):
    def test_bca_co_id_terdaftar(self):
        hasil = cek_daftar_putih("bca.co.id")
        self.assertIsNotNone(hasil)
        self.assertEqual(hasil["domain"], "bca.co.id")
        self.assertEqual(hasil["sumber"], "daftar putih bawaan")

    def test_subdomain_www_bca_terdaftar(self):
        hasil = cek_daftar_putih("www.bca.co.id")
        self.assertIsNotNone(hasil)
        self.assertEqual(hasil["domain"], "bca.co.id")

    def test_google_com_terdaftar(self):
        self.assertIsNotNone(cek_daftar_putih("google.com"))

    def test_akhiran_go_id_terdaftar(self):
        hasil = cek_daftar_putih("kemenkeu.go.id")
        self.assertIsNotNone(hasil)
        self.assertIn("go.id", hasil["sumber"])

    def test_akhiran_ac_id_terdaftar(self):
        hasil = cek_daftar_putih("ui.ac.id")
        self.assertIsNotNone(hasil)
        self.assertIn("ac.id", hasil["sumber"])

    def test_bca_co_id_tiruan_bukan_putih(self):
        # bca-co.id: beda domain, bukan subdomain bca.co.id.
        self.assertIsNone(cek_daftar_putih("bca-co.id"))

    def test_danau_com_bukan_putih(self):
        self.assertIsNone(cek_daftar_putih("danau.com"))

    def test_daftar_bawaan_berisi_39_domain(self):
        self.assertEqual(len(daftar_putih_bawaan()), 39)


class TestDaftarPutihKustom(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.jalur = Path(self.tmp.name) / "putih.json"
        self._env_asli = os.environ.get("CEKURL_PUTIH")
        os.environ["CEKURL_PUTIH"] = str(self.jalur)
        self.addCleanup(self._pulihkan_env)

    def _pulihkan_env(self):
        if self._env_asli is None:
            os.environ.pop("CEKURL_PUTIH", None)
        else:
            os.environ["CEKURL_PUTIH"] = self._env_asli

    def test_awal_kosong(self):
        self.assertEqual(muat_putih_kustom(), [])

    def test_tambah_lalu_cek_terdaftar(self):
        tambah_putih_kustom("contohku.com")
        hasil = cek_daftar_putih("contohku.com")
        self.assertIsNotNone(hasil)
        self.assertEqual(hasil["sumber"], "daftar putih kustom")

    def test_subdomain_kustom_terdaftar(self):
        tambah_putih_kustom("contohku.com")
        self.assertIsNotNone(cek_daftar_putih("www.contohku.com"))

    def test_tambah_duplikat_ditolak(self):
        tambah_putih_kustom("contohku.com")
        with self.assertRaises(ValueError):
            tambah_putih_kustom("contohku.com")

    def test_tambah_domain_bawaan_ditolak(self):
        with self.assertRaises(ValueError):
            tambah_putih_kustom("google.com")

    def test_tambah_bentuk_tak_sah_ditolak(self):
        with self.assertRaises(ValueError):
            tambah_putih_kustom("bukan domain!!")
        with self.assertRaises(ValueError):
            tambah_putih_kustom("")

    def test_hapus_domain(self):
        tambah_putih_kustom("contohku.com")
        hapus_putih_kustom("contohku.com")
        self.assertEqual(muat_putih_kustom(), [])
        self.assertIsNone(cek_daftar_putih("contohku.com"))

    def test_hapus_domain_tidak_ada_ditolak(self):
        with self.assertRaises(ValueError):
            hapus_putih_kustom("tidak-ada.com")

    def test_berkas_rusak_kembali_list_kosong(self):
        self.jalur.write_text("{bukan json", encoding="utf-8")
        self.assertEqual(muat_putih_kustom(), [])

    def test_berkas_bukan_list_kembali_list_kosong(self):
        self.jalur.write_text(json.dumps({"a": 1}), encoding="utf-8")
        self.assertEqual(muat_putih_kustom(), [])


if __name__ == "__main__":
    unittest.main()
