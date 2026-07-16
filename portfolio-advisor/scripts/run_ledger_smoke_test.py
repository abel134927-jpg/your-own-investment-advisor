#!/usr/bin/env python3
"""Run Portfolio Weekly v1 ledger smoke test.

Copies tests/fixtures/ledger-smoke-transactions.csv into a scratch
tests/output/ledger-smoke/ directory (as transactions.csv) and runs
validate_portfolio_ledger.py / build_holdings_json.py against it via
--portfolio-dir. Does not touch a real portfolio/ directory.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "ledger-smoke-transactions.csv"
WORKDIR = ROOT / "tests" / "output" / "ledger-smoke"


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def assert_close(name: str, got: float, expected: float, tol: float = 1e-6) -> None:
    if abs(got - expected) > tol:
        raise AssertionError(f"{name}: expected {expected}, got {got}")


def main() -> int:
    if WORKDIR.exists():
        shutil.rmtree(WORKDIR)
    WORKDIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FIXTURE, WORKDIR / "transactions.csv")

    run([sys.executable, "scripts/validate_portfolio_ledger.py", "--portfolio-dir", str(WORKDIR)])
    run([sys.executable, "scripts/build_holdings_json.py", "--portfolio-dir", str(WORKDIR)])

    output = WORKDIR / "holdings.json"
    data = json.loads(output.read_text(encoding="utf-8"))
    holdings = data["holdings"]
    cash = data["cash"]
    warnings = data.get("warnings", [])

    if len(holdings) != 1:
        raise AssertionError(f"expected exactly 1 holding after reversal, got {len(holdings)}: {holdings}")
    nvda = holdings[0]
    if nvda["ticker"] != "NVDA":
        raise AssertionError(f"expected NVDA holding, got {nvda}")

    # Expected sequence:
    # deposit +10000
    # buy 10 * 100 + 1 fee => cash -1001, cost 1001, qty 10
    # dividend +10, tax withholding -3
    # split 2-for-1 => qty 20, cost 1001, avg 50.05
    # AMD buy is reversed/excluded
    # sell 5 * 120 - 1 fee => cash +599; removes avg cost 50.05 * 5 = 250.25
    # final cash = 10000 - 1001 + 10 - 3 + 599 = 9605
    # final NVDA qty = 15, cost_basis = 750.75, avg_cost = 50.05
    assert_close("NVDA quantity", float(nvda["quantity"]), 15.0)
    assert_close("NVDA cost_basis", float(nvda["cost_basis"]), 750.75)
    assert_close("NVDA avg_cost", float(nvda["avg_cost"]), 50.05)

    if len(cash) != 1 or cash[0]["currency"] != "USD":
        raise AssertionError(f"expected one USD cash row, got {cash}")
    assert_close("USD cash", float(cash[0]["amount"]), 9605.0)

    if not any("txn_20260713_AMD_buy_bad was reversed" in w for w in warnings):
        raise AssertionError(f"expected reversed AMD warning, got {warnings}")

    print("SMOKE TEST OK: deposit/buy/dividend/tax/split/reversal/sell ledger math passed.")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
