#!/usr/bin/env python3
"""Build holdings.json from transactions.csv.

Phase 1/2 scope:
- Supports buy/sell/deposit/withdraw/fee/dividend/tax_withholding/reversal/split.
- Does not fetch current prices.
- Does not compute TWR.
- Uses transactions.csv as source of truth.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORTFOLIO_DIR = ROOT / "portfolio"


def fnum(value: str | None) -> float:
    try:
        return float(value) if str(value or "").strip() else 0.0
    except ValueError:
        return 0.0


def build(transactions: Path, output_path: Path) -> dict:
    positions: dict[tuple[str, str, str, str], dict] = {}
    cash = defaultdict(float)
    reversed_txns: set[str] = set()

    with transactions.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    # First pass: collect reversals.
    for row in rows:
        if row.get("action") == "reversal" and row.get("reversal_of"):
            reversed_txns.add(row["reversal_of"].strip())

    processed = 0
    warnings: list[str] = []

    for row in rows:
        if not any((v or "").strip() for v in row.values()):
            continue
        txn_id = row["txn_id"].strip()
        if txn_id in reversed_txns:
            warnings.append(f"transaction {txn_id} was reversed and excluded")
            continue
        if row.get("confirmed_by_user", "").lower() != "true":
            warnings.append(f"transaction {txn_id or '<missing>'} not confirmed; excluded")
            continue

        action = row["action"].strip()
        ticker = row["ticker"].strip().upper()
        market = row["market"].strip()
        asset_type = row["asset_type"].strip()
        sleeve = row["sleeve"].strip()
        currency = row["currency"].strip() or "USD"
        qty = fnum(row["quantity"])
        price = fnum(row["price"])
        fees = fnum(row["fees"])
        tax = fnum(row["tax"])

        if action == "deposit":
            cash[currency] += price or qty
        elif action == "withdraw":
            cash[currency] -= price or qty
        elif action == "fee":
            cash[currency] -= fees or price or qty
        elif action == "dividend":
            cash[currency] += price or qty
        elif action == "tax_withholding":
            cash[currency] -= tax or price or qty
        elif action in {"buy", "transfer_in"}:
            key = (ticker, market, asset_type, sleeve)
            pos = positions.setdefault(key, {"quantity": 0.0, "cost_basis": 0.0, "currency": currency})
            pos["cost_basis"] += qty * price + fees + tax
            pos["quantity"] += qty
            if action == "buy":
                cash[currency] -= qty * price + fees + tax
        elif action in {"sell", "transfer_out"}:
            key = (ticker, market, asset_type, sleeve)
            pos = positions.setdefault(key, {"quantity": 0.0, "cost_basis": 0.0, "currency": currency})
            avg_cost = pos["cost_basis"] / pos["quantity"] if pos["quantity"] else 0.0
            sell_qty = min(qty, pos["quantity"]) if pos["quantity"] > 0 else qty
            if qty > pos["quantity"] and pos["quantity"] >= 0:
                warnings.append(f"transaction {txn_id}: sell/transfer_out quantity exceeds current position")
            cost_removed = avg_cost * sell_qty
            pos["quantity"] -= qty
            pos["cost_basis"] -= cost_removed
            if action == "sell":
                cash[currency] += qty * price - fees - tax
        elif action == "split":
            key = (ticker, market, asset_type, sleeve)
            pos = positions.setdefault(key, {"quantity": 0.0, "cost_basis": 0.0, "currency": currency})
            # For split, use quantity as ratio multiplier, e.g. 2-for-1 => quantity=2
            if qty > 0:
                pos["quantity"] *= qty
        elif action == "reverse_split":
            key = (ticker, market, asset_type, sleeve)
            pos = positions.setdefault(key, {"quantity": 0.0, "cost_basis": 0.0, "currency": currency})
            if qty > 0:
                pos["quantity"] /= qty
        elif action in {"reversal", "fx"}:
            # Reversal handled by first pass. FX reserved for future.
            pass
        else:
            warnings.append(f"unsupported action {action} in {txn_id}")
        processed += 1

    holdings = []
    for (ticker, market, asset_type, sleeve), pos in sorted(positions.items()):
        if abs(pos["quantity"]) < 1e-12:
            continue
        avg_cost = pos["cost_basis"] / pos["quantity"] if pos["quantity"] else 0.0
        holdings.append({
            "ticker": ticker,
            "market": market,
            "asset_type": asset_type,
            "sleeve": sleeve,
            "quantity": round(pos["quantity"], 8),
            "avg_cost": round(avg_cost, 6),
            "cost_basis": round(pos["cost_basis"], 2),
            "currency": pos["currency"],
            "current_price": None,
            "market_value": None,
            "unrealized_pnl": None,
            "weight": None,
        })

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_of_truth": str(transactions),
        "base_currency": "USD",
        "reference_currency": "TWD",
        "status": "generated",
        "phase": "v1-ledger-skeleton",
        "processed_transactions": processed,
        "holdings": holdings,
        "cash": [{"currency": k, "amount": round(v, 2)} for k, v in sorted(cash.items())],
        "warnings": warnings,
        "limitations": [
            "No live current_price fetching in Phase 1/2.",
            "No TWR calculation in Phase 1/2.",
            "Simplified cost-basis logic; broker reconciliation required before production.",
            "fx action is recorded only and does not affect ledger math (v1); use withdraw+deposit for multi-currency cash movements."
        ]
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portfolio-dir", type=Path, default=DEFAULT_PORTFOLIO_DIR)
    args = parser.parse_args()
    transactions = args.portfolio_dir / "transactions.csv"
    output = args.portfolio_dir / "holdings.json"
    build(transactions, output)
    print(f"OK: wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
