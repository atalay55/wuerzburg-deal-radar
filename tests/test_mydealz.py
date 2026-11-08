import unittest
from src.parser_utils import parse_german_price, compute_discount_pct, classify_keyword
from src.mydealz import parse_mydealz_rss


class TestParserAndMyDealz(unittest.TestCase):
    def test_parse_german_price(self):
        self.assertEqual(parse_german_price("1.299,95 €"), 1299.95)
        self.assertEqual(parse_german_price("69,90€"), 69.90)
        self.assertEqual(parse_german_price("49€"), 49.0)
        self.assertIsNone(parse_german_price("kostenlos"))

    def test_compute_discount_from_prices_or_title(self):
        self.assertEqual(compute_discount_pct(70.0, 100.0, "Samsung SSD"), 30.0)
        self.assertEqual(compute_discount_pct(None, None, "Levi's 501 Jeans Hose mit -40% Rabatt"), 40.0)
        self.assertEqual(compute_discount_pct(None, None, "Adidas Schuhe 35% Extra-Rabatt"), 35.0)
        # Must NOT confuse fabric composition (94% Baumwolle) with a 94% discount!
        self.assertEqual(compute_discount_pct(47.61, None, "Levi's 501 Jeans (94% Baumwolle, 5% Polyester)"), 0.0)

    def test_classify_keyword_includes_pants_clothing_shoes_and_hardware(self):
        self.assertEqual(classify_keyword("WD Black SN850X 2TB NVMe SSD"), ("electronics", "SSD"))
        self.assertEqual(classify_keyword("Seagate Expansion 16TB externe HDD Festplatte"), ("electronics", "HDD"))
        self.assertEqual(classify_keyword("Samsung Galaxy Tab S9 FE Tablet"), ("electronics", "Tablet"))
        self.assertEqual(classify_keyword("Levi's 501 Herren Jeans Hose"), ("fashion", "Kıyafet (Pantolon/Giyim)"))
        self.assertEqual(classify_keyword("Carhartt Cargohose & Hoodie"), ("fashion", "Kıyafet (Pantolon/Giyim)"))
        self.assertEqual(classify_keyword("Nike Air Max Sneaker Schuhe"), ("fashion", "Ayakkabı"))
        self.assertIsNone(classify_keyword("Kaffeemaschine DeLonghi"))

    def test_parse_mydealz_rss_extracts_deal_and_filters_temp(self):
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:pepper="http://www.pepper.com/rss">
          <channel>
            <item>
              <title><![CDATA[[185°] Crucial P3 Plus 2TB NVMe SSD für 89,99€ statt 129,99€ (-31%)]]></title>
              <link>https://www.mydealz.de/deals/crucial-p3-plus-2tb-12345</link>
              <guid>12345</guid>
              <description><![CDATA[Super Preis für 2TB SSD (PVG: 129,99€)]]></description>
            </item>
            <item>
              <title><![CDATA[[10°] Kalter Deal Jeans Hose für 40€ statt 80€]]></title>
              <link>https://www.mydealz.de/deals/kalter-deal-99999</link>
              <guid>99999</guid>
              <description><![CDATA[Kalter Deal]]></description>
            </item>
          </channel>
        </rss>"""
        deals = parse_mydealz_rss(sample_xml, min_temp=50)
        self.assertEqual(len(deals), 1)
        self.assertEqual(deals[0].category, "electronics")
        self.assertEqual(deals[0].subcategory, "SSD")
        self.assertEqual(deals[0].current_price, 89.99)
        self.assertEqual(deals[0].old_price, 129.99)
        self.assertEqual(round(deals[0].discount_pct), 31)

    def test_parse_mydealz_rss_skips_old_and_expired_deals(self):
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:pepper="http://www.pepper.com/rss">
          <channel>
            <item>
              <title><![CDATA[[250°] Levi's 501 Jeans Hose für 39,99€ statt 89,99€]]></title>
              <link>https://www.mydealz.de/deals/old-levis-111</link>
              <guid>111</guid>
              <pubDate>Tue, 27 Oct 2026 10:00:00 +0100</pubDate>
              <description><![CDATA[Alter Deal vom 27.10]]></description>
            </item>
            <item>
              <title><![CDATA[[190°] [Abgelaufen] Samsung SSD 2TB für 99€ statt 149€]]></title>
              <link>https://www.mydealz.de/deals/expired-ssd-222</link>
              <guid>222</guid>
              <description><![CDATA[Leider schon abgelaufen / ausverkauft]]></description>
            </item>
          </channel>
        </rss>"""
        deals = parse_mydealz_rss(sample_xml, min_temp=50, max_age_hours=48)
        self.assertEqual(len(deals), 0)


if __name__ == "__main__":
    unittest.main()

