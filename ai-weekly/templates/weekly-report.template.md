<!--
AI 產業鏈週報 · Markdown 完整版模板 (schema v1.0)
用途：文件庫留存 + AI agent 檢索與再生成
規則：
  1. 不得出現真實姓名等私人稱呼。可分享版。
  2. 報告語言以繁體中文為主；公司名稱、股票代號、產品名可保留英文。
  3. 英文專有名詞第一次出現時，若保留英文，需在後方加繁體中文括號解釋，例如 capex ROI（資本支出投資回收）、operating cash flow（營運現金流）。
  4. 常用通用詞直接中文化：Power→電力/能源、Grid→電網、Cooling→散熱、Watchlist→觀察名單、Sources→資料來源。
  5. H2 標題與 <!-- slot: --> 註解為固定 anchor，agent 不得改名。
  6. thesis 只能因新事實或明確反證改變；單週股價波動只影響估值狀態。
  7. 狀態符號固定：● 延續 / ▲ 強化 / ▼ 削弱 / ✕ 推翻 / ◌ 待驗證
  8. 熱度等級固定：1 冷 / 2 偏冷 / 3 中性 / 4 偏熱 / 5 過熱
  9. 證據等級固定：●●● 硬數據 / ●●○ 訊號 / ●○○ 敘事
-->

---
report: ai-value-chain-weekly
schema_version: "1.0"
issue: YYYY-Www            # ISO week
date: YYYY-MM-DD
verdict_one_line: ""       # 本週一句話判斷
fundamentals_status: 穩健   # 穩健 | 轉弱 | 惡化
fundamentals_score: 4      # 1–5
valuation_status: 偏貴      # 便宜 | 合理 | 偏貴 | 昂貴
valuation_score: 3         # 1–5
bubble_risk: 中             # 低 | 中 | 高
bubble_score: 3            # 1–5
strongest_segment: ""
watch_segment: ""
net_tilt_blue: 60          # Blue/Red 傾斜，0–100
tags: [ai-weekly, ai-value-chain]
---

# AI 產業鏈週報 · {{issue}}

> [!abstract] 本週一句話判斷
> <!-- slot: cover.verdict_one_line -->
> {{verdict_one_line}}

| 儀表 | 讀數 | 一句話理由 |
|---|---|---|
| AI 基本面 | `{{fundamentals_status}}` | <!-- slot: cover.fundamentals_note --> |
| 估值狀態 | `{{valuation_status}}` | <!-- slot: cover.valuation_note --> |
| 泡沫風險 | `{{bubble_risk}}` | <!-- slot: cover.bubble_note --> |
| 最強板塊 | `{{strongest_segment}}` | <!-- slot: cover.strongest_note --> |
| 最需警戒 | `{{watch_segment}}` | <!-- slot: cover.watch_note --> |

> [!tip] 本週反共識
> <!-- slot: cover.contrarian_view -->

---

## 02 AI 產業鏈熱力圖
<!-- slot: heatmap.rows[] · schema: {position, segment, heat_level 1-5, heat_label, signal, tickers} -->

> 熱度＝市場擁擠度與定價完美度，不等於基本面好壞。

| 位置 | 板塊 | 熱度 | 本週關鍵訊號 | 代表 |
|---|---|---|---|---|
| 上游 | HBM / DRAM | `4 偏熱` |  |  |
| 中游 | GPU / ASIC | `5 過熱` |  |  |
| 中游 | 光通訊 | `5 過熱` |  |  |
| 基建 | 電力 / 散熱 | `4 偏熱` |  |  |
| 下游 | Cloud CAPEX | `3 中性` |  |  |
| 下游 | AI 應用 | `2 偏冷` |  |  |

![供應鏈流向圖](../assets/{{date}}/supply-chain-map.svg)
<!-- asset: supply-chain-map.svg · 上游→中游→基建→下游節點圖，節點色=熱度色 -->

---

## 03 與上週判斷的延續 / 修正
<!-- slot: thesis_tracker.rows[] · schema: {prior_view, status ●▲▼✕◌, evidence, thesis_updated bool, update_reason} -->

狀態統計：`● 延續 n` · `▲ 強化 n` · `▼ 削弱 n` · `✕ 推翻 n` · `◌ 待驗證 n`

| 上週判斷 | 本週狀態 | 說明（觸發證據） | Thesis 更新 |
|---|---|---|---|
|  | `▲ 強化` |  | 否 |
|  | `● 延續` |  | 否 |
|  | `▼ 削弱` |  | 是 — 理由： |
|  | `◌ 待驗證` |  | 否 |

> [!warning] Thesis 變更規則（不可協商）
> 1. Thesis 只能因**新事實**或**明確反證**改變，變更必須註明觸發證據。
> 2. 單週股價波動只影響「估值狀態」，**不能直接改變基本面 thesis**。
> 3. 「推翻」需要 ≥2 個獨立來源反證；單一數據點最多標「削弱」。

---

## 04 本週重大事件
<!-- slot: events.company[] / events.chain[] / events.macro[] / events.geopolitics[] · schema: {date, headline, why_it_matters, impact_label} -->

### 公司與財報
- **MM-DD — 標題** · `影響 badge`
  重要性：

### 產業鏈
- **MM-DD — 標題** · `影響 badge`
  重要性：

### 宏觀 / 利率 / 資金面
- **MM-DD — 標題** · `影響 badge`
  重要性：

### 地緣政治 / 出口管制
- **MM-DD — 標題** · `影響 badge`
  重要性：

### 市場隱含機率
<!-- slot: events.implied_prob[] · schema: {event, market_implied, our_view} -->

| 事件 | 市場隱含 | 我們的評估 |
|---|---|---|
|  |  |  |

---

## 05 Blue Team vs Red Team
<!-- slot: debate.blue[] / debate.red[] · schema: {claim, evidence, strength ●●●|●●○|●○○} -->

### 🔵 Blue Team · 多頭論點
1. **論點** — 證據說明 `●●●`
2. **論點** — 證據說明 `●●○`
3. **論點** — 證據說明 `●○○`

### 🔴 Red Team · 空頭論點
1. **論點** — 證據說明 `●●●`
2. **論點** — 證據說明 `●●○`
3. **論點** — 證據說明 `●○○`

**當前傾斜（NET TILT）**：Blue {{net_tilt_blue}} / Red {{100-net_tilt_blue}} — 一句話說明傾斜變化。

---

## 06 Valuation Check
<!-- slot: valuation.map[] · schema: {segment, fundamental_risk 0-100, valuation_level 0-100, quadrant} -->
<!-- slot: valuation.table[] · schema: {segment, fundamentals_support, risk_reward_worse, conclusion} -->

| 板塊 | 基本面是否支持估值 | 風險報酬是否變差 | 結論 |
|---|---|---|---|
|  |  |  | `可持有 / 不加碼 / 警戒` |

> 估值 vs 基本面風險地圖為互動散點圖，直接渲染於 dashboard HTML（`render_report.py` 第 06 頁），對應上方 `valuation.map[]` schema；本 Markdown 存檔版不含對應靜態圖檔。

> [!quote] 估值紀律
> 單週股價波動只能改變「估值狀態」讀數，不構成基本面 thesis 的證據。價格是投票機，本報告只對稱重機負責。

---

## 07 需求真實性檢查
<!-- slot: demand.earning[] / demand.burning[] · schema: {who, metric} -->
<!-- slot: demand.capex · schema: {capex_ocf_ratio, funding_structure, guidance_tone, verdict} -->
<!-- slot: demand.monetization[] · schema: {layer, revenue_trend, unit_margin, verdict} -->

### 誰正在賺錢
| 環節 | 證據指標 |
|---|---|
|  |  |

### 誰仍在燒錢
| 環節 | 證據指標 |
|---|---|
|  |  |

### CAPEX 是否可持續
- CAPEX / OCF：
- 融資結構：
- Guidance 措辭：
- **判定**：`可持續 / 惡化中 / 不可持續`

![CAPEX 趨勢圖](../assets/{{date}}/capex-trend.png)

### AI 應用是否真的變現
| 層級 | 收入趨勢 | 單位毛利 | 判定 |
|---|---|---|---|
|  |  |  | `真變現 / 部分 / 未證明` |

---

## 08 Watchlist 四象限
<!-- slot: watchlist.core[] / watchlist.pullback[] / watchlist.mispriced[] / watchlist.overheated[] · schema: {name, note} -->
<!-- 縱軸：長期信念；橫軸：當前價格吸引力。象限異動必須在 §3 留檔。 -->

### 🟢 核心長期（高信念 · 價格可接受）
- **代號** — 一句話理由

### 🔵 等待回調（高信念 · 價格偏貴）
- **代號** — 一句話理由

### 🟡 預期差（市場低估 · 價格便宜）
- **代號** — 一句話理由

### 🔴 過熱警戒（低信念 · 價格昂貴）
- **代號** — 一句話理由

**本週象限異動**：<!-- slot: watchlist.moves -->

---

## 09 最終判斷
<!-- slot: final.believe / final.doubt / final.market_mispricing / final.if_wrong / final.signals[] -->

**我現在相信什麼**：

**我懷疑什麼**：

**市場可能錯估哪裡**：

**如果我錯了，最可能錯在哪裡**：

### 下週最值得觀察的 3–5 個信號
1. 信號 — 觸發後回寫哪個 section（§3 / §7 / 警戒觸發器）
2.
3.

---

## 10 Sources / Disclaimer
<!-- slot: sources[] · schema: {tier 一手|產業|二手|市場隱含, items[]} -->

### Sources（依證據等級）
- **一手 / 硬數據**：
- **產業數據**：
- **二手 / 訊號**：
- **市場隱含**：

> [!caution] Disclaimer
> 本報告為可分享之投資研究筆記，僅供資訊與教育用途，不構成任何證券之買賣建議或投資邀約。所有判斷可能出錯；讀者應自行進行盡職調查並為自身決策負責。過往表現不代表未來結果。

<!-- generated: {{date}} · schema v1.0 · pipeline: research packet → md → charts → html → pdf -->

> 本報告僅供研究與教育用途，不構成投資建議。
