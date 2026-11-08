import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from src.models import Deal
from src.parser_utils import compute_discount_pct, parse_german_price

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)

# Geizhals category URLs sorted by popularity/price-drop for SSD, HDD, Tablet
GEIZHALS_CATEGORY_URLS: list[tuple[str, str]] = [
    ("SSD", "https://geizhals.de/?cat=hdssd&xf=252_960&sort=p"),
    ("HDD", "https://geizhals.de/?cat=hde7s&xf=958_1000&sort=p"),
    ("Tablet", "https://geizhals.de/?cat=nbtabl&sort=r"),
]


def parse_geizhals_price_drops(html: str, subcategory: str = "SSD") -> list[Deal]:
    deals: list[Deal] = []
    soup = BeautifulSoup(html, "html.parser")

    # Supports both Geizhals productlist rows and generic price-drop blocks
    rows = soup.select(".productlist__item, .listview__item, tr.t1, tr.t2")
    for row in rows:
        link_el = row.select_one("a.productlist__link, a.listview__name-link, a[href*='-a']")
        if not link_el:
            continue
        title = link_el.get_text(" ", strip=True)
        href = link_el.get("href", "")
        if not title or not href:
            continue

        full_url = urljoin("https://geizhals.de/", href)
        row_text = row.get_text(" ", strip=True)

        current_price = parse_german_price(row_text)
        discount_pct = compute_discount_pct(current_price, None, row_text)
        if discount_pct <= 0:
            continue

        old_price = (
            round(current_price / (1.0 - discount_pct / 100.0), 2)
            if current_price and discount_pct < 95.0
            else None
        )

        # Extract Geizhals product ID like a2807718
        m_id = re.search(r"-(a\d+)\.html", full_url)
        raw_id = m_id.group(1) if m_id else re.sub(r"\W+", "_", title.lower())[:32]

        deals.append(
            Deal(
                deal_id=f"geizhals:{raw_id}",
                title=title,
                category="electronics",
                subcategory=subcategory,
                current_price=current_price,
                old_price=old_price,
                discount_pct=discount_pct,
                temperature=None,
                url=full_url,
                source="geizhals",
            )
        )

    return deals


def fetch_geizhals_deals(timeout: int = 12) -> list[Deal]:
    deals: list[Deal] = []
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9"}

    for subcat, url in GEIZHALS_CATEGORY_URLS:
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                continue
            deals.extend(parse_geizhals_price_drops(resp.text, subcategory=subcat))
        except requests.RequestException:
            continue

    return deals

