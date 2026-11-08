import tempfile
import unittest
from pathlib import Path
from src.models import Deal
from src.state import DealStateStore


def make_deal(deal_id="d1", price=80.0, old_price=100.0, discount=20.0, cat="electronics"):
    return Deal(
        deal_id=deal_id,
        title="Samsung 990 PRO 1TB SSD",
        category=cat,
        subcategory="SSD",
        current_price=price,
        old_price=old_price,
        discount_pct=discount,
        temperature=120,
        url="https://example.com/d1",
        source="mydealz",
    )


class TestDealStateStore(unittest.TestCase):
    def test_first_time_deal_above_threshold_alerts(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = DealStateStore(Path(tmp) / "seen.json")
            res = store.evaluate_and_record(make_deal(price=80.0, discount=20.0), min_discount_pct=20.0)
            self.assertTrue(res.should_alert)
            self.assertFalse(res.is_price_update)

    def test_below_threshold_does_not_alert(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = DealStateStore(Path(tmp) / "seen.json")
            res = store.evaluate_and_record(make_deal(price=85.0, discount=15.0), min_discount_pct=20.0)
            self.assertFalse(res.should_alert)

    def test_same_or_higher_price_does_not_alert_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = DealStateStore(Path(tmp) / "seen.json")
            store.evaluate_and_record(make_deal(price=80.0, discount=20.0), min_discount_pct=20.0)
            res_same = store.evaluate_and_record(make_deal(price=80.0, discount=20.0), min_discount_pct=20.0)
            res_higher = store.evaluate_and_record(make_deal(price=85.0, discount=15.0), min_discount_pct=20.0)
            self.assertFalse(res_same.should_alert)
            self.assertFalse(res_higher.should_alert)

    def test_further_discount_20_to_30_triggers_update_alert(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "seen.json"
            store = DealStateStore(path)
            store.evaluate_and_record(make_deal(price=80.0, discount=20.0), min_discount_pct=20.0)
            store.save()

            store_reloaded = DealStateStore(path)
            res_drop = store_reloaded.evaluate_and_record(
                make_deal(price=70.0, discount=30.0), min_discount_pct=20.0
            )
            self.assertTrue(res_drop.should_alert)
            self.assertTrue(res_drop.is_price_update)
            self.assertEqual(res_drop.previous_price, 80.0)
            self.assertEqual(res_drop.previous_discount_pct, 20.0)

            res_repeat = store_reloaded.evaluate_and_record(
                make_deal(price=70.0, discount=30.0), min_discount_pct=20.0
            )
            self.assertFalse(res_repeat.should_alert)


if __name__ == "__main__":
    unittest.main()
