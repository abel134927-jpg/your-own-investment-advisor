#!/usr/bin/env python3
"""Validate Portfolio Weekly v1 ledger files.

Scope:
- Validate transactions.csv header and required fields.
- Validate action enum.
- Detect duplicate txn_id.
- Detect likely duplicate trades.
- Validate confirmed_by_user is true/false.

This script does not fetch prices, compute TWR, or integrate external market data.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORTFOLIO_DIR = ROOT / "portfolio"

REQUIRED_COLUMNS = [
    "txn_id",
    "date",
    "action",
    "ticker",
    "market",
    "asset_type",
    "sleeve",
    "quantity",
    "price",
    "currency",
    "fees",
    "tax",
    "source",
    "confirmed_by_user",
    "notes",
    "reversal_of",
]

ACTIONS = {
    "buy",
    "sell",
    "deposit",
    "withdraw",
    "dividend",
    "tax_withholding",
    "fee",
    "split",
    "reverse_split",
    "reversal",
    "transfer_in",
    "transfer_out",
    "fx",
}
SLEEVES = {"Core Long-term", "AI Strategy", "Cash", "Crypto Satellite"}
CURRENCIES = {"USD", "TWD", "HKD"}
ASSET_TYPES = {"Stock", "ETF", "Cash", "Crypto"}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)


def warn(msg: str) -> None:
    print(f"WARNING: {msg}")


def validate(portfolio_dir: Path) -> int:
    transactions = portfolio_dir / "transactions.csv"
    if not transactions.exists():
        fail(f"Missing {transactions}")

    with transactions.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != REQUIRED_COLUMNS:
            fail(f"transactions.csv header mismatch. Expected {REQUIRED_COLUMNS}, got {reader.fieldnames}")
        txn_ids: set[str] = set()
        duplicate_keys: dict[tuple[str, str, str, str, str, str], str] = {}
        rows = list(reader)

    errors: list[str] = []

    for i, row in enumerate(rows, start=2):
        if not any((v or "").strip() for v in row.values()):
            continue

        txn_id = row["txn_id"].strip()
        action = row["action"].strip()
        ticker = row["ticker"].strip().upper()
        asset_type = row["asset_type"].strip()
        sleeve = row["sleeve"].strip()
        currency = row["currency"].strip()
        confirmed = row["confirmed_by_user"].strip().lower()

        if not txn_id:
            errors.append(f"line {i}: missing txn_id")
        elif txn_id in txn_ids:
            errors.append(f"line {i}: duplicate txn_id {txn_id}")
        else:
            txn_ids.add(txn_id)

        if action not in ACTIONS:
            errors.append(f"line {i}: invalid action {action}")
        if asset_type and asset_type not in ASSET_TYPES:
            errors.append(f"line {i}: invalid asset_type {asset_type}")
        if sleeve and sleeve not in SLEEVES:
            errors.append(f"line {i}: invalid sleeve {sleeve}")
        if currency and currency not in CURRENCIES:
            errors.append(f"line {i}: invalid currency {currency}")
        if confirmed not in {"true", "false"}:
            errors.append(f"line {i}: confirmed_by_user must be true/false")
        if action in {"buy", "sell", "transfer_in", "transfer_out"}:
            for col in ["ticker", "market", "quantity", "price"]:
                if not row[col].strip():
                    errors.append(f"line {i}: action {action} requires {col}")
        if action in {"deposit", "withdraw"} and not (row["price"].strip() or row["quantity"].strip()):
            errors.append(f"line {i}: action {action} requires amount in price or quantity")
        if action == "reversal" and not row["reversal_of"].strip():
            errors.append(f"line {i}: reversal requires reversal_of")

        duplicate_key = (
            row["date"].strip(),
            action,
            ticker,
            row["quantity"].strip(),
            row["price"].strip(),
            sleeve,
        )
        if action in {"buy", "sell"} and all(duplicate_key):
            if duplicate_key in duplicate_keys:
                warn(f"line {i}: likely duplicate trade with {duplicate_keys[duplicate_key]}")
            else:
                duplicate_keys[duplicate_key] = f"line {i} / {txn_id}"

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    print(f"OK: validated {len(rows)} transaction row(s); {len(txn_ids)} txn_id(s). Source={transactions}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portfolio-dir", type=Path, default=DEFAULT_PORTFOLIO_DIR)
    args = parser.parse_args()
    return validate(args.portfolio_dir)


if __name__ == "__main__":
    raise SystemExit(main())
