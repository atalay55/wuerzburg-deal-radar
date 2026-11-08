# Würzburg Black Friday Deal Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a hybrid German Black Friday deal radar (MyDealz + Geizhals) for SSD, HDD, Tablet, Shoes, and Clothing (pants, jackets, hoodies, etc.) that alerts via Telegram whenever a deal hits the discount threshold AND re-alerts whenever the price drops further (e.g., from 20% off to 30% off).

**Architecture:** A modular Python 3.11+ package (`src/`) with 4 focused modules: `models.py` & `state.py` (price-aware deduplication that triggers re-alerts on further price drops), `mydealz.py` (RSS/HTML parser extracting temperature, current price, reference price, and discount %), `geizhals.py` (hardware price-drop parser for SSD/HDD/Tablet), and `notifier.py` + `main.py` (Telegram formatting & CLI/GitHub Actions runner).

**Tech Stack:** Python 3.11+, `httpx` (or `requests`), `beautifulsoup4`, `pytest` for unit tests, GitHub Actions for free 24/7 scheduling.

**Spec:** `docs/superpowers/specs/2026-11-08-wuerzburg-deal-radar-design.md`

## Global Constraints

- Minimum discount threshold defaults: `20.0%` for electronics (`SSD`, `HDD`, `Tablet`), `30.0%` for fashion (`Shoes`, `Clothing` including pants/Hose, Jeans, Jacke, Hoodie, etc.).
- Re-alert rule: If a previously alerted item (`deal_id`) appears again with a strictly lower `current_price` OR strictly higher `discount_pct` (by at least `1.0%` or `0.50€`), it MUST trigger a new notification marked as a further price drop (`is_price_update=True`).
- Minimal dependencies (YAGNI): standard library + `requests`, `beautifulsoup4`, `pytest`.

## Review Focus

- German number formats in prices (`"89,99 €"`, `"1.299,00€"`, `"-25%"`) must parse accurately to `float`.
- Missing reference price (`old_price=None`) when a percentage coupon (e.g., `"-35% bei Adidas"`) is in the title must still extract `discount_pct=35.0`.
- Same price or higher price on an already seen `deal_id` must NOT trigger a duplicate alert.
- Further price drop (`20%` -> `30%`, or `80€` -> `70€`) on an already seen `deal_id` MUST trigger a re-alert and update stored state.
- Network timeouts or malformed HTML on one source must not crash the entire run.

---

### Task 1: Data Models & Price-Aware State Store (Re-Alert on Further Drops)

**Files:**
- Create: `src/models.py`
- Create: `src/state.py`
- Create: `requirements.txt`
- Test: `tests/test_state.py`

**Interfaces:**
- Produces:
  - `Deal` dataclass in `src/models.py`: `deal_id: str`, `title: str`, `category: str` (`"electronics"` | `"fashion"`), `subcategory: str`, `current_price: Optional[float]`, `old_price: Optional[float]`, `discount_pct: float`, `temperature: Optional[int]`, `url: str`, `source: str`
  - `EvaluationResult` dataclass in `src/state.py`: `should_alert: bool`, `is_price_update: bool`, `previous_price: Optional[float]`, `previous_discount_pct: Optional[float]`
  - `DealStateStore(path: Path)` in `src/state.py` with `.evaluate_and_record(deal: Deal, min_discount_pct: float) -> EvaluationResult` and `.save() -> None`

- [ ] **Step 1: Write the failing tests in `tests/test_state.py`**

```python
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

def test_first_time_deal_above_threshold_alerts(tmp_path: Path):
    store = DealStateStore(tmp_path / "seen.json")
    res = store.evaluate_and_record(make_deal(price=80.0, discount=20.0), min_discount_pct=20.0)
    assert res.should_alert is True
    assert res.is_price_update is False

def test_same_price_does_not_alert_again(tmp_path: Path):
    store = DealStateStore(tmp_path / "seen.json")
    store.evaluate_and_record(make_deal(price=80.0, discount=20.0), min_discount_pct=20.0)
    res2 = store.evaluate_and_record(make_deal(price=80.0, discount=20.0), min_discount_pct=20.0)
    assert res2.should_alert is False

def test_further_discount_20_to_30_triggers_update_alert(tmp_path: Path):
    store = DealStateStore(tmp_path / "seen.json")
    store.evaluate_and_record(make_deal(price=80.0, discount=20.0), min_discount_pct=20.0)
    store.save()

    store_reloaded = DealStateStore(tmp_path / "seen.json")
    res_drop = store_reloaded.evaluate_and_record(make_deal(price=70.0, discount=30.0), min_discount_pct=20.0)
    assert res_drop.should_alert is True
    assert res_drop.is_price_update is True
    assert res_drop.previous_price == 80.0
    assert res_drop.previous_discount_pct == 20.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_state.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src'`

- [ ] **Step 3: Implement `src/models.py` and `src/state.py`**

Implement `Deal` in `src/models.py` and `DealStateStore` in `src/state.py` so that:
- Deals below `min_discount_pct` return `should_alert=False`.
- Unseen deals at or above `min_discount_pct` record `{price, discount_pct, title, updated_at}` and return `should_alert=True, is_price_update=False`.
- Seen deals where `deal.current_price < prev_price - 0.01` OR `deal.discount_pct >= prev_discount + 1.0` update the stored record and return `should_alert=True, is_price_update=True, previous_price=prev_price, previous_discount_pct=prev_discount`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_state.py -v`
Expected: PASS

---

### Task 2: German Price/Discount Parser & MyDealz Scanner (Electronics + Fashion/Pants)

**Files:**
- Create: `src/parser_utils.py`
- Create: `src/mydealz.py`
- Test: `tests/test_mydealz.py`

**Interfaces:**
- Consumes: `Deal` from `src/models.py`
- Produces:
  - `parse_german_price(text: str) -> Optional[float]` in `src/parser_utils.py`
  - `compute_discount_pct(current_price: Optional[float], old_price: Optional[float], title: str) -> float` in `src/parser_utils.py`
  - `classify_keyword(text: str) -> Optional[tuple[str, str]]` in `src/parser_utils.py` returning `(category, subcategory)` covering `SSD`, `HDD`, `Tablet`, `Ayakkabı/Schuhe`, `Kıyafet/Hose/Jeans/Jacke/Hoodie/Shirt`
  - `parse_mydealz_rss(xml_text: str, min_temp: int = 50) -> list[Deal]` in `src/mydealz.py`
  - `fetch_mydealz_deals(min_temp: int = 50) -> list[Deal]` in `src/mydealz.py`

- [ ] **Step 1: Write the failing tests in `tests/test_mydealz.py`**

```python
from src.parser_utils import parse_german_price, compute_discount_pct, classify_keyword
from src.mydealz import parse_mydealz_rss

def test_parse_german_price():
    assert parse_german_price("1.299,95 €") == 1299.95
    assert parse_german_price("69,90€") == 69.90
    assert parse_german_price("kostenlos") is None

def test_compute_discount_from_prices_or_title():
    assert compute_discount_pct(70.0, 100.0, "Samsung SSD") == 30.0
    assert compute_discount_pct(None, None, "Levi's 501 Jeans Hose mit -40% Rabatt") == 40.0

def test_classify_keyword_includes_pants_and_hardware():
    assert classify_keyword("WD Black SN850X 2TB NVMe SSD") == ("electronics", "SSD")
    assert classify_keyword("Levi's 501 Herren Jeans Hose") == ("fashion", "Kıyafet (Pantolon/Giyim)")
    assert classify_keyword("Nike Air Max Sneaker Schuhe") == ("fashion", "Ayakkabı")

def test_parse_mydealz_rss_extracts_deal():
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:pepper="http://www.pepper.com/rss">
      <channel>
        <item>
          <title><![CDATA[[185°] Crucial P3 Plus 2TB NVMe SSD für 89,99€ statt 129,99€ (-31%)]]></title>
          <link>https://www.mydealz.de/deals/crucial-p3-plus-2tb-12345</link>
          <guid>12345</guid>
          <description><![CDATA[Super Preis für 2TB SSD]]></description>
        </item>
      </channel>
    </rss>"""
    deals = parse_mydealz_rss(sample_xml, min_temp=50)
    assert len(deals) == 1
    assert deals[0].category == "electronics"
    assert deals[0].current_price == 89.99
    assert deals[0].old_price == 129.99
    assert round(deals[0].discount_pct) == 31
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_mydealz.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `src/parser_utils.py` and `src/mydealz.py`**

Implement German price parsing (`statt X€`, `PVG: X€`, `für Y€`, `-Z%`), category/keyword matching (including `hose`, `jeans`, `cargohose`, `jogginghose`, `chino`, `pullover`, `hoodie`, `jacke`, `t-shirt`, `hemd`, `kleidung`, `schuhe`, `sneaker`, `stiefel`, `ssd`, `nvme`, `hdd`, `festplatte`, `tablet`, `ipad`, `galaxy tab`), and RSS feed parsing.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_mydealz.py -v`
Expected: PASS

---

### Task 3: Geizhals.de Hardware Price-Drop Scanner & Telegram Notifier + Runner

**Files:**
- Create: `src/geizhals.py`
- Create: `src/notifier.py`
- Create: `src/main.py`
- Create: `.github/workflows/deal_radar.yml`
- Create: `README.md`
- Test: `tests/test_notifier_and_geizhals.py`

**Interfaces:**
- Consumes: `Deal` from `src/models.py`, `EvaluationResult` & `DealStateStore` from `src/state.py`
- Produces:
  - `parse_geizhals_price_drops(html: str, subcategory: str) -> list[Deal]` in `src/geizhals.py`
  - `format_telegram_message(deal: Deal, eval_result: EvaluationResult) -> str` in `src/notifier.py`
  - `send_telegram_message(token: str, chat_id: str, text: str) -> bool` in `src/notifier.py`
  - `run_radar(...)` CLI entrypoint in `src/main.py`

- [ ] **Step 1: Write the failing tests in `tests/test_notifier_and_geizhals.py`**

```python
from src.models import Deal
from src.state import EvaluationResult
from src.notifier import format_telegram_message
from src.geizhals import parse_geizhals_price_drops

def test_format_telegram_message_marks_further_price_drop():
    deal = Deal(
        deal_id="d1",
        title="Levi's 501 Jeans",
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
    assert "FİYAT DAHA DA DÜŞTÜ" in msg
    assert "69.00€" in msg or "69,00€" in msg
    assert "49.00€" in msg or "49,00€" in msg
    assert "51%" in msg

def test_parse_geizhals_price_drops_sample_html():
    html = """
    <div class="productlist__item">
      <a class="productlist__link" href="https://geizhals.de/kingston-nv2-1tb-a2807718.html">Kingston NV2 1TB SSD</a>
      <span class="price">48,90 €</span>
      <span class="price-drop">-24%</span>
    </div>
    """
    deals = parse_geizhals_price_drops(html, subcategory="SSD")
    assert len(deals) == 1
    assert deals[0].current_price == 48.90
    assert deals[0].discount_pct == 24.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_notifier_and_geizhals.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `src/geizhals.py`, `src/notifier.py`, `src/main.py`, and `.github/workflows/deal_radar.yml`**

Implement:
- `src/geizhals.py`: parses Geizhals price drop items and also supports monitoring specific Geizhals/Idealo URLs added by the user in `config.json`.
- `src/notifier.py`: formats initial alerts (`🚨 YENİ İNDİRİM YAKALANDI`) vs. further price-drop alerts (`🔥🔥 EK İNDİRİM: FİYAT DAHA DA DÜŞTÜ! Önceki: X€ (%Y) -> Şimdi: Z€ (%W)`) and sends via Telegram Bot API.
- `src/main.py`: loads config/env, fetches deals from MyDealz & Geizhals, runs `DealStateStore.evaluate_and_record`, sends notifications, and supports `--dry-run` (prints to console without requiring Telegram keys for instant testing).
- `.github/workflows/deal_radar.yml`: runs every 10 minutes on GitHub Actions and commits updated `data/seen_deals.json` so price history persists across runs.

- [ ] **Step 4: Run full test suite and a live dry-run**

Run: `pytest -v` and `python -m src.main --dry-run`
Expected: All tests PASS and live deals from Germany are printed to terminal.

