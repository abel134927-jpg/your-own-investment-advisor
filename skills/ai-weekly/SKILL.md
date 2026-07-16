---
name: ai-weekly
description: Use when 用戶要求生成本週產業週報、初始化週報設定、或更換產業板塊
---

# ai-weekly — AI 產業鏈週報

單 agent 四段角色流程：研究員蒐證 → 主筆下判斷草稿 → 紅隊攻擊 → 主筆定稿並渲染。每段以檔案交接；只有紅隊那段有隔離規則（見下方④），其餘三段可在同一個對話裡依序執行。

## ① 觸發語範例

- 「跑本週週報」「產出這週的 AI 產業週報」
- 「這週 AI 產業有什麼變化，幫我看一下」
- 「我要換成半導體設備產業」「幫我把週報換成別的產業」
- 「初始化週報設定」「第一次用，帶我設定」

## ② 首次使用 onboarding

只有第一次使用、或環境有變動時才需要走完整段；平常直接跳到「③ 執行順序」即可。若 `outputs/ai-weekly/` 已有日期資料夾（代表先前已成功跑過一輪），可跳過下面的步驟 1–2，直接進「③ 執行順序」。

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

用 fixture 資料跑一次渲染，不需要真的研究內容：

```bash
python ai-weekly/scripts/generate_charts.py --data examples/fixtures/ai-weekly-report-data.json --industry-config ai-weekly/industry-config.yaml --assets-dir outputs/_smoke/assets
python ai-weekly/scripts/render_report.py --data examples/fixtures/ai-weekly-report-data.json --industry-config ai-weekly/industry-config.yaml --out-dir outputs/_smoke
python ai-weekly/scripts/render_searchable_pdf.py --data examples/fixtures/ai-weekly-report-data.json --out-dir outputs/_smoke
```

三支腳本都應該 exit code 0。`outputs/_smoke/` 只是暫時檢查用，可事後刪除（`outputs/` 已在 `.gitignore`）。若沒有瀏覽器，只會產出 `.html` 沒有 `.pdf`，同樣算通過。

**Step 3：產業訪談（只有想換掉預設「AI 產業鏈」產業時才需要）**

預設 `ai-weekly/industry-config.yaml` 已內建一組可直接使用的 AI 產業鏈設定（6 個板塊、7 類研究項目、10 檔估值標的、5 類觀察名單）。若使用者想換成別的產業，依 `industry-config.yaml` 現有結構逐項訪談使用者，改寫該檔：

- `industry.name_zh` / `industry.name_en`
- `segments[]`：熱力圖板塊清單，每項含 `en`/`zh` 對照
- `research_categories[]`：每期必查的研究類別
- `valuation_snapshot_tickers[]`：估值快照要追蹤的標的代號
- `watchlist_categories[]`：觀察名單分類

改完後，直接進入下方「③ 執行順序」跑第一期即可；第一期的「延續性（continuity）」欄位沒有上一期可比較，屬正常情況（主筆會在草稿階段自行處理）。

## ③ 四段執行順序與檔案交接

每一段都是「讀取並遵循」對應 prompt 檔案的完整內容來執行，不是照抄檔名跑腳本：

| 段落 | Prompt | 讀 | 寫 | 完成條件 |
|---|---|---|---|---|
| 1. 研究員 | `ai-weekly/prompts/01-research.md` | `ai-weekly/industry-config.yaml` | `outputs/ai-weekly/<date>/research-packet.md` | 7 類研究皆有資料或明確標 `MISSING`，10 檔估值快照皆已查 |
| 2. 主筆草稿 | `ai-weekly/prompts/02-draft.md` | `research-packet.md` | `draft.md` + `report-data.draft.json` | 每個判斷都附「依據＋失效條件」，dashboard 11 個子鍵全填 |
| 3. 紅隊 | `ai-weekly/prompts/03-redteam.md` | `research-packet.md` + `draft.md` + `report-data.draft.json` | `redteam.md` | 見下方④，**必須在隔離的 subagent 執行** |
| 4. 主筆定稿 | `ai-weekly/prompts/04-final.md` | `draft.md` + `report-data.draft.json` + `redteam.md`（若無則走失敗容錯） | `report-data.json` + `final.md` + `summary-short.md` + 渲染產物 | 三支渲染腳本皆執行過，逐條 `R#` 已回應（採納或反駁） |

`<date>` 為本次執行當天日期（`YYYY-MM-DD`），資料夾在 `outputs/ai-weekly/<date>/` 下，不存在就自行建立。全程跑完一次即為完整一期週報。

## ④ 紅隊必須隔離執行 —— 不得餵主上下文

`ai-weekly/prompts/03-redteam.md` 檔頭已明講：紅隊必須在**沒看過草稿、也沒看過主對話推理過程**的狀態下，先形成自己獨立的空頭觀點，否則會被草稿的措辭錨定、攻擊失去力道。

執行方式：**用 Task 工具（或你這個 agent 提供的等效 subagent／背景任務功能）開一個全新的 subagent**，subagent 的初始 prompt 只包含：

1. `ai-weekly/prompts/03-redteam.md` 的完整內容
2. 本次執行的檔案路徑：`outputs/ai-weekly/<date>/research-packet.md`、`draft.md`、`report-data.draft.json`、`ai-weekly/industry-config.yaml`

**不可以**把主對話目前為止的討論、你對草稿的想法、或任何推理過程寫進 subagent 的 prompt——subagent 應該只看得到上面兩項，其餘一概不給，讓它自己從 research-packet 重新形成判斷。等 subagent 完成並寫出 `redteam.md`，主對話再讀取結果繼續④之後的流程。

## ⑤ 降級與 degraded 規則

- **找不到 Chrome/Edge**：`render_report.py`／`render_searchable_pdf.py` 會印 warning 到 stderr，只產出 `.html`、沒有 `.pdf`，但 exit code 仍是 0——這是**正常降級**，不是失敗，不要重跑或報錯，在 `final.md` 註明即可。
- **找不到 CJK 字型**：圖表仍會產出，只是中文字可能顯示異常，同樣是正常降級，記錄不報錯。
- **研究資料缺料**：一律標 `MISSING`，禁止腦補或估算數字頂替——這才是 degraded，跟上面兩種「腳本自動降級」不同，degraded 的資料缺口要在報告裡明確列出，不能悄悄用猜測值填滿。
- 若腳本因其他原因（JSON 格式錯誤、必要欄位缺失）真的失敗，要如實回報失敗，不可假裝完成。

## ⑥ 合規提醒

每次交付的 `final.md`／`summary-short.md` 頁尾與完成回報最後一行，都必須附上：

> 本報告僅供研究與教育用途，不構成投資建議。

這份週報是研究筆記，不是持牌投資建議，所有判斷可能出錯，讀者需自行盡職調查。
