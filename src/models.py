from dataclasses import dataclass
from typing import Optional


@dataclass
class Deal:
    deal_id: str
    title: str
    category: str          # "electronics" | "fashion"
    subcategory: str       # "SSD", "HDD", "Tablet", "Ayakkabı", "Kıyafet (Pantolon/Giyim)"
    current_price: Optional[float]
    old_price: Optional[float]
    discount_pct: float
    temperature: Optional[int]
    url: str
    source: str            # "mydealz" | "geizhals"

