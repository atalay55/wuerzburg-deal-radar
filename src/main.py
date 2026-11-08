import argparse
import json
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.geizhals import fetch_geizhals_deals
from src.mydealz import fetch_mydealz_deals, is_deal_expired_on_page
from src.notifier import auto_detect_chat_id, format_telegram_message, send_telegram_message
from src.state import DealStateStore

DEFAULT_CONFIG_PATH = BASE_DIR / "config.json"
DEFAULT_STATE_PATH = BASE_DIR / "data" / "seen_deals.json"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    defaults = {
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "min_discount_electronics_pct": 20.0,
        "min_discount_fashion_pct": 30.0,
        "min_mydealz_temperature": 50,
        "check_interval_seconds": 300,
    }
    if path.exists():
        try:
            user_cfg = json.loads(path.read_text(encoding="utf-8"))
            defaults.update(user_cfg)
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


def save_config(cfg: dict, path: Path = DEFAULT_CONFIG_PATH) -> None:
    try:
        path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def ensure_telegram_connected(cfg: dict, config_path: Path = DEFAULT_CONFIG_PATH, wait_for_user: bool = False) -> tuple[str, str]:
    tg_token = (os.environ.get("TELEGRAM_BOT_TOKEN") or cfg.get("telegram_bot_token") or "").strip()
    tg_chat_id = (os.environ.get("TELEGRAM_CHAT_ID") or cfg.get("telegram_chat_id") or "").strip()

    if not tg_token or tg_chat_id:
        return tg_token, tg_chat_id

    while True:
        detected = auto_detect_chat_id(tg_token)
        if detected:
            tg_chat_id = detected
            cfg["telegram_chat_id"] = detected
            save_config(cfg, config_path)
            print(f"[Otomatik Bağlandı] Telegram Chat ID bulundu ve kaydedildi: {tg_chat_id}", flush=True)
            send_telegram_message(
                tg_token,
                tg_chat_id,
                "✅ <b>Merhaba! Würzburg Black Friday Radar Bağlandı!</b> 🇩🇪🎯\n\n"
                "• <b>Donanım (SSD, HDD, Tablet):</b> En az %20 indirim\n"
                "• <b>Giyim & Ayakkabı (Pantolon, Jeans, Hoodie, Ceket, Sneaker):</b> En az %30 indirim\n"
                "• <b>Kademeli Fiyat Takibi:</b> Bir ürün %20'den %30'a düşerse tekrar alarm verir!\n\n"
                "🔍 <i>Şu anki güncel indirimler taranıyor ve hemen gönderiliyor...</i>",
            )
            return tg_token, tg_chat_id

        if not wait_for_user:
            print(
                "[Uyarı] Telegram Chat ID henüz bulunamadı! Lütfen Telegram'da "
                "https://t.me/Indirim_black_bot adresine tıklayıp 'merhaba' yaz.",
                flush=True,
            )
            return tg_token, ""

        print("[Bekleniyor] https://t.me/Indirim_black_bot üzerinden mesaj bekleniyor (3 sn)...", flush=True)
        time.sleep(3)


def run_once(dry_run: bool = False, config_path: Path = DEFAULT_CONFIG_PATH, wait_for_user: bool = False) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    cfg = load_config(config_path)
    store = DealStateStore(DEFAULT_STATE_PATH)

    tg_token, tg_chat_id = ("", "")
    if not dry_run:
        tg_token, tg_chat_id = ensure_telegram_connected(cfg, config_path, wait_for_user=wait_for_user)

    min_temp = int(cfg["min_mydealz_temperature"])
    deals = fetch_mydealz_deals(min_temp=min_temp) + fetch_geizhals_deals()

    alert_count = 0
    for deal in deals:
        threshold = (
            float(cfg["min_discount_electronics_pct"])
            if deal.category == "electronics"
            else float(cfg["min_discount_fashion_pct"])
        )
        if deal.discount_pct < threshold:
            continue

        # Live check on MyDealz page to guarantee the deal is NOT expired (Abgelaufen)
        if deal.source == "mydealz" and is_deal_expired_on_page(deal.url):
            continue

        eval_res = store.evaluate_and_record(deal, min_discount_pct=threshold)
        if not eval_res.should_alert:
            continue

        msg = format_telegram_message(deal, eval_res)
        alert_count += 1

        if dry_run or not tg_token or not tg_chat_id:
            print("=" * 65, flush=True)
            print(msg, flush=True)
        else:
            sent = send_telegram_message(tg_token, tg_chat_id, msg)
            print(f"[Telegram={'OK' if sent else 'ERR'}] {deal.subcategory}: {deal.title} (-{deal.discount_pct}%)", flush=True)
            time.sleep(0.4)  # Avoid Telegram rate-limit

    # Only persist seen_deals when actually sent to Telegram so dry-runs don't swallow deals!
    if tg_token and tg_chat_id and not dry_run:
        store.save()
        if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
            send_telegram_message(
                tg_token,
                tg_chat_id,
                f"✅ <b>GitHub Actions Bulut Testi Başarılı!</b> ☁️🚀\n"
                f"• <b>Taranan taze fırsat:</b> {len(deals)}\n"
                f"• <b>Gönderilen yeni/ek indirim alarmı:</b> {alert_count}\n"
                f"<i>Sistem bilgisayarın kapalıyken 7/24 aktif olarak çalışıyor.</i>",
            )

    print(f"\n[Tarama Tamamlandı] Taranan uygun kategori fırsatı: {len(deals)} | Yeni/Ek İndirim Alarmı: {alert_count}", flush=True)
    return alert_count


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Würzburg Black Friday Deal Radar")
    parser.add_argument("--dry-run", action="store_true", help="Telegram'a atmadan ekrana yazdırır")
    parser.add_argument("--loop", action="store_true", help="Sürekli arka planda (5 dakikada bir) çalışır")
    args = parser.parse_args()

    cfg = load_config()
    interval = int(cfg.get("check_interval_seconds", 300))

    if not args.loop:
        run_once(dry_run=args.dry_run, wait_for_user=False)
        return

    print(f"🚀 Würzburg Deal Radar başlatıldı! Kontrol sıklığı: {interval} saniye.", flush=True)
    while True:
        try:
            run_once(dry_run=args.dry_run, wait_for_user=True)
        except KeyboardInterrupt:
            print("\nDurduruldu.", flush=True)
            break
        except Exception as exc:
            print(f"[Hata] {exc}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
