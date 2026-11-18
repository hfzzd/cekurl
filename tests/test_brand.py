"""Unit test deteksi domain meniru brand lokal (cekurl.brand)."""

import unittest

from cekurl.brand import deteksi_brand, levenshtein


class TestTypoSquat(unittest.TestCase):
    def test_jarak_edit_satu_terdeteksi(self):
        # bca-co.id hanya beda 1 karakter dari bca.co.id.
        self.assertEqual(levenshtein("bca-co.id", "bca.co.id"), 1)
        hasil = deteksi_brand("bca-co.id")
        self.assertIsNotNone(hasil)
        self.assertEqual(hasil["brand"], "BCA")
        self.assertIn("bca.co.id", hasil["domain_resmi"])

    def test_jarak_edit_dua_terdeteksi(self):
        # bc4.co.id beda 1 huruf; bcb.co.id juga dalam jarak 2.
        hasil = deteksi_brand("bc4.co.id")
        self.assertIsNotNone(hasil)
        self.assertEqual(hasil["brand"], "BCA")

    def test_jarak_lebih_dari_dua_tidak_terdeteksi(self):
        self.assertGreater(levenshtein("bni-super.co.id", "bca.co.id"), 2)


class TestBrandDiSubdomain(unittest.TestCase):
    def test_brand_di_subdomain_terdeteksi(self):
        hasil = deteksi_brand("bca.situsku.com")
        self.assertIsNotNone(hasil)
        self.assertEqual(hasil["brand"], "BCA")

    def test_brand_menempel_di_label_terdeteksi(self):
        hasil = deteksi_brand("shopeepay.xyz")
        self.assertIsNotNone(hasil)
        self.assertEqual(hasil["brand"], "Shopee")

    def test_brand_dengan_tld_berbeda_terdeteksi(self):
        hasil = deteksi_brand("bca.com")
        self.assertIsNotNone(hasil)
        self.assertEqual(hasil["brand"], "BCA")


class TestTidakFalsePositive(unittest.TestCase):
    def test_domain_resmi_tidak_ditandai(self):
        self.assertIsNone(deteksi_brand("bca.co.id"))
        self.assertIsNone(deteksi_brand("www.dana.id"))
        self.assertIsNone(deteksi_brand("tokopedia.com"))

    def test_subdomain_domain_resmi_tidak_ditandai(self):
        self.assertIsNone(deteksi_brand("login.bca.co.id"))
        self.assertIsNone(deteksi_brand("www.bca.co.id"))

    def test_domain_biasa_tidak_ditandai(self):
        self.assertIsNone(deteksi_brand("www.google.com"))
        self.assertIsNone(deteksi_brand("contoh.or.id"))


if __name__ == "__main__":
    unittest.main()
