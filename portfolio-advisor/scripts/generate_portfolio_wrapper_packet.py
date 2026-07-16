#!/usr/bin/env python3
"""Generate a Portfolio Weekly wrapper packet.

Inputs:
- <portfolio-dir>/transactions.csv (ledger, source of truth)
- <portfolio-dir>/price-snapshots.csv (single price source; agent fills this
  in via research, e.g. WebSearch, before running this script)
- <portfolio-dir>/recommendations.csv (prior recommendations, optional)
- --config portfolio-config.yaml (target allocation, risk limits, fx_rates)

This script does NOT make investment recommendations and does NOT estimate
missing prices or fx rates. Any held ticker without a price snapshot, or any
non-USD holding without a configured fx rate, is listed in the degraded
section at the top of the packet instead of being silently guessed.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import yaml

from build_holdings_json import build as build_holdings

# sleeve 顯示名稱 -> portfolio-config.yaml target_allocation 的鍵名
SLEEVE_CONFIG_KEYS = {
    "Core Long-term": "core_long_term",
    "AI Strategy": "ai_strategy",
    "Cash": "cash",
}


def q2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def d(value: str | int | float | Decimal | None) -> Decimal:
    if value is None or str(value).strip() == "":
        return Decimal("0")
    return Decimal(str(value))


def parse_decimal_strict(value) -> Decimal | None:
    """嚴格版本:空白或無法解析回傳 None,不像 d() 靜默回 0。

    用於「值缺席」與「值為 0」在語意上不能混為一談的欄位(price-snapshots.csv 的
    price、fx_rates 的匯率值)——這兩者只要空白/無法解析就必須視為缺資料,絕不能
    被 d() 悄悄轉成 Decimal("0") 再被當成合法數字計入總值。
    """
    s = str(value).strip() if value is not None else ""
    if not s:
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def latest_prices(portfolio_dir: Path) -> tuple[dict[str, dict], str]:
    """讀 price-snapshots.csv,回傳 {ticker: 最新一筆 snapshot row} 與整體最新 as_of_date。

    唯一價源:不讀任何外部資料庫,每個 ticker 若有多筆快照,取 as_of_date 最新者。
    """
    rows = read_csv(portfolio_dir / "price-snapshots.csv")
    prices: dict[str, dict] = {}
    as_of = ""
    for row in rows:
        ticker = (row.get("ticker") or "").strip().upper()
        if not ticker:
            continue
        row_date = row.get("as_of_date") or ""
        existing = prices.get(ticker)
        if existing is None or row_date >= (existing.get("as_of_date") or ""):
            prices[ticker] = row
        if row_date > as_of:
            as_of = row_date
    return prices, as_of or "unknown"


def pct(value: Decimal, total: Decimal) -> str:
    if total == 0:
        return "0.00%"
    return f"{q2(value / total * Decimal('100'))}%"


def compute_portfolio_state(portfolio_dir: Path, holdings_output: Path, config: dict) -> dict:
    """以 build_holdings_json 的帳本數學為唯一持倉來源,疊加價格與匯率。

    缺價格快照或缺匯率設定的持倉/現金一律列入 degraded,不估算補值,
    也不計入 sleeve 總值與權重。
    """
    base_currency = config.get("base_currency", "USD")
    # 空白/無法解析/為 0 的匯率一律不收進 fx_rates,查表時就會是 None(缺匯率),
    # 觸發 degraded——匯率為 0 從不合法,絕不能被當成「查到有效匯率 0」用來歸零總值。
    fx_rates = {}
    for k, v in (config.get("fx_rates") or {}).items():
        rate = parse_decimal_strict(v)
        if rate is not None and rate != 0:
            fx_rates[str(k).upper()] = rate

    state = build_holdings(portfolio_dir / "transactions.csv", holdings_output)
    prices, as_of = latest_prices(portfolio_dir)

    degraded: list[str] = []
    holdings: list[dict] = []
    sleeve_values: dict[str, Decimal] = defaultdict(Decimal)

    for h in state["holdings"]:
        ticker = h["ticker"]
        currency = h["currency"]
        qty = d(h["quantity"])
        avg_cost = d(h["avg_cost"])
        cost_basis = d(h["cost_basis"])

        price_row = prices.get(ticker)
        # price_row 存在不代表有價:price 欄位可能空白或無法解析,兩者都必須視為缺價,
        # 不能被 d() 悄悄轉成 0 再被當成真實市價計入市值。
        price_value = parse_decimal_strict(price_row.get("price")) if price_row else None
        fx_rate = Decimal("1") if currency == base_currency else fx_rates.get(f"{currency}{base_currency}")

        reasons = []
        if price_value is None:
            reasons.append("缺價格快照(price-snapshots.csv 無此 ticker 的資料列,或該列 price 欄位空白/無法解析)")
        if fx_rate is None:
            reasons.append(f"缺匯率設定(portfolio-config.yaml 的 fx_rates 無 {currency}{base_currency},或該匯率值空白/為 0)")

        if reasons:
            degraded.append(f"{ticker}: {'; '.join(reasons)}")
            holdings.append({
                "ticker": ticker,
                "market": h["market"],
                "asset_type": h["asset_type"],
                "sleeve": h["sleeve"],
                "quantity": qty,
                "avg_cost": avg_cost,
                "current_price": None,
                "currency": currency,
                "cost_basis": cost_basis,
                "market_value_native": None,
                "unrealized_pnl_native": None,
                "return_pct": None,
                "market_value_usd": None,
                "degraded": True,
            })
            continue

        current = price_value
        native_mv = qty * current
        pnl = native_mv - cost_basis
        ret = ((current - avg_cost) / avg_cost * Decimal("100")) if avg_cost else Decimal("0")
        usd_mv = native_mv * fx_rate
        sleeve_values[h["sleeve"]] += usd_mv
        holdings.append({
            "ticker": ticker,
            "market": h["market"],
            "asset_type": h["asset_type"],
            "sleeve": h["sleeve"],
            "quantity": qty,
            "avg_cost": avg_cost,
            "current_price": current,
            "currency": currency,
            "cost_basis": cost_basis,
            "market_value_native": native_mv,
            "unrealized_pnl_native": pnl,
            "return_pct": ret,
            "market_value_usd": usd_mv,
            "degraded": False,
        })

    cash_usd = Decimal("0")
    for c in state["cash"]:
        currency = c["currency"]
        amount = d(c["amount"])
        fx_rate = Decimal("1") if currency == base_currency else fx_rates.get(f"{currency}{base_currency}")
        if fx_rate is None:
            degraded.append(f"Cash({currency}): 缺匯率設定(portfolio-config.yaml 的 fx_rates 無 {currency}{base_currency})")
            continue
        cash_usd += amount * fx_rate

    sleeve_values["Cash"] += cash_usd
    total = sum(sleeve_values.values(), Decimal("0"))

    return {
        "holdings": holdings,
        "sleeves": dict(sleeve_values),
        "total": total,
        "as_of": as_of,
        "degraded": degraded,
        "base_currency": base_currency,
        "fx_rates": fx_rates,
    }


def recommendations_status(portfolio_dir: Path) -> str:
    rows = read_csv(portfolio_dir / "recommendations.csv")
    rows = [r for r in rows if any((v or "").strip() for v in r.values())]
    return "No prior recommendations yet — initial baseline week." if not rows else f"{len(rows)} prior recommendation row(s) found."


def build_targets(config: dict) -> dict[str, Decimal]:
    ta = config.get("target_allocation") or {}
    targets: dict[str, Decimal] = {}
    for sleeve, key in SLEEVE_CONFIG_KEYS.items():
        if key in ta:
            targets[sleeve] = d(ta[key])
    return targets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portfolio-dir", type=Path, default=Path(__file__).resolve().parents[1] / "portfolio")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    portfolio_dir = args.portfolio_dir
    config = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    target_allocation = config.get("target_allocation") or {}
    risk_limits = config.get("risk_limits") or {}
    targets = build_targets(config)
    rebalance_band = d(target_allocation.get("rebalance_band", "0.05"))

    state = compute_portfolio_state(portfolio_dir, portfolio_dir / "holdings.json", config)
    holdings = state["holdings"]
    sleeves = state["sleeves"]
    total = state["total"]
    as_of = state["as_of"]
    degraded = state["degraded"]
    base_currency = state["base_currency"]
    fx_rates = state["fx_rates"]

    tx_count = len([r for r in read_csv(portfolio_dir / "transactions.csv") if r.get("txn_id")])

    lines: list[str] = []
    lines.append(f"# Portfolio Weekly Wrapper Packet — {args.date}")
    lines.append("")

    lines.append("## 0. Degraded data")
    lines.append("")
    if degraded:
        lines.append("以下項目因缺價格快照或缺匯率設定,已從總值/權重計算中排除,數值一律不估算補值,請先處理:")
        lines.append("")
        for item in degraded:
            lines.append(f"- {item}")
    else:
        lines.append("無降級項目:所有持倉皆有價格快照,且非 USD 持倉皆有對應匯率設定。")
    lines.append("")

    lines.append("## 1. Scope and caveats")
    lines.append("")
    lines.append("- This is a wrapper packet, not the final investment report.")
    lines.append("- Final judgment belongs to the user; this packet only structures inputs for review.")
    lines.append(f"- Report as-of date: {as_of}")
    lines.append("- Price snapshot source: portfolio/price-snapshots.csv (single price source; no external database)")
    lines.append(f"- Ledger version / txn count: transactions.csv / {tx_count} confirmed transactions")
    lines.append("")

    lines.append("## 2. Portfolio state")
    lines.append("")
    lines.append("### 2.1 Allocation summary")
    lines.append("")
    lines.append("| Sleeve | USD ref value | Weight | Target | Drift | Status |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for sleeve in ["Core Long-term", "AI Strategy", "Crypto Satellite", "Cash"]:
        value = sleeves.get(sleeve, Decimal("0"))
        if sleeve in targets:
            target = targets[sleeve]
            drift = (value / total - target) if total else Decimal("0")
            status = "needs review" if abs(drift) >= rebalance_band else "within band"
            lines.append(f"| {sleeve} | {q2(value):,} | {pct(value, total)} | {q2(target * 100)}% | {q2(drift * 100)}% | {status} |")
        else:
            lines.append(f"| {sleeve} | {q2(value):,} | {pct(value, total)} | N/A | N/A | tracked only |")
    lines.append(f"| **Total** | **{q2(total):,}** | **100.00%** |  |  |  |")
    lines.append("")
    if degraded:
        lines.append("> Note: totals above exclude the degraded holdings/cash listed in section 0.")
        lines.append("")

    lines.append("### 2.2 Holdings table")
    lines.append("")
    lines.append("| Ticker | Market | Type | Sleeve | Qty | Avg cost | Current price | Currency | MV native | P&L native | Return | Weight | Notes |")
    lines.append("|---|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|")
    for h in holdings:
        if h["degraded"]:
            lines.append(
                f"| {h['ticker']} | {h['market']} | {h['asset_type']} | {h['sleeve']} | {h['quantity']} | {h['avg_cost']} | — | {h['currency']} | — | — | — | — | degraded — see section 0 |"
            )
            continue
        notes = "tracked only; no active crypto trading recommendations" if h["sleeve"] == "Crypto Satellite" else ""
        lines.append(
            f"| {h['ticker']} | {h['market']} | {h['asset_type']} | {h['sleeve']} | {h['quantity']} | {h['avg_cost']} | {h['current_price']} | {h['currency']} | {q2(h['market_value_native']):,} | {q2(h['unrealized_pnl_native']):,} | {q2(h['return_pct'])}% | {pct(h['market_value_usd'], total)} | {notes} |"
        )
    lines.append("")

    lines.append("### 2.3 Concentration / overlap checks")
    lines.append("")
    single_stock_max = d(risk_limits.get("single_stock_max_total_portfolio", "0"))
    single_etf_max = d(risk_limits.get("single_etf_max_total_portfolio", "0"))
    priced = [h for h in holdings if not h["degraded"]]

    def weight_of(h: dict) -> Decimal:
        return (h["market_value_usd"] / total) if total else Decimal("0")

    if single_stock_max > 0:
        violations = [h for h in priced if h["asset_type"] == "Stock" and weight_of(h) > single_stock_max]
        if violations:
            lines.append(f"- Single-stock cap violations (> {q2(single_stock_max * 100)}% of total): " + ", ".join(f"{h['ticker']} ({pct(h['market_value_usd'], total)})" for h in violations))
        else:
            lines.append(f"- Single-stock cap violations (> {q2(single_stock_max * 100)}% of total): none detected.")
    else:
        lines.append("- Single-stock cap violations: risk_limits.single_stock_max_total_portfolio not set in config.")
    if single_etf_max > 0:
        violations = [h for h in priced if h["asset_type"] == "ETF" and weight_of(h) > single_etf_max]
        if violations:
            lines.append(f"- ETF cap violations (> {q2(single_etf_max * 100)}% of total): " + ", ".join(f"{h['ticker']} ({pct(h['market_value_usd'], total)})" for h in violations))
        else:
            lines.append(f"- ETF cap violations (> {q2(single_etf_max * 100)}% of total): none detected.")
    else:
        lines.append("- ETF cap violations: risk_limits.single_etf_max_total_portfolio not set in config.")
    lines.append("- ETF look-through overlap issues: not computed in this wrapper; add ETF top-10 mapping manually if needed.")
    crypto_holdings = [h for h in holdings if h["asset_type"] == "Crypto"]
    if crypto_holdings:
        lines.append(f"- Crypto risk note: {', '.join(h['ticker'] for h in crypto_holdings)} tracked as Crypto Satellite exposure only; no active trading recommendation in v1.")
    else:
        lines.append("- Crypto risk note: no Crypto Satellite holdings.")
    lines.append("")

    lines.append("## 3. Long-term thesis context")
    lines.append("")
    lines.append("| Ticker | Prior thesis | Current evidence | Thesis status | Failure condition | Research needed |")
    lines.append("|---|---|---|---|---|---|")
    for h in holdings:
        if h["asset_type"] == "Crypto":
            thesis = "Crypto Satellite exposure; track risk/P&L only in v1"
            research = "No active crypto research required unless flagged"
        elif h["asset_type"] == "ETF":
            thesis = "ETF core allocation; verify theme/expense/top-10 overlap"
            research = "ETF issuer holdings, expense ratio, concentration, overlap"
        else:
            thesis = "Core long-term stock holding; verify thesis durability"
            research = "Latest earnings, guidance, valuation vs history, failure conditions"
        evidence = f"Ledger + price snapshot as of {as_of}" if not h["degraded"] else "Ledger only (price snapshot missing, see section 0)"
        lines.append(f"| {h['ticker']} | {thesis} | {evidence} | 待驗證 | Not yet defined in IPS per ticker | {research} |")
    lines.append("")

    lines.append("## 4. Fundamentals / valuation add-on")
    lines.append("")
    lines.append("This wrapper packet is generated from the ledger and price snapshots only; it does not include fundamentals research. Before treating any of this as a final report, add at least lightweight fundamentals/valuation/event checks for each holding below.")
    lines.append("")
    lines.append("| Ticker | Latest earnings / guidance | Valuation vs history | Revenue / margin trend | Balance-sheet / FCF notes | Source quality |")
    lines.append("|---|---|---|---|---|---|")
    for h in holdings:
        if h["asset_type"] == "Crypto":
            lines.append(f"| {h['ticker']} | N/A in v1 | N/A | N/A | N/A | Ledger-only / low priority |")
        else:
            lines.append(f"| {h['ticker']} | TODO | TODO | TODO | TODO | Needed before final report |")
    lines.append("")

    lines.append("## 5. Event calendar")
    lines.append("")
    lines.append("| Date | Event | Affected tickers | Why it matters | Action before event? |")
    lines.append("|---|---|---|---|---|")
    non_crypto = [h["ticker"] for h in holdings if h["asset_type"] != "Crypto"]
    if non_crypto:
        lines.append(f"| TODO | Earnings dates | {' / '.join(non_crypto)} | thesis and guidance updates | fill in after researching each ticker |")
    lines.append("| TODO | CPI / FOMC / macro releases | All growth-sensitive holdings | discount-rate risk | monitor |")
    etf_tickers = [h["ticker"] for h in holdings if h["asset_type"] == "ETF"]
    if etf_tickers:
        lines.append(f"| TODO | ETF distributions / rebalancing | {' / '.join(etf_tickers)} | holdings and income impact | monitor |")
    lines.append("")

    lines.append("## 6. Prior recommendations follow-up")
    lines.append("")
    lines.append(recommendations_status(portfolio_dir))
    lines.append("")

    lines.append("## 7. Decision inputs")
    lines.append("")
    lines.append("### 7.1 Suggested issues to decide")
    lines.append("")
    lines.append("- Review section 2.1 for any sleeve outside its rebalance band.")
    lines.append("- Review section 2.3 for any concentration cap violations.")
    lines.append("- Is any Core Long-term thesis weakened or broken?")
    lines.append("- Should any AI Strategy candidate be proposed this week, or should it wait for more research?")
    lines.append("- Does the degraded list in section 0 need a manual price/fx update before this packet is usable?")
    lines.append("")
    lines.append("### 7.2 Guardrails to enforce")
    lines.append("")
    ignore_drift = d(target_allocation.get("ignore_drift_below", "0.01"))
    turnover_warn = d(risk_limits.get("weekly_turnover_warning", "0.20"))
    cooldown_min = risk_limits.get("new_position_cooldown_weeks", "2")
    cooldown_max = risk_limits.get("new_position_cooldown_max_weeks", "4")
    lines.append(f"- Do not recommend action for <{q2(ignore_drift * 100)}% target drift.")
    lines.append(f"- Weekly turnover >{q2(turnover_warn * 100)}% must be red-flagged.")
    lines.append(f"- New positions should have {cooldown_min}–{cooldown_max} week cooldown unless thesis breaks.")
    lines.append("- Crypto Satellite: no active trading recommendation in v1.")
    lines.append("")

    lines.append("## 8. Source quality")
    lines.append("")
    lines.append("| Source | Type | Confidence | Issue / limitation |")
    lines.append("|---|---|---|---|")
    lines.append("| transactions.csv (ledger) | 一手/硬數據 | 高 | quantities/cost basis from ledger; must be broker-reconciled by the user |")
    lines.append("| price-snapshots.csv | 一手/硬數據 | 中 | manually captured prices; only as fresh as the last update |")
    used_fx = sorted({h["currency"] for h in holdings if h["currency"] != base_currency and not h["degraded"]})
    for cur in used_fx:
        rate = fx_rates.get(f"{cur}{base_currency}")
        lines.append(f"| {cur}/{base_currency} reference rate ({rate}) | 二手/訊號 | 中 | reference FX from portfolio-config.yaml; broker FX may differ |")
    lines.append("")

    lines.append("## 9. Files and reproducibility")
    lines.append("")
    lines.append(f"- Ledger: `{portfolio_dir / 'transactions.csv'}`")
    lines.append(f"- Holdings state: `{portfolio_dir / 'holdings.json'}`")
    lines.append(f"- Price snapshots: `{portfolio_dir / 'price-snapshots.csv'}`")
    lines.append(f"- Config: `{args.config}`")
    lines.append("- This packet generated by: `scripts/generate_portfolio_wrapper_packet.py`")
    lines.append("")

    lines.append("## 10. Readiness")
    lines.append("")
    lines.append("This packet is suitable for a first baseline discussion, but fundamentals/event-calendar fields are still TODO. Use it to decide whether more research is needed before treating anything here as actionable.")
    lines.append("")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
