# Portfolio Advisor Scripts

Portfolio Weekly v1 腳本:帳本(ledger)管理、wrapper packet 產生、報告渲染。

## Scripts

- `validate_portfolio_ledger.py` — validates CSV headers, action enum, append-only assumptions, duplicate candidates, and required fields. `--portfolio-dir`(預設 `portfolio/`),讀 `<portfolio-dir>/transactions.csv`。
- `build_holdings_json.py` — generates `<portfolio-dir>/holdings.json` from `<portfolio-dir>/transactions.csv`。`--portfolio-dir`(預設 `portfolio/`)。
- `run_ledger_smoke_test.py` — 以 `tests/fixtures/ledger-smoke-transactions.csv` 驗證上述兩支腳本的帳本數學(deposit/buy/dividend/tax/split/reversal/sell),不觸碰真實 `portfolio/` 目錄。
- `generate_portfolio_wrapper_packet.py` — 讀 `<portfolio-dir>/transactions.csv` + `<portfolio-dir>/price-snapshots.csv` + `--config`(portfolio-config.yaml)產生 wrapper packet(非最終投資報告)。`--portfolio-dir --config --out`。價格與匯率缺失時列入 packet 開頭的 degraded 清單,不估算補值。
- `render_portfolio_report.py` — 將 report-data.json 注入 `templates/portfolio-dashboard.template.html`,輸出 HTML,並在偵測到 Chrome/Edge 時額外輸出 A4 PDF(`--data --out-pdf [--out-html]`)。找不到瀏覽器時仍輸出 HTML 並印警告,不中斷。

## Phase 1 limitations

- No broker integration.
- No live price fetching(價格需由使用者/agent 手動填入 `price-snapshots.csv`)。
- Simplified holdings aggregation only.
- TWR is not implemented in v1 skeleton; schema reserves future support.
