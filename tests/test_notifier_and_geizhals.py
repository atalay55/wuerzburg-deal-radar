import unittest
from src.models import Deal
from src.state import EvaluationResult
from src.notifier import format_telegram_message, extract_chat_id_from_updates
from src.geizhals import parse_geizhals_price_drops


class TestNotifierAndGeizhals(unittest.TestCase):
    def test_format_telegram_message_marks_further_price_drop(self):
        deal = Deal(
            deal_id="d1",
            title="Levi's 501 Jeans Hose",
            category="fashion",
            subcategory="Kıyafet (Pantolon/Giyim)",
            current_price=49.0,
            old_price=100.0,
            discount_pct=51.0,
            temperature=200,
            url="https://example.com/levis",
            source="mydealz",
        )
        eval_res = EvaluationResult(
            should_alert=True,
            is_price_update=True,
            previous_price=69.0,
            previous_discount_pct=31.0,
        )
        msg = format_telegram_message(deal, eval_res)
        self.assertIn("FİYAT DAHA DA DÜŞTÜ", msg)
        self.assertIn("69.00€", msg)
        self.assertIn("49.00€", msg)
        self.assertIn("51.0%", msg)

    def test_format_telegram_message_initial_alert(self):
        deal = Deal(
            deal_id="d2",
            title="Samsung 990 PRO 2TB SSD",
            category="electronics",
            subcategory="SSD",
            current_price=129.99,
            old_price=179.99,
            discount_pct=27.8,
            temperature=310,
            url="https://example.com/ssd",
            source="mydealz",
        )
        eval_res = EvaluationResult(should_alert=True, is_price_update=False)
        msg = format_telegram_message(deal, eval_res)
        self.assertIn("YENİ İNDİRİM YAKALANDI", msg)
        self.assertIn("129.99€", msg)
        self.assertIn("27.8%", msg)

    def test_parse_geizhals_price_drops_sample_html(self):
        html = """
        <div class="productlist__item">
          <a class="productlist__link" href="https://geizhals.de/kingston-nv2-1tb-a2807718.html">Kingston NV2 1TB NVMe SSD</a>
          <span class="price">48,90 €</span>
          <span class="price-drop">-24%</span>
        </div>
        """
        deals = parse_geizhals_price_drops(html, subcategory="SSD")
        self.assertEqual(len(deals), 1)
        self.assertEqual(deals[0].current_price, 48.90)
        self.assertEqual(deals[0].discount_pct, 24.0)
        self.assertEqual(deals[0].subcategory, "SSD")

    def test_extract_chat_id_from_updates(self):
        payload = {
            "ok": True,
            "result": [
                {"update_id": 1, "message": {"chat": {"id": 987654321}, "text": "/start"}}
            ],
        }
        self.assertEqual(extract_chat_id_from_updates(payload), "987654321")
        self.assertIsNone(extract_chat_id_from_updates({"ok": True, "result": []}))


if __name__ == "__main__":
    unittest.main()

