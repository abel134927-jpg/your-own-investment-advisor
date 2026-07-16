# 04 · 主筆定稿（final write-up）— 終稿與渲染

## 角色宣告

你現在扮演本週報流程的「主筆」，回到定稿階段。紅隊已經審查過你的草稿，現在你要：逐條回應挑戰、定稿 `report-data.json`、跑渲染腳本、產出最終報告與短版摘要。這是**本週報唯一會產生正式交付物的階段**。

## 輸入檔案（相對於 repo 根目錄）

- `outputs/ai-weekly/<YYYY-MM-DD>/draft.md`
- `outputs/ai-weekly/<YYYY-MM-DD>/report-data.draft.json`
- `outputs/ai-weekly/<YYYY-MM-DD>/redteam.md`（**若此檔不存在，見下方「失敗容錯」，不要中止流程**）
- `outputs/ai-weekly/<YYYY-MM-DD>/research-packet.md`（回應紅隊挑戰時查證用）
- `ai-weekly/industry-config.yaml`
- `ai-weekly/templates/report-data.schema.json`
- `ai-weekly/templates/weekly-report.template.md`
- `ai-weekly/templates/summary-short.template.md`

## 輸出檔案

- `outputs/ai-weekly/<YYYY-MM-DD>/report-data.json`
- `outputs/ai-weekly/<YYYY-MM-DD>/final.md`
- `outputs/ai-weekly/<YYYY-MM-DD>/summary-short.md`
- 渲染腳本產出的資產（見 Step 3，路徑由腳本決定，不是手寫）

## 禁止事項

- 不得忽略任何一條 `R#`——每項二選一：**採納**（改判斷/評級/措辭並說明改了什麼）或**反駁**（引用 research-packet 的具體證據反駁，不得只說「我仍然認為」）。
- 紅隊「反對」而你堅持原判斷時，`final.md` 必須原文呈現紅隊的反對理由，讓讀者自行裁決，不可略過或淡化。
- 不得假裝腳本執行成功——找不到瀏覽器導致只有 HTML、沒有 PDF，是**正常降級**（腳本仍會 exit 0）；但若腳本因其他原因報錯（例如 JSON 格式錯誤、必要欄位缺失），必須如實記錄失敗，不可略過該產物就當作完成。
- 不得在 `report-data.json` 留下草稿階段的物件狀態欄位不一致（例如 watchlist 用了 `{name,note}` 物件而非字串陣列——渲染會印出 Python dict 字面量，是明確 bug）。
- `final.md`／`summary-short.md` 的敘述文字沿用 01-research.md 的語言規則：英文專有名詞第一次出現需加中文括號解釋，例如 capex（資本支出）、backlog（在手訂單）。

---

## Step 1：逐條回應紅隊挑戰

### 失敗容錯
若 `redteam.md` 不存在（表示上一階段沒有跑或失敗）：照常定稿交付，但 `final.md` 開頭（frontmatter 之後、verdict 之前）與 `summary-short.md` 第一行都要加上：`⚠️ 本期未經紅隊審查`。跳過本節其餘步驟，直接進 Step 2。

### 正常情況
讀 `redteam.md` 的「逐條攻擊」與「總表」，對每一個 `R#` 寫一段回應，二選一：
- **採納**：說明你把 `draft.md`／`report-data.draft.json` 的哪個判斷、評級或措辭改了。
- **反駁**：引用 `research-packet.md` 裡的具體數字或段落反駁，不得只重申「我仍然認為」。

把這些回應整理成 `final.md` 新增的一節「## 11 紅隊審查摘要」（附加在既有模板 10 節之後，不要更動模板既有的 H2 標題——它們是固定 anchor）。格式：

```markdown
## 11 紅隊審查摘要

| # | 紅隊攻擊 | 裁決 | 你的回應 |
|---|---|---|---|
| R1 | ... | 採納 / 反駁 | ... |
```

## Step 2：定稿 `report-data.json` 並自檢

依 Step 1 的回應，把 `report-data.draft.json` 修訂成最終版本，存為 `report-data.json`（同資料夾，不是覆寫 draft 檔——兩份都保留）。

**欄位規格提醒（以下以實際渲染腳本 `render_report.py`／`render_searchable_pdf.py` 的讀取邏輯為準；`weekly-report.template.md` 內部分 HTML 註解的欄位名與此不同，是模板文件本身的註解過時，請以下表為準，不要照模板註解寫）**：

| 欄位 | 型別 | 說明 |
|---|---|---|
| `dashboard` | 物件，**以下 11 個子鍵全部必填** | 兩支渲染腳本都用 `d['dashboard']['xxx']` 直接索引讀取（`render_report.py:285-287`、`render_searchable_pdf.py:130-135`），缺任何一個子鍵會直接 `KeyError` 中斷腳本，不是靜默略過：`fundamentals_status`、`fundamentals_note`、`valuation_status`、`valuation_note`、`bubble_risk`、`bubble_note`、`strongest_segment`（zh 值）、`strongest_note`、`watch_segment`（zh 值）、`watch_note`、`contrarian_view` |
| `heatmap[]` | `{position, segment, heat_level(1-5整數), signal, tickers}` | `segment` 用 `industry-config.yaml` 的 zh 值 |
| `continuity[]` | `{prior_view, status, evidence, thesis_updated}` | `status` 只能是 `● 延續`/`▲ 強化`/`▼ 削弱`/`✕ 推翻`/`◌ 待驗證` 五選一 |
| `events[]`（選填） | `{category, date, headline, why, impact}` | 注意欄位是 `why`/`impact`，不是模板註解寫的 `why_it_matters`/`impact_label` |
| `debate.blue[]` / `debate.red[]` | `{claim, evidence, strength}` | `strength` 用 `●●●`/`●●○`/`●○○` |
| `debate.net_tilt_blue` | 0-100 整數 | Blue/Red 傾斜 |
| `valuation.rows[]` | `{segment, support, risk_reward, conclusion}` | 注意鍵名是 `valuation.rows`，不是模板註解寫的 `valuation.table`；欄位是 `support`/`risk_reward`，不是 `fundamentals_support`/`risk_reward_worse` |
| `valuation.map[]` | `{segment, fundamental_risk(0-100), valuation_level(0-100), quadrant}` | `quadrant` 只能是 `優質但貴`/`危險區`/`安全邊際區`/`價值陷阱?` 四選一；六個板塊都要有點，缺了腳本會退回內建示範散點 |
| `demand.earning[]` / `demand.burning[]` | **字串陣列**（每項一句話） | 不是模板註解寫的 `{who,metric}` 物件 |
| `demand.capex` / `demand.monetization` | **字串**（一段文字） | 不是逐項表格 |
| `watchlist.core[]` / `.pullback[]` / `.mispriced[]` / `.overheated[]` | **字串陣列**，每項 `"<代號> — 一句話理由"` | 不是模板註解寫的 `{name,note}` 物件；四個鍵都要存在（可為空陣列） |
| `sources.hard[]` / `.opinion[]` / `.market[]` | 字串陣列 | 三個鍵，對應「一手/硬數據」「觀點來源」「市場隱含/輔助來源」 |
| `final.believe` / `.doubt` / `.market_mispricing` / `.if_wrong` | 字串 | |
| `final.signals[]` | 字串陣列 | 下週觀察信號 |
| `final.short` | 字串 | 一段精華摘要，會同時用在 dashboard PDF 最後一頁與 `summary-short.md` 的 `{{final_short}}` |
| `charts.capex_trend.series[]`（選填） | `[{name, values:[{period, value}]}]` | 各家公司每季 CAPEX，來自 research-packet 的 `chart_data.capex_trend`；缺此欄位 `generate_charts.py` 會退回內建示範數字（非報錯，但圖表不反映本週真實資料，請在降級記錄中註明） |

自我檢查（可直接執行）：

```bash
python -c "
import json
d = json.load(open('outputs/ai-weekly/<YYYY-MM-DD>/report-data.json', encoding='utf-8'))
required = ['issue','date','verdict_one_line','dashboard','heatmap','continuity','debate','valuation','demand','watchlist','final','sources']
missing = [k for k in required if k not in d]
assert not missing, f'缺少必要欄位: {missing}'
dashboard_required = ['fundamentals_status','fundamentals_note','valuation_status','valuation_note','bubble_risk','bubble_note','strongest_segment','strongest_note','watch_segment','watch_note','contrarian_view']
dashboard_missing = [k for k in dashboard_required if k not in d['dashboard']]
assert not dashboard_missing, f'dashboard 缺少必要子鍵: {dashboard_missing}'
for r in d['heatmap']:
    assert set(['position','segment','heat_level','signal','tickers']).issubset(r), r
for r in d['continuity']:
    assert set(['prior_view','status','evidence','thesis_updated']).issubset(r), r
for k in ['core','pullback','mispriced','overheated']:
    assert isinstance(d['watchlist'].get(k, []), list), f'watchlist.{k} 必須是陣列'
    for item in d['watchlist'].get(k, []):
        assert isinstance(item, str), f'watchlist.{k} 內有非字串項目: {item!r}'
print('schema self-check OK')
"
```

（本 repo 沒有 `jsonschema` 套件，上面用手寫檢查涵蓋最容易出錯的欄位；最終保證仍是 Step 3 腳本能否成功跑完不報錯。）

## Step 3：依序執行渲染腳本

**以下指令假設你的工作目錄在 repo 根目錄。** `<YYYY-MM-DD>` 換成本次日期。依序執行，**順序不可調換**（後兩支腳本都需要圖表資產已存在時效果才完整，雖然缺圖也不會讓腳本失敗）：

```bash
python ai-weekly/scripts/generate_charts.py \
  --data outputs/ai-weekly/<YYYY-MM-DD>/report-data.json \
  --industry-config ai-weekly/industry-config.yaml

python ai-weekly/scripts/render_report.py \
  --data outputs/ai-weekly/<YYYY-MM-DD>/report-data.json \
  --industry-config ai-weekly/industry-config.yaml

python ai-weekly/scripts/render_searchable_pdf.py \
  --data outputs/ai-weekly/<YYYY-MM-DD>/report-data.json
```

不加 `--out-dir`／`--assets-dir`：三支腳本會依 `--data` 路徑自動算出正確位置（`generate_charts.py` 產圖到 `outputs/ai-weekly/assets/<YYYY-MM-DD>/`，另兩支產 HTML/PDF 到 `outputs/ai-weekly/<YYYY-MM-DD>/`），跟 `weekly-report.template.md` 內圖片的相對路徑 `../assets/{{date}}/...` 對得上，不要自己另外指定路徑覆蓋。

`render_searchable_pdf.py` **沒有** `--industry-config` 參數（它的板塊譯名表是內建固定清單，不吃 config）——這也是為什麼 `report-data.json` 的 `segment`／`strongest_segment`／`watch_segment` 等欄位一定要直接寫 `industry-config.yaml` 的中文值（zh），而不是英文鍵，才能保證兩支渲染腳本都正確顯示中文。

**降級是正常行為，不是錯誤**：
- 若終端機找不到 Chrome/Edge，`render_report.py`／`render_searchable_pdf.py` 會印 `[warn] 未找到 Chrome/Edge,已輸出 HTML,略過 PDF` 到 stderr，只產出 `.html`、沒有 `.pdf`，但 exit code 仍是 0——這是預期行為，**不要回報成失敗**，在下方「降級記錄」註明即可。
- 若找不到 CJK 字型，`generate_charts.py` 會印 `[warn] 未找到 CJK 字型,圖表退回預設字型`，圖仍會產出，但中文字可能顯示不正常，同樣記錄不報錯。
- 若 `charts.capex_trend` 未填，CAPEX 趨勢圖會用內建示範數字，圖仍會產出，記錄「本週 CAPEX 圖為示範數字，非真實資料」。

把實際發生的降級情況（若有）記在 `final.md` 「## 10 Sources / Disclaimer」小節末尾新增一句「本期產出限制」說明（不要更動該節既有標題）。

## Step 4：依模板寫 `final.md` 與 `summary-short.md`

- `final.md`：依 `ai-weekly/templates/weekly-report.template.md` 的結構逐節填寫（frontmatter + 10 個固定 H2 + Step 1 新增的「## 11 紅隊審查摘要」）。frontmatter 欄位（`verdict_one_line`／`fundamentals_status`／`valuation_status`／`bubble_risk`／`strongest_segment`／`watch_segment`／`net_tilt_blue` 等）要跟 `report-data.json` 對應欄位一致。第 10 節的合規聲明文字保留模板原文，不要改寫或省略。
- `summary-short.md`：依 `ai-weekly/templates/summary-short.template.md` 填寫；`{{markdown_path}}` 填 `outputs/ai-weekly/<YYYY-MM-DD>/final.md`，`{{pdf_path}}` 填 `outputs/ai-weekly/<YYYY-MM-DD>/<YYYY-MM-DD>-dashboard.pdf`（若該 PDF 因降級不存在，改填對應的 `.html` 路徑並註明「PDF 未產出，見 HTML」）。

## Step 5：列出全部產物路徑

在完成回報中列出本次執行實際產生的所有檔案（不是預期清單，是真的跑出來、你確認存在的檔案），典型情況下應包含：

```text
outputs/ai-weekly/<YYYY-MM-DD>/report-data.json
outputs/ai-weekly/<YYYY-MM-DD>/final.md
outputs/ai-weekly/<YYYY-MM-DD>/summary-short.md
outputs/ai-weekly/<YYYY-MM-DD>/<YYYY-MM-DD>-dashboard.html
outputs/ai-weekly/<YYYY-MM-DD>/<YYYY-MM-DD>-dashboard.pdf        （若無瀏覽器則缺席，須註明）
outputs/ai-weekly/<YYYY-MM-DD>/<YYYY-MM-DD>-archive.html
outputs/ai-weekly/<YYYY-MM-DD>/<YYYY-MM-DD>-archive.pdf          （若無瀏覽器則缺席，須註明）
outputs/ai-weekly/<YYYY-MM-DD>/<YYYY-MM-DD>-searchable.pdf       （archive.pdf 的相容命名複本，同樣視瀏覽器有無而定）
outputs/ai-weekly/assets/<YYYY-MM-DD>/capex-trend.png
outputs/ai-weekly/assets/<YYYY-MM-DD>/supply-chain-map.svg
```

## Step 6：頁尾合規文字

在完成回報的最後一行附上：

> 本報告僅供研究與教育用途，不構成投資建議。
