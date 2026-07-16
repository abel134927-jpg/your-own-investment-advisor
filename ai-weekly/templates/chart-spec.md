# 圖表元件規格 · AI 產業鏈週報 (schema v1.0)

所有圖表遵守同一套 tokens（見 `design-tokens.css`）。原則：
- 純 HTML/CSS 可完成的圖（熱力圖、四象限、傾斜條、量表）**不出圖檔**，由 template 直接渲染 → PDF 永遠銳利。
- 需要數據繪圖的（CAPEX 趨勢、供應鏈圖）輸出 PNG 至 `assets/{issue}/`，模板留 `.asset-slot` 槽位，檔名固定。
- 圖內文字一律 IBM Plex Mono；中文標籤 Noto Sans TC。深底 `#070C18`，格線 `#16233F`。

---

## 1. 產業鏈熱力圖（HTML 渲染）
- 形式：grid 表格列，每列 = 一個環節（固定 6 列順序：HBM/DRAM → GPU/ASIC → 光通訊 → 電力/散熱 → Cloud CAPEX → AI 應用）
- 欄位：位置(56px) / 板塊(118px) / 熱度 badge(92px) / 溫度計(110px) / 關鍵訊號(1fr)
- 溫度計：5 格 16×8px、radius 2px、gap 3px；填 `heat_level` 格，填色 = `--heat-{level}`，未填 = `--track`
- 熱度 badge 對應：5 過熱→risk、4 偏熱→hot、3 中性→mute、2/1 偏冷→info
- Cover 縮略版（heat strip）：6 格卡片，10px 色點 + 板塊名 + 熱度字

## 2. Watchlist 四象限（HTML 渲染）
- 2×2 grid，gap 12px；軸標籤 mono 9px：Y=長期信念（vertical-rl）、X=當前價格吸引力
- 象限固定位置與色：右上 核心長期(ok) / 左上 等待回調(info) / 右下 預期差(warn) / 左下 過熱警戒(risk)
- 象限卡：4% 透明底 + 35% 透明邊框 + 象限名 14px/700 + 條目「mono 代號 — 一句話理由」
- 每期附「本週象限異動」註記；異動同步寫入 §3

## 3. Thesis 狀態 Dashboard（HTML 渲染）
- 5 格統計卡：24px mono 數字 + 狀態符號標籤
- 符號/色固定：● 延續(ok) ▲ 強化(ok) ▼ 削弱(warn) ✕ 推翻(risk) ◌ 待驗證(mute)
- 追蹤卡：grid `1fr 84px`，右上 badge；卡內固定三行 = 上週判斷 / 本週證據 / THESIS 更新：是|否＋理由

## 4. Blue vs Red 對照圖（HTML 渲染）
- 兩欄 `1fr 1fr`；左 `card--blue`、右 `card--red`，各含 2–4 張論點卡
- 論點卡固定三行：claim(13px/600) / evidence(11px muted) / 證據等級 `●●●|●●○|●○○`（mono，藍側 accent-text、紅側 risk-text）
- NET TILT 條：10px 高、radius 5px；左段 accent 漸層寬 = blue%，右段 risk 漸層，交界 2px 白線

## 5. Valuation vs Fundamental Risk Map（HTML 渲染）
- 400px 高 plot 區；X = 基本面風險 0–100 → left%、Y = 估值水位 0–100 → top% 反轉（高估值在上）
- 四象限底色(5–7% 透明)＋虛線十字：左上 優質但貴(warn) / 右上 危險區(risk) / 左下 安全邊際區(ok) / 右下 價值陷阱?(mute)
- 資料點：12px 圓、2px 頁底色描邊 + 1px 同色外環；點色 = 該板塊結論色；標籤 10.5px/600 置右

## 6. CAPEX Trend Chart（PNG 資產）
- 檔名：`assets/{issue}/capex-trend.png`，槽位尺寸 ~658×150px（@2x 輸出 1316×300）
- 內容：四大雲季度 CAPEX 堆疊柱（藍系四階：#1E4FA3/#2E7CD6/#35A2FF/#7CC4FF）+ YoY% 折線（--warn，右軸）
- 底 `#0A1120`、格線 `#16233F`、軸字 mono 9px `#5A6B8C`；不加圖表標題（槽外已有標籤）

## 7. Supply Chain Map（PNG 資產）
- 檔名：`assets/{issue}/supply-chain-map.png`，槽位 ~658×260px（@2x 1316×520）
- 內容：上游→中游→基建→下游 四欄節點圖；節點 = 圓角卡（板塊名+代表公司 mono），節點邊框色 = 當週熱度色；連線 1px `#2A3D63`，關鍵瓶頸連線 = accent 實線
- 節點色必須與 §2 熱力圖同步（同一 heat_level 來源）

---

## 生成規則（給 agent）
1. 數據來源 = 當週 research packet 的 `heatmap.rows[]`、`valuation.map[]` 等 slot（slot 名見 md 模板註解；PDF 模板開啟 `showSlotLabels` 可對照）。
2. HTML 渲染圖直接由 slot 數據套 tokens 生成；PNG 圖表生成後放入 `assets/{issue}/`，檔名不變，模板 `.asset-slot` 內以 `<img>` 置換。
3. 色彩只允許 tokens 內的值；新增語意需先擴充 tokens，不得 inline 發明新色。
4. 所有判斷型圖（熱度、象限、tilt）的值必須能在 §3 追溯上週值。
