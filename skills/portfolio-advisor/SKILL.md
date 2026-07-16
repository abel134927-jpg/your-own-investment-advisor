---
name: portfolio-advisor
description: Use when 用戶要求生成本週投資組合週報、初始化持倉建檔、或回報交易記帳
---

# portfolio-advisor — 投資組合週報 + 記帳

兩條流程共用同一份帳本：① 每週顧問流程（四段角色，研究員 → 主筆草稿 → 紅隊 → 主筆定稿），產出 Portfolio Weekly 報告；② 記帳流程（`ledger-entry.md`），隨時觸發，把使用者口頭報的交易安全寫進帳本。

## ① 觸發語範例

- 「跑本週 Portfolio Weekly」「幫我看一下這週組合狀況」
- 「我買了 X」「我賣了 X」「幫我記一筆交易」「我入金了 10000 美金」
- 「初始化我的投資組合」「第一次用，帶我設定持倉」

## ② 首次使用 onboarding

**Step 1：環境自檢**

```bash
python --version          # 需 >= 3.10（若指令不存在，改試 python3 --version）
pip install -r requirements.txt   # 安裝 pillow + pyyaml
```

檢查瀏覽器（用於渲染 PDF；找不到不是錯誤，只是會自動降級成只出 HTML）：

```bash
python -c "from common import render_env; b=render_env.find_browser(); print('Chrome/Edge:', b or 'NOT FOUND -> 正常降級，只出 HTML')"
```

**Step 2：smoke test（確認渲染管線可執行）**

```bash
python portfolio-advisor/scripts/render_portfolio_report.py --data examples/fixtures/portfolio-report-data.json --out-pdf outputs/_smoke/portfolio-report-data.pdf
```

應 exit code 0。`outputs/_smoke/` 只是暫時檢查用，可事後刪除（`outputs/` 已在 `.gitignore`）。若沒有瀏覽器，只會產出對應的 `.html` 沒有 `.pdf`，同樣算通過。

**Step 3：持倉與 investment-policy 訪談**

真實帳本目錄 `portfolio-advisor/portfolio/` 不會被提交到版本控制（`.gitignore` 已排除），第一次使用需要從範本複製一份：

```bash
cp -r portfolio-advisor/portfolio.example portfolio-advisor/portfolio
```

複製之後，依序帶使用者填寫：

1. **交易紀錄**：`portfolio-advisor/portfolio/transactions.csv` 裡的範例列先清空，改用下方「ledger-entry」流程逐筆把使用者現有持倉（起始入金 + 各筆買入）補進去，或請使用者提供一份完整的交易明細一次性訪談建檔。
2. **`portfolio-config.yaml`**：訪談 `target_allocation`（各 sleeve 目標權重、再平衡帶寬）、`risk_limits`（單一標的上限、週轉率警戒、現金下限等）、`benchmarks`（整體與各 sleeve 對照的基準指數）、`fx_rates`（非美元資產的參考匯率）。
3. **`investment-policy.md`**：逐節訪談並填掉全部 `<請填寫>`——授權邊界（哪些倉位使用者自主、哪些交給顧問建議）、投資目標、投資期限、風險偏好與禁用工具清單、賣出／減碼門檻、benchmarks、現金與出入金規則、合規與責任邊界。這份文件是每次顧問流程的最高優先規則，沒填的欄位會被顧問當成最保守假設處理。

訪談完成後才進入下方「③ 執行順序」跑第一期；第一期沒有 `recommendations.csv` 歷史紀錄，主筆會視為首次運行處理。

## ③ 執行順序與檔案交接

**每週顧問流程**（四段，以檔案交接，讀取並遵循對應 prompt 檔案完整內容執行）：

| 段落 | Prompt | 讀 | 寫 | 完成條件 |
|---|---|---|---|---|
| 1. 研究員 | `portfolio-advisor/prompts/01-packet.md` | `portfolio-advisor/portfolio/` 下帳本與設定檔 | `outputs/portfolio/<date>/packet.md`（副作用：更新 `price-snapshots.csv`、重建 `holdings.json`） | 每檔持倉皆已查價或標 degraded，`packet.md` 無殘留 `TODO` |
| 2. 主筆草稿 | `portfolio-advisor/prompts/02-draft.md` | `packet.md` + `recommendations.csv`/`transactions.csv`（只讀） | `draft.md` | Core 持倉五態判定齊全，策略倉建議每條附最強反方論證 |
| 3. 紅隊 | `portfolio-advisor/prompts/03-redteam.md` | `packet.md` + `draft.md` + `portfolio-config.yaml` + `investment-policy.md` | `redteam.md` | 見下方④，**必須在隔離的 subagent 執行** |
| 4. 主筆定稿 | `portfolio-advisor/prompts/04-final.md` | `draft.md` + `redteam.md`（若無則走失敗容錯） + `packet.md` | `report-data.json` + `final.md` + `summary-short.md` + 渲染產物 + append `recommendations.csv` | 逐條 `R#` 已回應，渲染腳本已執行過 |

`<date>` 為本次執行當天日期（`YYYY-MM-DD`），資料夾在 `outputs/portfolio/<date>/` 下，不存在就自行建立。

**記帳流程**（隨時觸發，不是上面四段的一部分）：讀取並遵循 `portfolio-advisor/prompts/ledger-entry.md`。流程固定為：自然語言報單 → 解析成 pending 交易並展示摘要表 → **等使用者在下一則訊息明確確認**（同一則訊息裡順帶講的確認語句不算數）→ 確認後才 append 到 `transactions.csv` 並重建 `holdings.json`。未經確認絕不寫入是硬邊界，模糊輸入要追問，不可用假設值填補。

## ④ 紅隊必須隔離執行 —— 不得餵主上下文

`portfolio-advisor/prompts/03-redteam.md` 檔頭已明講：紅隊必須在**沒看過草稿、也沒看過主對話推理過程**的狀態下，先形成自己獨立的空頭觀點，否則會被草稿措辭錨定、攻擊失去力道。

執行方式：**用 Task 工具（或你這個 agent 提供的等效 subagent／背景任務功能）開一個全新的 subagent**，subagent 的初始 prompt 只包含：

1. `portfolio-advisor/prompts/03-redteam.md` 的完整內容
2. 本次執行的檔案路徑：`outputs/portfolio/<date>/packet.md`、`draft.md`、`portfolio-advisor/portfolio/portfolio-config.yaml`、`portfolio-advisor/portfolio/investment-policy.md`（`03-redteam.md` 自身宣告的攻擊清單第 4/7/9 項要對照 `portfolio-config.yaml`、第 5/9 項要對照 `investment-policy.md`，兩份都要給）

**不可以**把主對話目前為止的討論、你對草稿的想法、或任何推理過程寫進 subagent 的 prompt。等 subagent 完成並寫出 `redteam.md`，主對話再讀取結果繼續④之後的流程。

## ⑤ 降級與 degraded 規則

- **找不到 Chrome/Edge**：`render_portfolio_report.py` 會印 warning 到 stderr，只產出 `.html`、沒有 `.pdf`，但 exit code 仍是 0——這是**正常降級**，不是失敗，在 `final.md` 註明即可。
- **查不到即時價格、匯率、財報數字**：一律讓查價流程標示 degraded，禁止用其他標的的數字推算或腦補填入——這才是真正的 degraded，跟上面「腳本自動降級」不同。
- 若腳本因其他原因（JSON 格式錯誤、模板讀取失敗）真的失敗，要如實回報失敗，不可假裝完成。

## ⑥ 合規提醒

每次交付的 `final.md`／`summary-short.md`／`report-data.json` 的 `compliance` 欄位，以及完成回報最後一行，都必須附上：

> 本報告僅供研究與教育用途，不構成投資建議；最終決策與下單由使用者本人完成。

顧問不得自動下單，也不得繞過使用者確認；任何寫入帳本的交易都必須經過使用者本人明確確認。
