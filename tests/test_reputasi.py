"""Unit test skor reputasi domain (cekurl.reputasi)."""


import unittest

from cekurl.reputasi import reputasi_domain


def poin_faktor(hasil, kata):
    """Jumlah poin dari faktor yang alasannya mengandung `kata`."""
    return sum(f["poin"] for f in hasil["faktor"] if kata in f["alasan"])


class TestReputasiDasar(unittest.TestCase):
    def test_whitelisted_skor_100(self):
        for host in ("google.com", "www.bca.co.id", "kemenkeu.go.id"):
            hasil = reputasi_domain(host)
            self.assertEqual(hasil["skor"], 100)
            self.assertEqual(hasil["tier"], "TERPERCAYA")

    def test_host_ip_skor_nol(self):
        hasil = reputasi_domain("203.0.113.5")
        self.assertEqual(hasil["skor"], 0)
        self.assertEqual(hasil["tier"], "MERAGUKAN")
        self.assertEqual(
            poin_faktor(hasil, "alamat IP"), -50
        )

    def test_host_kosong_ditolak(self):
        with self.assertRaises(ValueError):
            reputasi_domain("")


class TestTier(unittest.TestCase):
    def test_tier_terpercaya_minimal_70(self):
        self.assertEqual(reputasi_domain("google.com")["tier"], "TERPERCAYA")

    def test_tier_netral_40_sampai_69(self):
        # example.com: 50 + 5 (.com) = 55.
        hasil = reputasi_domain("example.com")
        self.assertEqual(hasil["skor"], 55)
        self.assertEqual(hasil["tier"], "NETRAL")
        # tokoku.co.id: 50 + 15 (.co.id) = 65.
        hasil = reputasi_domain("tokoku.co.id")
        self.assertEqual(hasil["skor"], 65)
        self.assertEqual(hasil["tier"], "NETRAL")
        # Batas bawah NETRAL: 40 tepat masih NETRAL.
        hasil = reputasi_domain("xn--nxasmq6b.com")
        self.assertEqual(hasil["skor"], 40)
        self.assertEqual(hasil["tier"], "NETRAL")

    def test_tier_meragukan_di_bawah_40(self):
        # bit.ly: 50 - 15 (pemendek) = 35.
        hasil = reputasi_domain("bit.ly")
        self.assertEqual(hasil["skor"], 35)
        self.assertEqual(hasil["tier"], "MERAGUKAN")


class TestFaktor(unittest.TestCase):
    def test_tld_indonesia_dua_label_tampil_benar(self):
        # bca-co.id: 50 + 15 (.id) - 25 (meniru BCA) = 40; teks faktor
        # harus menyebut ".id", bukan ".bca-co.id".
        hasil = reputasi_domain("bca-co.id")
        self.assertEqual(hasil["skor"], 40)
        self.assertTrue(
            any(".id (terdaftar di Indonesia)" in f["alasan"]
                for f in hasil["faktor"])
        )
        self.assertFalse(
            any(".bca-co.id" in f["alasan"] for f in hasil["faktor"])
        )

    def test_tld_indonesia_plus_15(self):
        hasil = reputasi_domain("tokoku.co.id")
        self.assertEqual(poin_faktor(hasil, "co.id"), 15)

    def test_tld_umum_plus_5(self):
        hasil = reputasi_domain("example.com")
        self.assertEqual(poin_faktor(hasil, ".com"), 5)

    def test_tld_mencurigakan_minus_20(self):
        # example.xyz: 50 - 20 = 30.
        hasil = reputasi_domain("example.xyz")
        self.assertEqual(hasil["skor"], 30)
        self.assertEqual(poin_faktor(hasil, ".xyz"), -20)

    def test_punycode_minus_15(self):
        hasil = reputasi_domain("xn--nxasmq6b.com")
        self.assertEqual(poin_faktor(hasil, "punycode"), -15)

    def test_meniru_brand_minus_25(self):
        # bca.com: 50 + 5 (.com) - 25 (meniru BCA) = 30.
        hasil = reputasi_domain("bca.com")
        self.assertEqual(hasil["skor"], 30)
        self.assertEqual(poin_faktor(hasil, "meniru brand"), -25)

    def test_pemendek_url_minus_15(self):
        hasil = reputasi_domain("bit.ly")
        self.assertEqual(poin_faktor(hasil, "Pemendek URL"), -15)

    def test_subdomain_berlapis_minus_10(self):
        # a.b.c.d.example.com: 6 label, 50 + 5 (.com) - 10 = 45.
        hasil = reputasi_domain("a.b.c.d.example.com")
        self.assertEqual(hasil["skor"], 45)
        self.assertEqual(poin_faktor(hasil, "berlapis"), -10)

    def test_host_panjang_minus_5(self):
        # 34 karakter, 50 + 5 (.com) - 5 = 50.
        hasil = reputasi_domain("namadomainyangpanjangsekali123.com")
        self.assertEqual(hasil["skor"], 50)
        self.assertEqual(poin_faktor(hasil, "sangat panjang"), -5)

    def test_banyak_tanda_hubung_minus_5(self):
        # 4 tanda hubung, 50 + 5 (.com) - 5 = 50.
        hasil = reputasi_domain("a-b-c-d-e.com")
        self.assertEqual(hasil["skor"], 50)
        self.assertEqual(poin_faktor(hasil, "tanda hubung"), -5)

    def test_skor_sesuai_jumlah_faktor(self):
        # Konsistensi: skor = 50 + jumlah poin faktor (dijepit 0-100).
        for host in (
            "example.com",
            "tokoku.co.id",
            "example.xyz",
            "bca.com",
            "bit.ly",
            "a.b.c.d.example.com",
        ):
            hasil = reputasi_domain(host)
            jumlah = 50 + sum(f["poin"] for f in hasil["faktor"])
            self.assertEqual(hasil["skor"], max(0, min(100, jumlah)))


if __name__ == "__main__":
    unittest.main()
