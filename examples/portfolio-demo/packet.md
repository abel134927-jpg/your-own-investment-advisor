# Portfolio Weekly Wrapper Packet（示範資料）— 2026-07-16

> ⚠️ （示範資料）本檔案由虛構持倉 fixtures（`examples/fixtures/demo-transactions.csv`、
> `demo-price-snapshots.csv`、`demo-portfolio-config.yaml`）生成，僅供展示 wrapper packet
> 格式，非真實投資組合，請勿當作真實持倉快照使用。

## 0. Degraded data

無降級項目:所有持倉皆有價格快照,且非 USD 持倉皆有對應匯率設定。

## 1. Scope and caveats

- This is a wrapper packet, not the final investment report.
- Final judgment belongs to the user; this packet only structures inputs for review.
- Report as-of date: 2026-07-15
- Price snapshot source: portfolio/price-snapshots.csv (single price source; no external database)
- Ledger version / txn count: transactions.csv / 8 confirmed transactions

## 2. Portfolio state

### 2.1 Allocation summary

| Sleeve | USD ref value | Weight | Target | Drift | Status |
|---|---:|---:|---:|---:|---|
| Core Long-term | 34,050.00 | 33.46% | 65.00% | -31.54% | needs review |
| AI Strategy | 16,125.00 | 15.84% | 30.00% | -14.16% | needs review |
| Crypto Satellite | 0.00 | 0.00% | N/A | N/A | tracked only |
| Cash | 51,602.80 | 50.70% | 5.00% | 45.70% | needs review |
| **Total** | **101,777.80** | **100.00%** |  |  |  |

### 2.2 Holdings table

| Ticker | Market | Type | Sleeve | Qty | Avg cost | Current price | Currency | MV native | P&L native | Return | Weight | Notes |
|---|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| AVGO | US | Stock | AI Strategy | 10.0 | 250.0 | 265 | USD | 2,650.00 | 150.00 | 6.00% | 2.60% |  |
| NVDA | US | Stock | AI Strategy | 40.0 | 155.0 | 165 | USD | 6,600.00 | 400.00 | 6.45% | 6.48% |  |
| QQQ | US | ETF | Core Long-term | 30.0 | 480.0 | 495 | USD | 14,850.00 | 450.00 | 3.13% | 14.59% |  |
| SMH | US | ETF | AI Strategy | 25.0 | 260.0 | 275 | USD | 6,875.00 | 375.00 | 5.77% | 6.75% |  |
| VOO | US | ETF | Core Long-term | 40.0 | 470.0 | 480 | USD | 19,200.00 | 400.00 | 2.13% | 18.86% |  |

### 2.3 Concentration / overlap checks

- Single-stock cap violations (> 8.00% of total): none detected.
- ETF cap violations (> 20.00% of total): none detected.
- ETF look-through overlap issues: not computed in this wrapper; add ETF top-10 mapping manually if needed.
- Crypto risk note: no Crypto Satellite holdings.

## 3. Long-term thesis context

| Ticker | Prior thesis | Current evidence | Thesis status | Failure condition | Research needed |
|---|---|---|---|---|---|
| AVGO | Core long-term stock holding; verify thesis durability | Ledger + price snapshot as of 2026-07-15 | 待驗證 | Not yet defined in IPS per ticker | Latest earnings, guidance, valuation vs history, failure conditions |
| NVDA | Core long-term stock holding; verify thesis durability | Ledger + price snapshot as of 2026-07-15 | 待驗證 | Not yet defined in IPS per ticker | Latest earnings, guidance, valuation vs history, failure conditions |
| QQQ | ETF core allocation; verify theme/expense/top-10 overlap | Ledger + price snapshot as of 2026-07-15 | 待驗證 | Not yet defined in IPS per ticker | ETF issuer holdings, expense ratio, concentration, overlap |
| SMH | ETF core allocation; verify theme/expense/top-10 overlap | Ledger + price snapshot as of 2026-07-15 | 待驗證 | Not yet defined in IPS per ticker | ETF issuer holdings, expense ratio, concentration, overlap |
| VOO | ETF core allocation; verify theme/expense/top-10 overlap | Ledger + price snapshot as of 2026-07-15 | 待驗證 | Not yet defined in IPS per ticker | ETF issuer holdings, expense ratio, concentration, overlap |

## 4. Fundamentals / valuation add-on

This wrapper packet is generated from the ledger and price snapshots only; it does not include fundamentals research. Before treating any of this as a final report, add at least lightweight fundamentals/valuation/event checks for each holding below.

| Ticker | Latest earnings / guidance | Valuation vs history | Revenue / margin trend | Balance-sheet / FCF notes | Source quality |
|---|---|---|---|---|---|
| AVGO | TODO | TODO | TODO | TODO | Needed before final report |
| NVDA | TODO | TODO | TODO | TODO | Needed before final report |
| QQQ | TODO | TODO | TODO | TODO | Needed before final report |
| SMH | TODO | TODO | TODO | TODO | Needed before final report |
| VOO | TODO | TODO | TODO | TODO | Needed before final report |

## 5. Event calendar

| Date | Event | Affected tickers | Why it matters | Action before event? |
|---|---|---|---|---|
| TODO | Earnings dates | AVGO / NVDA / QQQ / SMH / VOO | thesis and guidance updates | fill in after researching each ticker |
| TODO | CPI / FOMC / macro releases | All growth-sensitive holdings | discount-rate risk | monitor |
| TODO | ETF distributions / rebalancing | QQQ / SMH / VOO | holdings and income impact | monitor |

## 6. Prior recommendations follow-up

No prior recommendations yet — initial baseline week.

## 7. Decision inputs

### 7.1 Suggested issues to decide

- Review section 2.1 for any sleeve outside its rebalance band.
- Review section 2.3 for any concentration cap violations.
- Is any Core Long-term thesis weakened or broken?
- Should any AI Strategy candidate be proposed this week, or should it wait for more research?
- Does the degraded list in section 0 need a manual price/fx update before this packet is usable?

### 7.2 Guardrails to enforce

- Do not recommend action for <1.00% target drift.
- Weekly turnover >20.00% must be red-flagged.
- New positions should have 2–4 week cooldown unless thesis breaks.
- Crypto Satellite: no active trading recommendation in v1.

## 8. Source quality

| Source | Type | Confidence | Issue / limitation |
|---|---|---|---|
| transactions.csv (ledger) | 一手/硬數據 | 高 | quantities/cost basis from ledger; must be broker-reconciled by the user |
| price-snapshots.csv | 一手/硬數據 | 中 | manually captured prices; only as fresh as the last update |

## 9. Files and reproducibility

- Ledger: `..\..\examples\portfolio-demo\ledger-staging\transactions.csv`
- Holdings state: `..\..\examples\portfolio-demo\ledger-staging\holdings.json`
- Price snapshots: `..\..\examples\portfolio-demo\ledger-staging\price-snapshots.csv`
- Config: `..\..\examples\fixtures\demo-portfolio-config.yaml`
- This packet generated by: `scripts/generate_portfolio_wrapper_packet.py`

## 10. Readiness

This packet is suitable for a first baseline discussion, but fundamentals/event-calendar fields are still TODO. Use it to decide whether more research is needed before treating anything here as actionable.
