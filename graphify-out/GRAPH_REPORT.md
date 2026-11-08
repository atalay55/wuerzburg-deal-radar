# Graph Report - wuerzburg-deal-radar  (2026-11-08)

## Corpus Check
- 16 files · ~4,934 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .bat 1)

## Summary
- 116 nodes · 263 edges · 8 communities
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `582f4667`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- mydealz.py
- steps
- Deal
- main.py
- DealStateStore
- Review Focus
- Hızlı Kurulum ve Çalıştırma
- Würzburg Black Friday Deal Radar — Design Spec

## God Nodes (most connected - your core abstractions)
1. `Deal` - 21 edges
2. `DealStateStore` - 17 edges
3. `run_once()` - 14 edges
4. `parse_mydealz_rss()` - 14 edges
5. `EvaluationResult` - 10 edges
6. `parse_german_price()` - 9 edges
7. `parse_geizhals_price_drops()` - 8 edges
8. `format_telegram_message()` - 8 edges
9. `compute_discount_pct()` - 8 edges
10. `ensure_telegram_connected()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Task 2: German Price/Discount Parser & MyDealz Scanner (Electronics + Fashion/Pants)` --references--> `Deal`  [INFERRED]
  docs/superpowers/plans/2026-11-08-wuerzburg-deal-radar.md → src/models.py
- `Task 3: Geizhals.de Hardware Price-Drop Scanner & Telegram Notifier + Runner` --references--> `Deal`  [INFERRED]
  docs/superpowers/plans/2026-11-08-wuerzburg-deal-radar.md → src/models.py
- `Task 3: Geizhals.de Hardware Price-Drop Scanner & Telegram Notifier + Runner` --references--> `EvaluationResult`  [INFERRED]
  docs/superpowers/plans/2026-11-08-wuerzburg-deal-radar.md → src/state.py
- `Task 1: Data Models & Price-Aware State Store (Re-Alert on Further Drops)` --references--> `DealStateStore`  [INFERRED]
  docs/superpowers/plans/2026-11-08-wuerzburg-deal-radar.md → src/state.py
- `Task 1: Data Models & Price-Aware State Store (Re-Alert on Further Drops)` --references--> `Deal`  [INFERRED]
  docs/superpowers/plans/2026-11-08-wuerzburg-deal-radar.md → src/models.py

## Import Cycles
- None detected.

## Communities (8 total, 0 thin omitted)

### Community 0 - "mydealz.py"
Cohesion: 0.19
Nodes (10): parse_geizhals_price_drops(), _extract_temperature(), _has_expired_text(), _is_too_old(), parse_mydealz_rss(), classify_keyword(), compute_discount_pct(), extract_current_and_old_price() (+2 more)

### Community 1 - "steps"
Cohesion: 0.09
Nodes (21): env, FORCE_JAVASCRIPT_ACTIONS_TO_NODE24, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, jobs, scan-deals, name, on (+13 more)

### Community 2 - "Deal"
Cohesion: 0.27
Nodes (6): Task 1: Data Models & Price-Aware State Store (Re-Alert on Further Drops), Deal, extract_chat_id_from_updates(), format_telegram_message(), EvaluationResult, TestNotifierAndGeizhals

### Community 3 - "main.py"
Cohesion: 0.25
Nodes (10): fetch_geizhals_deals(), ensure_telegram_connected(), load_config(), main(), run_once(), save_config(), fetch_mydealz_deals(), is_deal_expired_on_page() (+2 more)

### Community 4 - "DealStateStore"
Cohesion: 0.30
Nodes (4): Task 3: Geizhals.de Hardware Price-Drop Scanner & Telegram Notifier + Runner, DealStateStore, make_deal(), TestDealStateStore

### Community 5 - "Review Focus"
Cohesion: 0.40
Nodes (4): Global Constraints, Review Focus, Task 2: German Price/Discount Parser & MyDealz Scanner (Electronics + Fashion/Pants), Würzburg Black Friday Deal Radar Implementation Plan

### Community 6 - "Hızlı Kurulum ve Çalıştırma"
Cohesion: 0.33
Nodes (5): 1. Telegram Bot Token ve Chat ID Alma (2 Dakika), 2. Bilgisayarında Çalıştırma, Hızlı Kurulum ve Çalıştırma, Würzburg Black Friday Deal Radar 🇩🇪🎯, Özellikler

### Community 7 - "Würzburg Black Friday Deal Radar — Design Spec"
Cohesion: 0.40
Nodes (4): Goals, Non-Goals & Anti-Goals, Intent & Why, Selected Approach (Approach 3 — Hybrid), Würzburg Black Friday Deal Radar — Design Spec

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Deal` connect `Deal` to `mydealz.py`, `main.py`, `DealStateStore`, `Review Focus`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Deal` (e.g. with `Task 1: Data Models & Price-Aware State Store (Re-Alert on Further Drops)` and `Task 2: German Price/Discount Parser & MyDealz Scanner (Electronics + Fashion/Pants)`) actually correct?**
  _`Deal` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `steps` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Why does `DealStateStore` connect `DealStateStore` to `Deal`, `main.py`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `DealStateStore` (e.g. with `Task 1: Data Models & Price-Aware State Store (Re-Alert on Further Drops)` and `Task 3: Geizhals.de Hardware Price-Drop Scanner & Telegram Notifier + Runner`) actually correct?**
  _`DealStateStore` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Why does `parse_mydealz_rss()` connect `mydealz.py` to `Deal`, `main.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `run_once()` (e.g. with `.evaluate_and_record()` and `.save()`) actually correct?**
  _`run_once()` has 2 INFERRED edges - model-reasoned connections that need verification._