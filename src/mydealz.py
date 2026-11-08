from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import re
import xml.etree.ElementTree as ET
from typing import Optional
import requests
from bs4 import BeautifulSoup
from src.models import Deal
from src.parser_utils import (
    classify_keyword,
    compute_discount_pct,
    extract_current_and_old_price,
    parse_german_price,
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)

MYDEALZ_FEEDS = [
    "https://www.mydealz.de/rss/hot",
    "https://www.mydealz.de/rss/alles",
    "https://www.mydealz.de/rss/gruppe/ssd",
    "https://www.mydealz.de/rss/gruppe/festplatte",
    "https://www.mydealz.de/rss/gruppe/tablet",
    "https://www.mydealz.de/rss/gruppe/schuhe",
    "https://www.mydealz.de/rss/gruppe/bekleidung",
    "https://www.mydealz.de/rss/gruppe/jeans",
    "https://www.mydealz.de/rss/gruppe/hosen",
]

EXPIRED_MARKERS = (
    "abgelaufen",
    "ausverkauft",
    "beendet",
    "expired",
    "sold out",
    "nicht mehr verfügbar",
    "deal vorbei",
)


def _extract_temperature(title: str, raw_item_xml: str = "") -> Optional[int]:
    m = re.search(r"([+-]?\d+)\s*°", title)
    if m:
        return int(m.group(1))
    m_xml = re.search(r"([+-]?\d+)\s*°", raw_item_xml)
    if m_xml:
        return int(m_xml.group(1))
    return None


def _is_too_old(pub_date_str: str, max_age_hours: int) -> bool:
    if not pub_date_str or max_age_hours <= 0:
        return False
    try:
        dt = parsedate_to_datetime(pub_date_str.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - dt) > timedelta(hours=max_age_hours)
    except (ValueError, TypeError):
        return False


def _has_expired_text(title: str, desc_text: str) -> bool:
    combined = f"{title} {desc_text}".lower()
    return any(marker in combined for marker in EXPIRED_MARKERS)


def is_deal_expired_on_page(url: str, timeout: int = 8) -> bool:
    """Checks the live MyDealz deal page to make sure it hasn't been marked expired (Abgelaufen)."""
    if not url or "mydealz.de" not in url:
        return False
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code in (404, 410):
            return True
        if resp.status_code != 200:
            return False
        html_lower = resp.text.lower()
        if '"isexpired":true' in html_lower or '"status":"expired"' in html_lower:
            return True
        if "dieser deal ist leider abgelaufen" in html_lower:
            return True
        return False
    except requests.RequestException:
        return False


def parse_mydealz_rss(
    xml_text: str, min_temp: int = 50, max_age_hours: int = 36
) -> list[Deal]:
    deals: list[Deal] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return deals

    ns = {"pepper": "http://www.pepper.com/rss"}

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        desc_html = item.findtext("description") or ""
        desc_text = BeautifulSoup(desc_html, "html.parser").get_text(" ", strip=True)

        # 1. Skip deals older than max_age_hours (e.g. from October 27!)
        if _is_too_old(pub_date, max_age_hours=max_age_hours):
            continue

        # 2. Skip deals explicitly marked expired/sold-out in RSS text
        if _has_expired_text(title, desc_text):
            continue

        temp = _extract_temperature(title, desc_text)
        if temp is not None and temp < min_temp:
            continue

        classification = classify_keyword(title)
        if not classification:
            continue
        category, subcategory = classification

        current_price, old_price = extract_current_and_old_price(title, desc_text)

        merchant = item.find("pepper:merchant", ns)
        if merchant is not None and current_price is None:
            current_price = parse_german_price(merchant.attrib.get("price", ""))

        discount_pct = compute_discount_pct(current_price, old_price, f"{title} {desc_text}")

        deal_id = f"mydealz:{guid.split('/')[-1]}"
        deals.append(
            Deal(
                deal_id=deal_id,
                title=title,
                category=category,
                subcategory=subcategory,
                current_price=current_price,
                old_price=old_price,
                discount_pct=discount_pct,
                temperature=temp,
                url=link,
                source="mydealz",
            )
        )

    return deals


def fetch_mydealz_deals(
    min_temp: int = 50, max_age_hours: int = 36, timeout: int = 12
) -> list[Deal]:
    seen_ids: set[str] = set()
    all_deals: list[Deal] = []
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9"}

    for feed_url in MYDEALZ_FEEDS:
        try:
            resp = requests.get(feed_url, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                continue
            parsed = parse_mydealz_rss(
                resp.text, min_temp=min_temp, max_age_hours=max_age_hours
            )
            for d in parsed:
                if d.deal_id not in seen_ids:
                    seen_ids.add(d.deal_id)
                    all_deals.append(d)
        except requests.RequestException:
            continue

    return all_deals
