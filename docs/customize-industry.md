# 自訂產業

`ai-weekly` 預設追蹤「AI 產業鏈」，但研究提示詞、渲染腳本、圖表全部讀同一份設定檔驅動：[`ai-weekly/industry-config.yaml`](../ai-weekly/industry-config.yaml)。換成任何你想追蹤的產業，不需要改任何程式碼，只要改這份設定檔。

## `industry-config.yaml` 欄位說明

```yaml
industry:
  name_zh: AI 產業鏈        # 產業中文名稱，會出現在報告標題、頁首
  name_en: AI Industry Chain # 產業英文名稱
report_language: zh-TW
segments:   # 熱力圖板塊清單；en 對應 report-data.json 的 segment 鍵值，zh 用於渲染顯示
  - { en: "HBM / Memory", zh: "HBM／記憶體" }
  - ...
research_categories:   # 研究段每期必查的類別（預設 7 類）
  - Hyperscaler CAPEX 與雲端資本支出
  - ...
valuation_snapshot_tickers: [NVDA, MSFT, ...]   # 估值快照要追蹤的標的代號
watchlist_categories: [核心長期, 預期差, 過熱警戒, 反向觀察, 事件驅動]   # 觀察名單分類
```

- **`industry.name_zh` / `industry.name_en`**：這個產業週報的中英文名稱。`name_zh` 會顯示在 **dashboard HTML/PDF**（`render_report.py` 產出）的封面標題、頁首與 `<title>`（格式：`{name_zh}週報`）。Archive／可搜尋 PDF（`render_searchable_pdf.py` 產出，見下方說明）的標題目前不吃這個設定，頁首名稱固定不變。
- **`segments[]`**：熱力圖要拆成幾個板塊，每項是 `{ en, zh }` 一對——`en` 是內部鍵值（要跟 `report-data.json` 裡的 segment 鍵值對上），`zh` 是渲染出來給人看的中文名稱。板塊數量不限，預設是 6 個。
- **`research_categories[]`**：研究員每期必查的研究類別清單，預設 7 類（含「來源品質與反向觀點」這種固定要查的項目）。換產業時把類別改成該產業真正關心的主題（例如半導體設備產業可能是「先進製程資本支出」「地緣政治出口管制」等）。
- **`valuation_snapshot_tickers[]`**：估值快照段要追蹤的個股代號清單，換成該產業的代表性公司即可。
- **`watchlist_categories[]`**：觀察名單要分成幾類，預設 5 類（核心長期／預期差／過熱警戒／反向觀察／事件驅動），一般不需要改，除非你想要不同的分類邏輯。

## 對 agent 說「我要 X 產業週報」

不需要自己動手編輯 YAML，直接對 agent 說類似「我要換成半導體設備產業週報」「幫我把週報換成別的產業」，流程是：

1. **Agent 訪談你**：依 `industry-config.yaml` 現有結構逐項問你——這個產業叫什麼名字（中英文）、要拆成哪些板塊、每期要查哪些研究類別、要追蹤哪些個股的估值快照、觀察名單要怎麼分類。
2. **Agent 改寫 `industry-config.yaml`**：把訪談結果寫回這份設定檔，覆蓋掉原本「AI 產業鏈」的預設值。
3. **直接跑第一期**：改完設定檔後，照 README「兩個模組」一節的觸發語（例如「跑本週週報」）直接執行即可，不需要額外步驟。

## 首次運行的 continuity 標記

換了新產業之後的第一期,沒有「上一期」可以比較——報告裡涉及「延續性（continuity）」的欄位（例如「這個判斷跟上週比是延續還是修正」）沒有歷史資料可比對，屬於**正常情況**，主筆會在草稿階段自行處理（標示為首次運行 / 無上期可比較），不代表流程出錯。從第二期開始，系統就能正常做週對週的延續性比較。

## 換產業後,渲染腳本怎麼吃到新設定

`generate_charts.py` 與 `render_report.py` 這兩支腳本都用 `--industry-config` 參數指定要讀哪一份設定檔（預設就是 `ai-weekly/industry-config.yaml`）。你不需要改任何腳本或指令：只要 `industry-config.yaml` 內容換了，agent 照 [`skills/ai-weekly/SKILL.md`](../skills/ai-weekly/SKILL.md) / [`AGENTS.md`](../AGENTS.md) 裡「④ 段執行順序」跑同一套指令，這兩支腳本就會自動吃到新產業的板塊、標的與分類，產出對應的熱力圖與 dashboard，不會殘留舊產業的設定。

`render_searchable_pdf.py`（產出 Archive／可搜尋 PDF）不吃 `--industry-config`，它的板塊中文標籤完全來自 `report-data.json` 本身的內容，不會另外讀設定檔。這代表換產業後不用改這支腳本，但要靠主筆在④定稿階段（`04-final`）依照新的 `industry-config.yaml` 把 `report-data.json` 裡的板塊名稱填成正確的中文標籤——只要定稿階段填對了，內文與板塊標籤就會正確跟隨新產業，不會殘留舊產業的板塊名稱。

**誠實說明**：這支腳本的報告標題（`<h1>`、頁首 meta、`<title>`）目前是**固定字串**「AI 產業鏈週報」，不會跟著 `industry-config.yaml` 換成新產業名稱——這是既定設計，不打算加參數修改。換產業後 Archive／可搜尋 PDF 的**內容與板塊標籤**會正確跟隨新產業（因為直接來自 `report-data.json`），但**頁首/標題的產業名稱不會變**。若這點造成困擾，可自行修改 `render_searchable_pdf.py` 裡的固定字串，或忽略 Archive PDF 標題、以 dashboard HTML/PDF（`render_report.py`，標題會正確跟隨 `industry.name_zh`）為準。
