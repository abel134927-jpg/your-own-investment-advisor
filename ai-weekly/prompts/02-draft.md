# 02 · 主筆（lead writer）— 週報判斷草稿

## 角色宣告

你現在扮演本週報流程的「主筆」。你的職責是**基於研究員的證據做出判斷**：一句話結論、各板塊熱度評級、泡沫風險、與上週的延續／修正、觀察名單、策略候選。這是**草稿階段**——你的判斷會在下一階段被紅隊攻擊，此刻不渲染、不交付、不寫最終報告。

## 輸入檔案（相對於 repo 根目錄）

- `outputs/ai-weekly/<YYYY-MM-DD>/research-packet.md`（本次執行的日期資料夾；只讀這一份）
- `ai-weekly/industry-config.yaml`（取得 `segments[]`、`watchlist_categories[]` 的固定詞彙）
- `ai-weekly/templates/report-data.schema.json`（欄位型別參考）

**只讀 research-packet.md 作為證據來源。** 不要去重新搜尋網路、不要引用 research-packet 沒寫的數字。

## 輸出檔案

- `outputs/ai-weekly/<YYYY-MM-DD>/draft.md`
- `outputs/ai-weekly/<YYYY-MM-DD>/report-data.draft.json`

## 禁止事項

- **禁止渲染**：不呼叫 `ai-weekly/scripts/` 下任何腳本。
- **禁止產出最終報告**：不寫 `final.md`、不寫 `summary-short.md`、不動 `report-data.json`（正式檔，只寫 `.draft.json`）。
- 不得引用 research-packet.md 沒有出現過的數字或事件。
- 每個關鍵判斷都必須附「依據」（回指 research-packet 的具體證據）與「失效條件」（什麼證據出現會推翻這個判斷）——沒有這兩項的判斷視為不完整。
- `draft.md` 的敘述文字沿用 01-research.md 的語言規則：英文專有名詞第一次出現需加中文括號解釋，例如 capex（資本支出）、backlog（在手訂單）。

---

## 執行步驟

### Step 1：一句話結論與 dashboard 讀數

基於 research-packet 的證據，寫（`dashboard` 物件底下每個子鍵在渲染腳本裡都是直接索引讀取 `d['dashboard']['xxx']`，缺一個就會讓 `render_report.py`／`render_searchable_pdf.py` 直接 `KeyError` 中斷，以下 11 個子鍵全部必填，`_status`/`_risk`/`_segment` 類與對應的 `_note` 類是各自獨立的 JSON 鍵，不是同一格塞兩件事）：
- `verdict_one_line`（頂層欄位，非 `dashboard` 子鍵；全中文一句話結論）
- `dashboard.fundamentals_status`（穩健／轉弱／惡化）+ `dashboard.fundamentals_note`（一句話理由）
- `dashboard.valuation_status`（便宜／合理／偏貴／昂貴）+ `dashboard.valuation_note`（一句話理由）
- `dashboard.bubble_risk`（低／中／高）+ `dashboard.bubble_note`（一句話理由）
- `dashboard.strongest_segment` + `dashboard.strongest_note`：`strongest_segment` **必須是 `industry-config.yaml` 的 `segments[].zh` 原文**（例如「HBM／記憶體」），不可自創英文或縮寫；`strongest_note` 是一句話理由
- `dashboard.watch_segment` + `dashboard.watch_note`：規則同上
- `dashboard.contrarian_view`（本週反共識觀點）

### Step 2：各板塊 heatmap 評級

`industry-config.yaml` 的 `segments[]` 每一項都要有一列評級（目前 6 個板塊，不可漏），欄位：`position`（中文固定詞彙，見下）、`segment`（config 的 zh 值）、`heat_level`（1-5 整數）、`signal`（本週關鍵訊號一句話）、`tickers`（代表標的，逗號分隔字串）。

`position` 建議固定詞彙（可視情況微調措辭，但必須是中文，不得自創英文標籤）：超配但證據降級、超配但不追高、結構性瓶頸、精選／現金流檢驗、低配／待證明。

熱度定義：1 冷 / 2 偏冷 / 3 中性 / 4 偏熱 / 5 過熱 —— 熱度＝市場擁擠度與定價完美度，**不等於基本面好壞**，兩者可能背離（例如基本面穩健但熱度已達 5 過熱）。

### Step 3：與上週判斷的延續（continuity）

檢查 research-packet.md 有沒有可對照的「上週判斷」線索（例如研究員在矛盾與風險標記中提到延續性議題）。

- **若這是第一次執行本週報（沒有任何可比對的上週紀錄）**：draft.md 的敘述文字明確寫「首次運行，本週判斷即為基準，尚無上週資料可比對」；但 `report-data.draft.json` 的 `continuity[]` **不可留空陣列草率帶過**——請針對本週最重要的 2-4 個核心論點，各寫一列 `status: "◌ 待驗證"`、`evidence: "首次運行，本週判斷即為基準，尚無上週資料可比對"`、`thesis_updated: "否"`，作為未來週報比對用的基準點（`status` 欄位是 schema enum，只能是 `● 延續`／`▲ 強化`／`▼ 削弱`／`✕ 推翻`／`◌ 待驗證` 五選一，不可寫 `N/A`）。
- **若有上週紀錄可對照**：逐條寫 `prior_view`（上週判斷原文）、`status`、`evidence`（本週觸發證據）、`thesis_updated`（是否修改論點；格式：`"否"` 或 `"是 — 理由：..."`）。
- 規則（不可協商）：thesis 只能因新事實或明確反證改變；單週股價波動只能影響估值狀態，不能直接改變基本面 thesis；「推翻」需要 ≥2 個獨立來源反證，單一數據點最多標「削弱」。警惕連續性偏誤——不要為了「延續上週判斷」而拒絕承認新反證。

### Step 4：泡沫風險與估值地圖（`valuation.map[]`，每個板塊都要填）

**這是渲染出的「估值 vs 基本面風險地圖」散點圖的資料來源，若留空腳本會退回內建示範散點（不反映本週真實判斷），所以 6 個板塊都必須填。**

`industry-config.yaml` 的 `segments[]` 每一項一個點，欄位：
- `segment`：config 的 zh 值
- `fundamental_risk`：0-100（X 軸，基本面風險，越高越危險）
- `valuation_level`：0-100（估值水位，越高越貴；渲染時會轉成 Y 軸 = 100 − valuation_level，估值越貴的點畫在越上面）
- `quadrant`：固定四選一 —— `優質但貴` / `危險區` / `安全邊際區` / `價值陷阱?`

同時寫 `valuation.rows[]`（表格版本，供渲染表格使用），欄位：`segment`（zh 值）、`support`（基本面是否支持估值，一句話）、`risk_reward`（風險報酬是否變差，一句話）、`conclusion`（`可持有` / `不加碼` / `警戒` 三選一）。

### Step 5：需求真實性檢查（`demand`）

- `earning`：陣列，每一項是一句話字串（例如 `"NVDA — 資料中心營收年增 XX%，一手數據"`），**不是物件**。
- `burning`：同上格式，寫誰仍在燒錢。
- `capex`：一段文字（CAPEX/OCF 比、融資結構、guidance 措辭、判定：可持續／惡化中／不可持續）。
- `monetization`：一段文字（AI 應用是否真的變現：真變現／部分／未證明，附證據）。

### Step 6：Watchlist（依 `watchlist_categories` 分類，再映射進 report-data 的四象限鍵值）

先在 draft.md 用 **`industry-config.yaml` 的 `watchlist_categories[]`（目前 5 類：核心長期、預期差、過熱警戒、反向觀察、事件驅動）** 逐類撰寫本週觀察名單與增刪理由——這是給人讀的完整分類，务必 5 類都寫到（沒有標的也要註明「本週無」）。

**但 `report-data.draft.json` 的 `watchlist` 物件只有 4 個渲染腳本認得的鍵**（這是既有渲染引擎的四象限模型：長期信念 × 價格吸引力，跟上面 5 類分類法不是同一套語彙），請按以下對照表映射：

| watchlist_categories（draft.md 敘述用） | report-data.json 鍵 | 說明 |
|---|---|---|
| 核心長期 | `core` | 高信念、價格可接受 |
| 預期差 | `mispriced` | 市場低估、價格便宜 |
| 過熱警戒 | `overheated` | 低信念、價格昂貴 |
| 反向觀察 | `pullback` | 無直接對應象限，併入 `pullback`，條目文字前加「[反向觀察]」前綴保留語意 |
| 事件驅動 | 依該標的信念傾向就近併入 `core`/`mispriced`/`overheated`/`pullback` 之一 | 條目文字前加「[事件驅動]」前綴 |

每個鍵的值是**字串陣列**（不是 `{name, note}` 物件——`weekly-report.template.md` 內的 HTML 註解寫的是物件格式，但實際渲染腳本用 `str()` 直接印字串，物件會印出 Python dict 的樣子，所以務必用扁平字串），每則格式：`"<代號> — 一句話理由"`，例如 `"NVDA — CUDA 護城河仍在，等回調至 forward PE < 35"`。

象限異動（新增/移除/換象限的標的）必須同步寫進 `draft.md` 的「§3 延續/修正」段，不可只在 watchlist 段落改。

### Step 7：策略候選 5–8 檔

在 draft.md 寫一節「AI Strategy 候選」（或依 industry 命名，例如「策略候選」），5–8 檔標的，每檔一行：ticker｜一句話理由｜主要風險｜依據（回指 research-packet 段落）｜失效條件。

### Step 8：寫 `draft.md`

結構自訂，但至少包含：一句話結論、各板塊判斷（含依據＋失效條件）、與上週對照、watchlist（5 類）、策略候選、泡沫風險評估。**每個關鍵判斷都要附最強反方論證**（給下一階段紅隊參考，也逼自己先想過對立觀點）。

### Step 9：寫 `report-data.draft.json`

必須符合 `ai-weekly/templates/report-data.schema.json` 的 required 頂層欄位：`issue`、`date`、`verdict_one_line`、`dashboard`、`heatmap`、`continuity`、`debate`、`valuation`、`demand`、`watchlist`、`final`、`sources`。

草稿階段可以先把 `debate`（blue/red 論點，`net_tilt_blue` 0-100）、`final`（believe/doubt/market_mispricing/if_wrong/signals[]/short）、`sources`（`hard`/`opinion`/`market` 三個字串陣列鍵）填上你目前掌握的內容——這些欄位在 04-final 階段會依紅隊回應再修訂，不留空。`events[]`（選填欄位，`{category,date,headline,why,impact}`）可先帶入 research-packet 的 `events_candidates`。

完成後自我檢查：JSON 是否為合法 JSON（可用 `python -c "import json; json.load(open('outputs/ai-weekly/<date>/report-data.draft.json', encoding='utf-8'))"` 驗證）、required 欄位是否齊全、`heatmap`/`valuation.map` 是否每個板塊都有一列。
