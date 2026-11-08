# Würzburg Black Friday Deal Radar 🇩🇪🎯

Almanya'daki (MyDealz.de + Geizhals.de) **SSD, HDD, Tablet, Ayakkabı ve Genel Kıyafet (Pantolon, Jeans, Eşofman, Ceket, Hoodie, Tişört vb.)** fırsatlarını tarayan, sahte indirimleri eleyen ve **fiyat daha da düştüğünde (%20 -> %30 gibi) tekrar bildirim atan** Telegram botu.

## Özellikler
1. **Kademeli İndirim Takibi (`src/state.py`):**
   - Bir ürün ilk kez eşiği geçtiğinde (ör. `%20` indirim, `80€`) **🚨 YENİ İNDİRİM YAKALANDI** bildirimi atar.
   - Aynı fiyatta kaldığı sürece tekrar mesaj atıp rahatsız etmez.
   - Fiyatı daha da düşerse (ör. `%30` indirim, `70€` olursa) **🔥🔥 EK İNDİRİM: FİYAT DAHA DA DÜŞTÜ! (Önceki: 80.00€ -> Şimdi: 70.00€)** diye tekrar alarm verir.
2. **Kategoriler (`src/parser_utils.py`):**
   - **Donanım (Varsayılan en az %20 indirim):** SSD, NVMe, M.2, HDD, Externe Festplatte, Tablet, iPad, Galaxy Tab, Xiaomi Pad.
   - **Giyim & Ayakkabı (Varsayılan en az %30 indirim):** Pantolon (`Hose`, `Jeans`, `Cargohose`, `Jogginghose`, `Chino`), Üst Giyim (`Jacke`, `Winterjacke`, `Hoodie`, `Pullover`, `Sweatshirt`, `T-Shirt`, `Hemd`), Ayakkabı (`Schuhe`, `Sneaker`, `Stiefel`, `Boots`).

## Hızlı Kurulum ve Çalıştırma

### 1. Telegram Bot Token ve Chat ID Alma (2 Dakika)
1. Telegram'da **@BotFather**'a git, `/newbot` yaz, botuna bir isim ver. Sana verdiği `TELEGRAM_BOT_TOKEN` değerini kopyala ve kendi botuna **Başlat (Start)** de.
2. Telegram'da **@userinfobot**'a git, `/start` yaz, sana verdiği `Id` numarasını (`TELEGRAM_CHAT_ID`) kopyala.
3. Bu iki değeri `config.json` dosyasına yapıştır:
   ```json
   {
     "telegram_bot_token": "BURAYA_BOT_TOKEN",
     "telegram_chat_id": "BURAYA_CHAT_ID",
     "min_discount_electronics_pct": 20.0,
     "min_discount_fashion_pct": 30.0,
     "min_mydealz_temperature": 50,
     "check_interval_seconds": 300
   }
   ```

### 2. Bilgisayarında Çalıştırma
- **Tek seferlik ekran testi (Telegram'sız deneme):**
  ```powershell
  python -m src.main --dry-run
  ```
- **Sürekli arka planda çalıştırma (5 dakikada bir kontrol eder ve Telegram'a atar):**
  ```powershell
  python -m src.main --loop
  ```
- **Testleri çalıştırma:**
  ```powershell
  python -m unittest discover -s tests -v
  ```

