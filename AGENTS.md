# AGENTS.md — your-own-investment-advisor

## 這個 repo 是什麼

這是一個單一 repo，打包兩條個人投資研究 pipeline，設計給只用 Claude/Codex 桌面 agent（沒有額外基礎建設）的人直接跑：

- **`ai-weekly/`** — AI 產業鏈週報：每週研究一次產業鏈現況，產出帶熱力圖與圖表的報告。
- **`portfolio-advisor/`** — 投資組合週報 + 記帳：對你自己的持倉每週做一次顧問流程（狀態檢查、buy/sell 建議、風險檢查），外加隨時可用的自然語言記帳流程。

兩條 pipeline 都是「單 agent 四段角色流程」：研究員蒐證 → 主筆下判斷草稿 → 紅隊攻擊 → 主筆定稿並渲染，每段以檔案交接（不是四個獨立 agent，是你自己依序扮演每個角色，只是紅隊那一段有特殊隔離規則，見下方④）。你（Codex）讀這份檔案作為操作指南；Claude 端的對應入口是 `skills/ai-weekly/SKILL.md` 與 `skills/portfolio-advisor/SKILL.md`，內容邏輯一致，唯一差異是紅隊隔離的實作方式（Claude 用 subagent，Codex 用新對話，見④）。

所有指令假設工作目錄在 repo 根目錄。

## outputs/ 位置與日期目錄慣例

所有本地產出集中在 `outputs/`（已在 `.gitignore`，不會被提交）：

- ai-weekly 每期輸出在 `outputs/ai-weekly/<YYYY-MM-DD>/`（`<YYYY-MM-DD>` = 執行當天日期）
- portfolio-advisor 每期輸出在 `outputs/portfolio/<YYYY-MM-DD>/`

資料夾不存在就自行建立；沒有版本化機制，同一天內重複執行會覆蓋同一份日期資料夾，若要保留歷史需自行備份。

---

# 模組一：ai-weekly（AI 產業鏈週報）

## ① 觸發語範例

- 「跑本週週報」「產出這週的 AI 產業週報」
- 「這週 AI 產業有什麼變化，幫我看一下」
- 「我要換成半導體設備產業」「幫我把週報換成別的產業」
- 「初始化週報設定」「第一次用，帶我設定」

## ② 首次使用 onboarding

只有第一次使用、或環境有變動時才需要走完整段；平常直接跳到「③ 執行順序」即可。

**Step 1：環境自檢**

```bash
python --version          # 需 >= 3.10（若指令不存在，改試 python3 --version）
pip install -r requirements.txt   # 安裝 pillow + pyyaml
python -c "import yfinance"   # 驗證量化因子計算用的 yfinance 可匯入；失敗就重跑上面的 pip install。量化段會依 common/quant-factors.md 的 degraded 規則自動降級標 MISSING，不會卡住整個流程
```

檢查瀏覽器（用於渲染 PDF；找不到不是錯誤，只是會自動降級成只出 HTML）：

```bash
python -c "from common import render_env; b=render_env.find_browser(); print('Chrome/Edge:', b or 'NOT FOUND -> 正常降級，只出 HTML')"
```

**Step 2：smoke test（確認渲染管線可執行）**

```bash
python ai-weekly/scripts/generate_charts.py --data examples/fixtures/ai-weekly-report-data.json --industry-config ai-weekly/industry-config.yaml --assets-dir outputs/_smoke/assets
python ai-weekly/scripts/render_report.py --data examples/fixtures/ai-weekly-report-data.json --industry-config ai-weekly/industry-config.yaml --out-dir outputs/_smoke
python ai-weekly/scripts/render_searchable_pdf.py --data examples/fixtures/ai-weekly-report-data.json --out-dir outputs/_smoke
```

三支腳本都應該 exit code 0（`outputs/_smoke/` 是暫時檢查用，可事後刪除）。若沒有瀏覽器，只會產出 `.html` 沒有 `.pdf`，同樣算通過。

**Step 3：產業訪談（只有想換掉預設「AI 產業鏈」產業時才需要）**

預設 `ai-weekly/industry-config.yaml` 已內建一組可直接使用的設定（6 個板塊、7 類研究項目、10 檔估值標的、5 類觀察名單）。若使用者想換成別的產業，依 `industry-config.yaml` 現有結構逐項訪談使用者並改寫該檔：`industry.name_zh`/`industry.name_en`、`segments[]`（`en`/`zh` 對照）、`research_categories[]`、`valuation_snapshot_tickers[]`、`watchlist_categories[]`。改完直接跑第一期即可；第一期沒有上一期可比較（continuity 欄位）屬正常情況。

## ③ 四段執行順序與檔案交接

每一段都是「讀取並遵循」對應 prompt 檔案的完整內容來執行：

| 段落 | Prompt | 讀 | 寫 | 完成條件 |
|---|---|---|---|---|
| 1. 研究員 | `ai-weekly/prompts/01-research.md` | `ai-weekly/industry-config.yaml` | `outputs/ai-weekly/<date>/research-packet.md` | 7 類研究皆有資料或明確標 `MISSING`，10 檔估值快照皆已查 |
| 2. 主筆草稿 | `ai-weekly/prompts/02-draft.md` | `research-packet.md` | `draft.md` + `report-data.draft.json` | 每個判斷都附「依據＋失效條件」，dashboard 11 個子鍵全填 |
| 3. 紅隊 | `ai-weekly/prompts/03-redteam.md` | `research-packet.md` + `draft.md` + `report-data.draft.json` | `redteam.md` | 見下方④，**必須開新對話執行** |
| 4. 主筆定稿 | `ai-weekly/prompts/04-final.md` | `draft.md` + `report-data.draft.json` + `redteam.md`（若無則走失敗容錯） | `report-data.json` + `final.md` + `summary-short.md` + 渲染產物 | 三支渲染腳本皆執行過，逐條 `R#` 已回應（採納或反駁） |

## ④ 紅隊必須開新對話 —— 不得帶著主對話上下文

`ai-weekly/prompts/03-redteam.md` 檔頭已明講：紅隊必須在**沒看過草稿、也沒看過主對話推理過程**的狀態下，先形成自己獨立的空頭觀點，否則會被草稿的措辭錨定、攻擊失去力道。

Codex 端操作方式：

1. **開一個全新對話**（不是接著目前這個對話問下去）。
2. 只貼入兩件事：`ai-weekly/prompts/03-redteam.md` 的完整內容，以及本次執行的 `outputs/ai-weekly/<date>/research-packet.md`、`draft.md`、`report-data.draft.json`、`ai-weekly/industry-config.yaml` 這幾份檔案的內容。**不要**貼入主對話目前為止的討論或你對草稿的想法。
3. 讓新對話依 prompt 產出 `redteam.md`，存回 `outputs/ai-weekly/<date>/redteam.md`。
4. 回到（或再開）原本的對話，帶著 `redteam.md` 繼續④之後的第 4 段（主筆定稿）。

## ⑤ 降級與 degraded 規則

- **找不到 Chrome/Edge**：只產出 `.html`、沒有 `.pdf`，exit code 仍是 0——正常降級，不是失敗，在 `final.md` 註明即可。
- **找不到 CJK 字型**：圖表仍會產出，只是中文字可能顯示異常，同樣是正常降級。
- **研究資料缺料**：一律標 `MISSING`，禁止腦補或估算數字頂替——這才是 degraded，跟上面兩種「腳本自動降級」不同。
- 若腳本因其他原因（JSON 格式錯誤、必要欄位缺失）真的失敗，要如實回報失敗，不可假裝完成。

## ⑥ 合規提醒

`final.md`／`summary-short.md` 頁尾與完成回報最後一行，都必須附上：

> 本報告僅供研究與教育用途，不構成投資建議。

---

# 模組二：portfolio-advisor（投資組合週報 + 記帳）

## ① 觸發語範例

- 「跑本週 Portfolio Weekly」「幫我看一下這週組合狀況」
- 「我買了 X」「我賣了 X」「幫我記一筆交易」「我入金了 10000 美金」
- 「初始化我的投資組合」「第一次用，帶我設定持倉」

## ② 首次使用 onboarding

**Step 1：環境自檢**

```bash
python --version          # 需 >= 3.10（若指令不存在，改試 python3 --version）
pip install -r requirements.txt   # 安裝 pillow + pyyaml
python -c "import yfinance"   # 驗證量化因子計算用的 yfinance 可匯入；失敗就重跑上面的 pip install。量化段會依 common/quant-factors.md 的 degraded 規則自動降級標 MISSING，不會卡住整個流程
```

檢查瀏覽器：

```bash
python -c "from common import render_env; b=render_env.find_browser(); print('Chrome/Edge:', b or 'NOT FOUND -> 正常降級，只出 HTML')"
```

**Step 2：smoke test**

```bash
python portfolio-advisor/scripts/render_portfolio_report.py --data examples/fixtures/portfolio-report-data.json --out-pdf outputs/_smoke/portfolio-report-data.pdf
```

應 exit code 0（`outputs/_smoke/` 是暫時檢查用，可事後刪除）。沒有瀏覽器時只出 `.html`，同樣算通過。

**Step 3：持倉與 investment-policy 訪談**

真實帳本目錄 `portfolio-advisor/portfolio/` 是 gitignored、不會被提交，第一次使用先從範本複製：

```bash
cp -r portfolio-advisor/portfolio.example portfolio-advisor/portfolio
```

複製之後依序訪談使用者並填寫：

1. **交易紀錄**：`portfolio-advisor/portfolio/transactions.csv` 的範例列清空，改用下方「記帳流程」逐筆把使用者現有持倉（起始入金 + 各筆買入）補進去，或一次性訪談建檔。
2. **`portfolio-config.yaml`**：訪談 `target_allocation`（各 sleeve 目標權重、再平衡帶寬）、`risk_limits`（單一標的上限、週轉率警戒、現金下限等）、`benchmarks`、`fx_rates`。
3. **`investment-policy.md`**：逐節填掉全部 `<請填寫>`——授權邊界、投資目標、投資期限、風險偏好與禁用工具清單、賣出／減碼門檻、benchmarks、現金與出入金規則、合規與責任邊界。這份文件是每次顧問流程的最高優先規則。

訪談完成後才進入下方「③ 執行順序」跑第一期；第一期沒有 `recommendations.csv` 歷史紀錄，視為首次運行。

## ③ 執行順序與檔案交接

**每週顧問流程**（四段，讀取並遵循對應 prompt 檔案完整內容執行）：

| 段落 | Prompt | 讀 | 寫 | 完成條件 |
|---|---|---|---|---|
| 1. 研究員 | `portfolio-advisor/prompts/01-packet.md` | `portfolio-advisor/portfolio/` 下帳本與設定檔 | `outputs/portfolio/<date>/packet.md`（副作用：更新 `price-snapshots.csv`、重建 `holdings.json`） | 每檔持倉皆已查價或標 degraded，`packet.md` 無殘留 `TODO` |
| 2. 主筆草稿 | `portfolio-advisor/prompts/02-draft.md` | `packet.md` + `recommendations.csv`/`transactions.csv`（只讀） | `draft.md` | Core 持倉五態判定齊全，策略倉建議每條附最強反方論證 |
| 3. 紅隊 | `portfolio-advisor/prompts/03-redteam.md` | `packet.md` + `draft.md` + `portfolio-config.yaml` + `investment-policy.md` | `redteam.md` | 見下方④，**必須開新對話執行** |
| 4. 主筆定稿 | `portfolio-advisor/prompts/04-final.md` | `draft.md` + `redteam.md`（若無則走失敗容錯） + `packet.md` | `report-data.json` + `final.md` + `summary-short.md` + 渲染產物 + append `recommendations.csv` | 逐條 `R#` 已回應，渲染腳本已執行過 |

**記帳流程**（隨時觸發，不是上面四段的一部分）：讀取並遵循 `portfolio-advisor/prompts/ledger-entry.md`。流程固定為：自然語言報單 → 解析成 pending 交易並展示摘要表 → **等使用者在下一則訊息明確確認**（同一則訊息裡順帶講的確認語句不算數）→ 確認後才 append 到 `transactions.csv` 並重建 `holdings.json`。未經確認絕不寫入是硬邊界，模糊輸入要追問，不可用假設值填補。

## ④ 紅隊必須開新對話 —— 不得帶著主對話上下文

`portfolio-advisor/prompts/03-redteam.md` 檔頭已明講：紅隊必須在**沒看過草稿、也沒看過主對話推理過程**的狀態下，先形成自己獨立的空頭觀點。

Codex 端操作方式：

1. **開一個全新對話**。
2. 只貼入：`portfolio-advisor/prompts/03-redteam.md` 的完整內容，以及本次執行的 `outputs/portfolio/<date>/packet.md`、`draft.md`、`portfolio-advisor/portfolio/portfolio-config.yaml`、`portfolio-advisor/portfolio/investment-policy.md` 這四份檔案的內容（`03-redteam.md` 自身宣告的攻擊清單第 4/7/9 項要對照 `portfolio-config.yaml`、第 5/9 項要對照 `investment-policy.md`，兩份都要貼）。**不要**貼入主對話目前為止的討論或你對草稿的想法。
3. 讓新對話依 prompt 產出 `redteam.md`，存回 `outputs/portfolio/<date>/redteam.md`。
4. 回到（或再開）原本的對話，帶著 `redteam.md` 繼續④之後的第 4 段（主筆定稿）。

## ⑤ 降級與 degraded 規則

- **找不到 Chrome/Edge**：只產出 `.html`、沒有 `.pdf`，exit code 仍是 0——正常降級，不是失敗。
- **查不到即時價格、匯率、財報數字**：一律標示 degraded，禁止用其他標的的數字推算或腦補填入。
- 若腳本因其他原因（JSON 格式錯誤、模板讀取失敗）真的失敗，要如實回報失敗，不可假裝完成。

## ⑥ 合規提醒

`final.md`／`summary-short.md`／`report-data.json` 的 `compliance` 欄位，以及完成回報最後一行，都必須附上：

> 本報告僅供研究與教育用途，不構成投資建議；最終決策與下單由使用者本人完成。

顧問不得自動下單，也不得繞過使用者確認；任何寫入帳本的交易都必須經過使用者本人明確確認。
