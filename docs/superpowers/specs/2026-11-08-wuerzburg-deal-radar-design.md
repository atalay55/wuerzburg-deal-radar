# Würzburg Black Friday Deal Radar — Design Spec

## Intent & Why
Würzburg'da yaşayan bir öğrenci için Black Friday döneminde **SSD, HDD, Tablet, Ayakkabı ve Genel Kıyafet (Pantolon, Ceket, Hoodie, Tişört vb.)** kategorilerinde marka bağımsız olarak **gerçek indirim oranına** göre fırsat yakalayan ve **Telegram** üzerinden bildirim atan hibrit bir fiyat/fırsat takip sistemi.

## Goals, Non-Goals & Anti-Goals
- **Goals:**
  - MyDealz.de üzerinden seçili kategorilerde (Donanım & Kıyafet/Ayakkabı) topluluk onaylı ve gerçek indirim yüzdesi yüksek fırsatları yakalamak.
  - Geizhals.de üzerinden SSD, HDD ve Tablet kategorilerinde tüm Almanya satıcıları arasındaki gerçek fiyat düşüşlerini (Preisfall / Top-Preis-Drops) yakalamak.
  - **Kademeli Fiyat Düşüşü Takibi (Price-Drop Re-Alerting):** Bir ürün önce %20 indirime girdiğinde bildirim atılır; eğer aynı ürünün fiyatı daha sonra tekrar düşerse (örneğin %30 indirim olursa veya fiyatı 80€'dan 70€'ya inerse) **tekrar bildirim atılır** (sadece aynı fiyat veya daha yüksek fiyat tekrar bildirilmez).
  - Hem yerel bilgisayarda hem de GitHub Actions üzerinde ücretsiz 7/24 çalışabilmesi.
- **Non-Goals:**
  - Tüm e-ticaret sitelerini (Amazon, Zalando, MediaMarkt) tek tek doğrudan kazımak (Cloudflare/IP ban nedeniyle).
  - Otomatik satın alma (checkout bot).
- **Anti-Goals:**
  - Şişirilmiş UVP (liste fiyatı) üzerinden sahte indirim bildirimi göndermek.
  - Aynı ürünü aynı fiyattan tekrar tekrar spamlemek.

## Selected Approach (Approach 3 — Hybrid)
1. **MyDealz.de Radar (`src/mydealz.py`):**
   - MyDealz RSS ve arama sayfalarından donanım (`SSD`, `NVMe`, `HDD`, `Festplatte`, `Tablet`, `iPad`, `Galaxy Tab`) ve giyim/ayakkabı (`Schuhe`, `Sneaker`, `Hose`, `Jeans`, `Cargohose`, `Jogginghose`, `Jacke`, `Hoodie`, `Pullover`, `T-Shirt`, `Kleidung`, `Mode`) anahtar kelimelerini tarar.
   - Sıcaklık (derece) filtresi (varsayılan `>= 50°`), fiyat, önceki karşılaştırma fiyatı (PVG - Preisvergleich) ve indirim yüzdesini ayrıştırır.
2. **Geizhals.de Hardware Price-Drop Scanner (`src/geizhals.py`):**
   - SSD, HDD ve Tablet kategorilerinde fiyatları en çok düşen ürünleri ve mevcut en ucuz satıcı fiyatlarını çeker.
3. **Price-Aware State Store (`src/state.py`):**
   - Her ürün/fırsat ID'si için **en son bildirilen fiyatı (`last_price`) ve indirim oranını (`last_discount_pct`)** `data/seen_deals.json` içinde saklar.
   - Kural: Ürün daha önce hiç bildirilmediyse VEYA `yeni_fiyat < last_price` (ya da `yeni_indirim_yüzdesi > last_discount_pct`) ise **yeni bir bildirim ("🔥 EK İNDİRİM / FİYAT DAHA DA DÜŞTÜ!")** gönderir ve kaydı günceller.
4. **Telegram Notifier (`src/notifier.py`):**
   - Telegram Bot API üzerinden kategori etiketi, ürün başlığı, eski fiyat -> yeni fiyat, indirim yüzdesi (ve varsa önceki bildirime göre ek düşüş bilgisi) ile doğrudan link gönderir.

