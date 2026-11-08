import re
from typing import Optional

# Keyword groups covering all requested categories in German & English
CATEGORY_KEYWORDS: list[tuple[str, str, list[str]]] = [
    (
        "electronics",
        "SSD",
        ["ssd", "nvme", "m.2", "solid state", "990 pro", "sn850x", "sn770", "crucial p3", "samsung t7", "samsung t9"],
    ),
    (
        "electronics",
        "HDD",
        ["hdd", "festplatte", "externe festplatte", "wd elements", "seagate expansion", "ironwolf", "wd red", "toshiba canvio"],
    ),
    (
        "electronics",
        "Tablet",
        ["tablet", "ipad", "galaxy tab", "xiaomi pad", "redmi pad", "lenovo tab", "surface pro", "matepad"],
    ),
    (
        "fashion",
        "Ayakkabı",
        [
            "schuhe", "sneaker", "laufschuhe", "sportschuhe", "stiefel", "boots", "turnschuhe",
            "air force", "air max", "ultraboost", "new balance", "puma", "asics", "salomon", "vans", "converse",
        ],
    ),
    (
        "fashion",
        "Kıyafet (Pantolon/Giyim)",
        [
            "hose", "jeans", "cargohose", "jogginghose", "sweatpants", "chino", "trainingshose", "shorts",
            "pantolon", "jacke", "winterjacke", "übergangsjacke", "fleecejacke", "daunenjacke", "mantel",
            "hoodie", "kapuzenpullover", "pullover", "sweatshirt", "strickjacke",
            "t-shirt", "shirt", "polohemd", "hemd", "unterwäsche", "boxershorts", "socken",
            "kleidung", "bekleidung", "mode", "outfit", "levi's", "levis", "carhartt", "tommy hilfiger",
        ],
    ),
]


def parse_german_price(text: str) -> Optional[float]:
    if not text:
        return None
    match = re.search(r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:\.\d{1,2})?)\s*€", text)
    if not match:
        return None
    raw = match.group(1).strip()
    if "," in raw:
        normalized = raw.replace(".", "").replace(",", ".")
    else:
        # Check if dot is a thousands separator (e.g. "1.299")
        if re.match(r"^\d{1,3}\.\d{3}$", raw):
            normalized = raw.replace(".", "")
        else:
            normalized = raw
    try:
        val = float(normalized)
        return val if val > 0 else None
    except ValueError:
        return None


def extract_current_and_old_price(title: str, description: str = "") -> tuple[Optional[float], Optional[float]]:
    combined = f"{title} {description}"

    # Look for explicit comparison patterns first: "für 89,99€ statt 129,99€" or "PVG: 129,99€" or "(Idealo: 129,99€)"
    old_price: Optional[float] = None
    old_patterns = [
        r"(?:statt|pvg|idealo|vergleichspreis|uvp|vorher|bisher)[:\s]*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?\s*€)",
        r"\[(?:pvg|idealo|statt)[:\s]*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?\s*€)\]",
    ]
    for pat in old_patterns:
        m = re.search(pat, combined, flags=re.IGNORECASE)
        if m:
            old_price = parse_german_price(m.group(1))
            if old_price:
                break

    # Extract current price from title (usually the first price before 'statt'/'pvg')
    title_before_statt = re.split(r"\b(?:statt|pvg|idealo|uvp)\b", title, flags=re.IGNORECASE)[0]
    current_price = parse_german_price(title_before_statt)

    if old_price is not None and current_price is not None and old_price <= current_price:
        old_price = None

    return current_price, old_price


def compute_discount_pct(
    current_price: Optional[float], old_price: Optional[float], text: str = ""
) -> float:
    if current_price is not None and old_price is not None and old_price > current_price > 0:
        return round(((old_price - current_price) / old_price) * 100.0, 1)

    # Match explicit negative percentages like "-35%" or percentages followed by discount keywords
    explicit_patterns = [
        r"-\s*(\d{1,2})\s*%",
        r"\b(\d{1,2})\s*%\s*(?:extra-?rabatt|rabatt|extra|sale|off|sparen|günstiger|reduziert|nachlass)\b",
        r"(?:bis\s+zu|mit)\s+(\d{1,2})\s*%",
    ]
    for pat in explicit_patterns:
        for m in re.findall(pat, text, flags=re.IGNORECASE):
            val = float(m)
            if 5.0 <= val <= 90.0:
                return val

    return 0.0


def classify_keyword(text: str) -> Optional[tuple[str, str]]:
    lowered = text.lower()
    for category, subcategory, keywords in CATEGORY_KEYWORDS:
        for kw in keywords:
            # Word-boundary aware match for short words like ssd/hdd/hose
            if len(kw) <= 4:
                if re.search(rf"\b{re.escape(kw)}\b", lowered):
                    return (category, subcategory)
            else:
                if kw in lowered:
                    return (category, subcategory)
    return None

