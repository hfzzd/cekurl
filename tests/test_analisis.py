"""Unit test analisis URL (cekurl.analisis)."""

import unittest

from cekurl.analisis import analisis_url


def poin_sinyal(hasil, kata):
    """Jumlah poin dari sinyal yang alasannya mengandung `kata`."""
    return sum(s["poin"] for s in hasil["sinyal"] if kata in s["alasan"])


class TestSkorDasar(unittest.TestCase):
    def test_domain_bersih_skor_nol(self):
        hasil = analisis_url("https://www.google.com")
        self.assertEqual(hasil["skor"], 0)
        self.assertEqual(hasil["verdict"], "AMAN")
        self.assertEqual(hasil["sinyal"], [])

    def test_domain_resmi_bank_skor_nol(self):
        hasil = analisis_url("https://www.bca.co.id")
        self.assertEqual(hasil["skor"], 0)
        self.assertEqual(hasil["verdict"], "AMAN")


class TestSinyalBerbahaya(unittest.TestCase):
    def test_ip_http_kata_kunci_bahaya_minimal_60(self):
        # http (+10) + IP (+30) + login & gratis (+20) = 60.
        hasil = analisis_url("http://203.0.113.5/login-gratis")
        self.assertEqual(hasil["skor"], 60)
        self.assertEqual(hasil["verdict"], "BAHAYA")

    def test_pemendek_url_waspada(self):
        # bit.ly (+15) + paket & tertunda (+20) = 35.
        hasil = analisis_url("https://bit.ly/paket-tertunda")
        self.assertEqual(hasil["skor"], 35)
        self.assertEqual(hasil["verdict"], "WASPADA")
        self.assertEqual(poin_sinyal(hasil, "Pemendek URL"), 15)

    def test_trik_at_tambah_25(self):
        hasil = analisis_url("https://www.google.com@evil.com")
        self.assertEqual(poin_sinyal(hasil, "'@'"), 25)

    def test_punycode_tambah_15(self):
        hasil = analisis_url("https://xn--contoh-abc.com")
        self.assertEqual(poin_sinyal(hasil, "punycode"), 15)

    def test_tld_mencurigakan_tambah_10(self):
        hasil = analisis_url("https://situsku.xyz")
        self.assertEqual(poin_sinyal(hasil, "TLD .xyz"), 10)


class TestKataKunci(unittest.TestCase):
    def test_kata_kunci_substring_tidak_dihitung_ganda(self):
        # "verifikasi" mengandung "verif" — tetap dihitung satu kata (+10).
        hasil = analisis_url("https://contoh.com/verifikasi")
        self.assertEqual(poin_sinyal(hasil, "Kata mencurigakan"), 10)
        self.assertEqual(hasil["skor"], 10)

    def test_dua_kata_kunci_dihitung_masing_masing(self):
        hasil = analisis_url("https://contoh.com/klaim-hadiah")
        self.assertEqual(poin_sinyal(hasil, "Kata mencurigakan"), 20)


class TestValidasi(unittest.TestCase):
    def test_skema_ftp_ditolak(self):
        with self.assertRaises(ValueError):
            analisis_url("ftp://contoh.com/berkas")

    def test_url_tanpa_skema_dilengkapi_https(self):
        hasil = analisis_url("www.google.com")
        self.assertTrue(hasil["url"].startswith("https://"))
        self.assertEqual(hasil["skor"], 0)

    def test_url_kosong_ditolak(self):
        with self.assertRaises(ValueError):
            analisis_url("   ")


if __name__ == "__main__":
    unittest.main()
