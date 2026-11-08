from typing import Optional
import requests
from src.models import Deal
from src.state import EvaluationResult


def format_telegram_message(deal: Deal, eval_result: EvaluationResult) -> str:
    if eval_result.is_price_update:
        header = "🔥🔥 <b>EK İNDİRİM: FİYAT DAHA DA DÜŞTÜ!</b> 🔥🔥"
    else:
        header = "🚨 <b>YENİ İNDİRİM YAKALANDI!</b> 🚨"

    price_str = f"{deal.current_price:.2f}€" if deal.current_price is not None else "Kampanya / Kupon"
    old_str = f" (Normal/PVG: <s>{deal.old_price:.2f}€</s>)" if deal.old_price is not None else ""
    temp_str = f" | 🌡️ {deal.temperature}°" if deal.temperature is not None else ""

    lines = [
        header,
        f"🏷️ <b>Kategori:</b> {deal.subcategory} ({deal.source.upper()}){temp_str}",
        f"📦 <b>Ürün:</b> {deal.title}",
        f"💰 <b>Fiyat:</b> <b>{price_str}</b>{old_str}",
        f"📉 <b>İndirim Oranı:</b> <b>-{deal.discount_pct:.1f}%</b>",
    ]

    if eval_result.is_price_update:
        prev_p = (
            f"{eval_result.previous_price:.2f}€"
            if eval_result.previous_price is not None
            else "Bilinmiyor"
        )
        prev_d = (
            f"-{eval_result.previous_discount_pct:.1f}%"
            if eval_result.previous_discount_pct is not None
            else ""
        )
        lines.append(
            f"⚡ <b>Önceki Bildirim:</b> {prev_p} ({prev_d}) ➡️ <b>Şimdi: {price_str} (-{deal.discount_pct:.1f}%)</b>"
        )

    lines.append(f"🔗 <a href=\"{deal.url}\">Fırsata Git / Satıcıları Gör</a>")
    return "\n".join(lines)


def extract_chat_id_from_updates(data: dict) -> Optional[str]:
    results = data.get("result") or []
    for item in reversed(results):
        msg = item.get("message") or item.get("edited_message") or {}
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is not None:
            return str(chat_id)
    return None


def auto_detect_chat_id(token: str, timeout: int = 10) -> Optional[str]:
    if not token:
        return None
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None
        return extract_chat_id_from_updates(resp.json())
    except (requests.RequestException, ValueError):
        return None


def send_telegram_message(token: str, chat_id: str, text: str, timeout: int = 10) -> bool:
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        return resp.status_code == 200
    except requests.RequestException:
        return False
