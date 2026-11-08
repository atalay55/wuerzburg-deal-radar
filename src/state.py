from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional
from src.models import Deal


@dataclass
class EvaluationResult:
    should_alert: bool
    is_price_update: bool = False
    previous_price: Optional[float] = None
    previous_discount_pct: Optional[float] = None


class DealStateStore:
    """
    Stores alerted deals along with their last alerted price and discount percentage.
    If an already-alerted deal drops further in price (or its discount % increases),
    it triggers a new 'is_price_update=True' alert!
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self._records: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._records = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._records = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def evaluate_and_record(self, deal: Deal, min_discount_pct: float) -> EvaluationResult:
        if deal.discount_pct < min_discount_pct:
            return EvaluationResult(should_alert=False)

        prev = self._records.get(deal.deal_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        if prev is None:
            self._records[deal.deal_id] = {
                "title": deal.title,
                "last_price": deal.current_price,
                "last_discount_pct": deal.discount_pct,
                "url": deal.url,
                "updated_at": now_iso,
            }
            return EvaluationResult(should_alert=True, is_price_update=False)

        prev_price = prev.get("last_price")
        prev_discount = float(prev.get("last_discount_pct", 0.0))

        price_dropped = (
            deal.current_price is not None
            and prev_price is not None
            and deal.current_price < float(prev_price) - 0.01
        )
        discount_increased = deal.discount_pct >= prev_discount + 1.0

        if price_dropped or discount_increased:
            self._records[deal.deal_id] = {
                "title": deal.title,
                "last_price": deal.current_price,
                "last_discount_pct": deal.discount_pct,
                "url": deal.url,
                "updated_at": now_iso,
            }
            return EvaluationResult(
                should_alert=True,
                is_price_update=True,
                previous_price=float(prev_price) if prev_price is not None else None,
                previous_discount_pct=prev_discount,
            )

        return EvaluationResult(should_alert=False)

