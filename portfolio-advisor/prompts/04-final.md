# 04 · 主筆定稿（final write-up）— 終稿與渲染

## 角色宣告

你現在扮演本次 Portfolio Weekly 流程的「主筆」，回到定稿階段。紅隊已經審查過你的草稿，現在你要：逐條回應挑戰、定稿 `report-data.json`、跑渲染腳本、產出最終報告與短版摘要、把可執行建議 append 到 `recommendations.csv`。這是**本次流程唯一會產生正式交付物的階段**。

## 輸入檔案（相對於 repo 根目錄）

- `outputs/portfolio/<YYYY-MM-DD>/draft.md`
- `outputs/portfolio/<YYYY-MM-DD>/redteam.md`（**若此檔不存在，見下方「失敗容錯」，不要中止流程**）
- `outputs/portfolio/<YYYY-MM-DD>/packet.md`（回應紅隊挑戰、填 `report-data.json` 時查證用）
- `portfolio-advisor/portfolio/recommendations.csv`（若存在，append 前用來算下一個 `rec_id` 序號）
- `portfolio-advisor/portfolio/portfolio-config.yaml`
- `portfolio-advisor/portfolio/investment-policy.md`
- `portfolio-advisor/templates/report-data.schema.json`
- `portfolio-advisor/templates/portfolio-dashboard.template.html`（欄位規格提醒表的依據來源，見下方 Step 2）

## 輸出檔案

- `outputs/portfolio/<YYYY-MM-DD>/report-data.json`
- `outputs/portfolio/<YYYY-MM-DD>/final.md`
- `outputs/portfolio/<YYYY-MM-DD>/summary-short.md`
- 渲染腳本產出的資產（見 Step 3，路徑由腳本決定，不是手寫）
- `portfolio-advisor/portfolio/recommendations.csv`（append 新列；首次執行時連表頭一起建檔）

## 禁止事項

- 不得忽略任何一條 `R#`——每項二選一：**採納**（改判斷／權重／措辭並說明改了什麼）或**反駁**（引用 `packet.md` 的具體證據反駁，不得只說「我仍然認為」）。
- 紅隊「反對」而你堅持原判斷時，`final.md` 必須原文呈現紅隊的反對理由，讓讀者自行裁決，不可略過或淡化。
- 不得假裝腳本執行成功——找不到瀏覽器導致只有 HTML、沒有 PDF，是**正常降級**（腳本仍會 exit 0）；但若腳本因其他原因報錯（例如 JSON 格式錯誤、模板讀取失敗），必須如實記錄失敗，不可略過該產物就當作完成。
- 不得改寫或刪除 `recommendations.csv` 既有的列——只能 append。
- `final.md`／`summary-short.md` 的敘述文字沿用 `01-packet.md` 的語言規則：英文專有名詞第一次出現需加中文括號解釋，例如 capex（資本支出）、backlog（在手訂單）。

---

## Step 1：逐條回應紅隊挑戰

### 失敗容錯

若 `redteam.md` 不存在（表示上一階段沒有跑或失敗）：照常定稿交付，但 `final.md` 開頭與 `summary-short.md` 第一行都要加上：`⚠️ 本期未經紅隊審查`。`report-data.json` 的 `redteam` 物件填 `{"reviewed": false, "agree": 0, "reserved": 0, "oppose": 0, "summary": "本期未經紅隊審查"}`。跳過本節其餘步驟，直接進 Step 2。

### 正常情況

讀 `redteam.md` 的「逐條攻擊」與「總表」，對每一個 `R#` 寫一段回應，二選一：

- **採納**：說明你把 `draft.md` 的哪個判斷、權重或措辭改了。
- **反駁**：引用 `packet.md` 裡的具體數字或段落反駁，不得只重申「我仍然認為」。

把這些回應整理成 `final.md` 新增的一節「## 紅隊審查摘要」，格式：

```markdown
## 紅隊審查摘要

| # | 紅隊攻擊 | 裁決 | 你的回應 |
|---|---|---|---|
| R1 | ... | 採納 / 反駁 | ... |
```

同時統計 `agree`／`reserved`／`oppose` 三個數字（分別對應 `redteam.md` 總表裡「同意」「有保留」「反對」的筆數），供 Step 2 填入 `report-data.json` 的 `redteam` 物件。

## Step 2：定稿 `report-data.json` 並自檢

**欄位規格以下表為準**——`render_portfolio_report.py` 本身只是把整包 JSON 塞進 `window.REPORT_DATA`（見 `render_portfolio_report.py` 的 `fill_template()`），實際「讀取」每個欄位的邏輯在 `portfolio-advisor/templates/portfolio-dashboard.template.html` 內嵌的 JS（`page1()`~`page7()`），下表附行號引用；`report-data.schema.json` 的 `required`／`enum` 定義與這份 JS 完全一致（本 repo 沒有 `jsonschema` 套件，不會有程式強制擋，但仍是「這份檔案的正式契約」，請照著填，不要只依賴 JS 不會當就算過）：

| 頂層欄位 | 型別 | 說明（附 `portfolio-dashboard.template.html` 行號） |
|---|---|---|
| `report_date` / `as_of_date` | 字串，`YYYY-MM-DD` | 頁首顯示（`:292`）；`as_of_date` 用 packet §1 的 as-of 價格日期，不一定等於 `report_date` |
| `verdict_one_line` | 字串 | 封面一句話結論（`:358`） |
| `degraded_items` | 字串陣列 | 直接沿用 `packet.md` §0 的降級清單（`:307-310`）；packet 沒有降級項目就填空陣列 |
| `redteam` | 物件，**5 子鍵全填**：`reviewed`(bool)、`agree`/`reserved`/`oppose`(整數)、`summary`(字串) | `:305,312-323`；`reviewed=false` 時 JS 只顯示「本期未經紅隊審查」，仍要把 4 個數字鍵都填（可以是 0） |
| `allocation` | 物件，`total_usd`(數字)、`sleeves[]` | `:325-344,353,366,573` |
| `allocation.sleeves[]` | `{name, value, weight, target}`，`target` 可為 `null` | 對照 packet §2.1；沒有目標配置的 sleeve（例如 Crypto Satellite）`target` 填 `null`，不要填 0（0 會被畫成「目標是零」） |
| `holdings[]` | 每筆 `{ticker,type,sleeve,qty,avg_cost,price,mv,pnl,return_pct,weight,currency}` | `:382-398`。**只放 packet §2.2 非 degraded 的持倉**——degraded 持倉不進這裡（型別要求都是數字，塞不進 `null`），只留在 `degraded_items[]` 裡 |
| `holdings[].mv` / `.pnl` | 數字，**USD** | `money()` 格式化會直接印 `$` 前綴（`:250,391-392`），所以就算某檔是 HKD 計價，`mv`/`pnl` 也要換成 USD：`mv = mv_native × fx_rate`、`pnl = pnl_native × fx_rate`（`fx_rate` 取自 `portfolio-config.yaml` 的 `fx_rates`，跟 wrapper packet 腳本用的是同一組）；`price`/`avg_cost` 維持原生幣別，`currency` 欄標明幣別即可（JS 會在 ticker 後面加幣別 chip，`:383`） |
| `thesis_board[]` | 每筆 `{ticker, status, note}`，`status_reason` 選填 | `:422-429`。`status` 只能是 `強化`/`未變`/`削弱`/`破壞`/`估值過熱`/`待驗證`/`追蹤` 七選一（`:260-268`）——前五個對應 draft.md 的五態判定；`待驗證` 給首次運行或資料不足的持倉（配 `status_reason` 說明缺什麼）；`追蹤` 給 Crypto Satellite／ETF 這類只追蹤曝險、不做個別 thesis 判定的持倉 |
| `recommendations[]` | 每筆 `{ticker,action,target_weight,current_weight,diff,reason,exit,redteam_verdict,redteam_note}`，`final_decision` 選填但建議填 | `:442-462,280-284`。本次終版建議（只放你在 Step 1 之後仍然主張要做的動作，「觀望」也算） |
| `recommendations[].action` | 字串，**8 選 1**：`買入`/`加碼`/`增持`/`持有`/`觀望`/`減碼`/`賣出`/`清倉` | `:287`。**這個 enum 跟 `02-draft.md` 建議表的動作 enum（買入/續抱/加碼/減碼/賣出/換入/換出/觀望）不是同一套**——dashboard 徽章顏色只認這 8 個詞（用不到的詞會退回中性藍色徽章，不會壞掉，但顏色語意會跑掉）。轉換時用下表對照，不要直接照抄 draft.md 的詞。**8 個 schema 值全部都要有機會被產生，不可以有永遠用不到的值**，`加碼`/`增持` 與 `賣出`/`清倉` 各自用一個可檢查的數字條件區分： |
| | | `買入→買入`；`續抱→持有`；`減碼→減碼`；`觀望→觀望`；`換入→買入`（在 `reason` 裡註明「換股買入，原輪動對象見 recommendations.csv」）；`換出→賣出`（同樣在 `reason` 註明） |
| | | `加碼`（draft）依 `diff = target_weight − current_weight` 拆兩種：**`diff < portfolio-config.yaml` 的 `target_allocation.rebalance_band`（目前 0.05）→ `加碼`**（例行性小幅加碼，尚未偏離原目標很多）；**`diff ≥ rebalance_band` → `增持`**（一次拉高很多、明顯偏離原有配置的重倉決定，用機構語彙「增持」區隔） |
| | | `賣出`（draft）依 `target_weight` 拆兩種：**`target_weight == 0` → `清倉`**（全部出清，不保留部位）；**`target_weight > 0` → `賣出`**（只賣掉一部分，仍保留部位） |
| `recommendations[].redteam_verdict` | 字串，3 選 1：`同意`/`有保留`/`反對` | `:272-276`。對應這條建議在 `redteam.md` 裡被攻擊時的裁決；沒被紅隊點名的建議填 `同意` 並在 `redteam_note` 註明「未被紅隊列為攻擊點」 |
| `prior_recommendations[]` | 每筆 `{recommendation, executed, result, revision}` | `:476-491`。對應 Step 1「上週建議追蹤」；首次運行填空陣列（JS 會自動顯示「首週基線」空狀態，`:484-491`） |
| `lookthrough` | 物件，`{as_of_date, total_usd, rows[], limitations, price_reconciliation}` | `:523-537`。`rows[]` 每筆 `{ticker, components, exposure_usd, exposure_pct}`——`ticker` 是公司（不是 ETF），`components` 寫透過哪些 ETF/直接持股曝險到它，資料來自 `packet.md` §4 的「ETF 前十大成分重疊」小節；沒有做穿透分析就把 `rows` 填空陣列並在 `limitations` 如實寫「本期未建立 ETF 穿透基線」 |
| `user_actions[]` | 每筆 `{item, owner, status, detail}` | `:544-547`。`owner` 3 選 1：`使用者`/`系統`/`使用者（可選）`；`status` 3 選 1：`本週執行`/`事件後更新`/`資料核對`。不可把系統自己該做的事（例如「下次執行前更新價格快照」）標成使用者要做的事 |
| `risks[]` | 字串陣列 | `:494-495`，每項一句話 |
| `events[]` | 每筆 `{date, event, tickers, action}` | `:500-507`。`action` 欄若包含「觀察」「不預先」「不行動」等字樣，dashboard 會顯示「觀察」灰徽章，否則顯示「需行動」黃徽章（`:501`）——寫的時候留意這個關鍵字判斷，不要文字上明明是「先觀察」卻被判成「需行動」 |
| `methodology_notes` / `compliance` | 字串 | `:559` / `:555`。`compliance` 固定放合規聲明（見 Step 6） |

自我檢查（可直接執行，執行前把 `<YYYY-MM-DD>` 換成本次日期）：

```bash
python -c "
import json
d = json.load(open('outputs/portfolio/<YYYY-MM-DD>/report-data.json', encoding='utf-8'))

required = ['report_date','as_of_date','verdict_one_line','degraded_items','redteam',
            'allocation','holdings','thesis_board','recommendations','prior_recommendations',
            'lookthrough','user_actions','risks','events','methodology_notes','compliance']
missing = [k for k in required if k not in d]
assert not missing, f'缺少必要欄位: {missing}'

redteam_required = ['reviewed','agree','reserved','oppose','summary']
redteam_missing = [k for k in redteam_required if k not in d['redteam']]
assert not redteam_missing, f'redteam 缺少必要子鍵: {redteam_missing}'

assert 'total_usd' in d['allocation'] and 'sleeves' in d['allocation'], 'allocation 缺 total_usd/sleeves'
for s in d['allocation']['sleeves']:
    assert set(['name','value','weight','target']).issubset(s), f'sleeve 缺欄位: {s}'

holdings_required = {'ticker','type','sleeve','qty','avg_cost','price','mv','pnl','return_pct','weight','currency'}
for h in d['holdings']:
    assert holdings_required.issubset(h), f'holdings 缺欄位: {h}'

THESIS_ENUM = {'強化','未變','削弱','破壞','估值過熱','待驗證','追蹤'}
for t in d['thesis_board']:
    assert set(['ticker','status','note']).issubset(t), f'thesis_board 缺欄位: {t}'
    assert t['status'] in THESIS_ENUM, f'thesis_board.status 不合法: {t[\"status\"]}'

ACTION_ENUM = {'買入','加碼','增持','持有','觀望','減碼','賣出','清倉'}
VERDICT_ENUM = {'同意','有保留','反對'}
rec_required = {'ticker','action','target_weight','current_weight','diff','reason','exit','redteam_verdict','redteam_note'}
for r in d['recommendations']:
    assert rec_required.issubset(r), f'recommendations 缺欄位: {r}'
    assert r['action'] in ACTION_ENUM, f'recommendations.action 不合法: {r[\"action\"]}'
    assert r['redteam_verdict'] in VERDICT_ENUM, f'recommendations.redteam_verdict 不合法: {r[\"redteam_verdict\"]}'

for p in d['prior_recommendations']:
    assert set(['recommendation','executed','result','revision']).issubset(p), f'prior_recommendations 缺欄位: {p}'

lt_required = {'as_of_date','total_usd','rows','limitations','price_reconciliation'}
assert lt_required.issubset(d['lookthrough']), f'lookthrough 缺欄位: {d[\"lookthrough\"]}'
for row in d['lookthrough']['rows']:
    assert set(['ticker','components','exposure_usd','exposure_pct']).issubset(row), f'lookthrough.rows 缺欄位: {row}'

OWNER_ENUM = {'使用者','系統','使用者（可選）'}
STATUS_ENUM = {'本週執行','事件後更新','資料核對'}
for a in d['user_actions']:
    assert set(['item','owner','status','detail']).issubset(a), f'user_actions 缺欄位: {a}'
    assert a['owner'] in OWNER_ENUM, f'user_actions.owner 不合法: {a[\"owner\"]}'
    assert a['status'] in STATUS_ENUM, f'user_actions.status 不合法: {a[\"status\"]}'

for e in d['events']:
    assert set(['date','event','tickers','action']).issubset(e), f'events 缺欄位: {e}'

assert isinstance(d['risks'], list) and all(isinstance(x, str) for x in d['risks']), 'risks 必須是字串陣列'

print('schema self-check OK')
"
```

（本 repo 沒有 `jsonschema` 套件，上面用手寫檢查涵蓋 required 欄位與最容易出錯的 enum；最終保證仍是 Step 3 腳本能否成功跑完不報錯。）

## Step 3：執行渲染腳本

**以下指令假設你的工作目錄在 repo 根目錄。** `<YYYY-MM-DD>` 換成本次日期。

```bash
python portfolio-advisor/scripts/render_portfolio_report.py \
  --data outputs/portfolio/<YYYY-MM-DD>/report-data.json \
  --out-pdf outputs/portfolio/<YYYY-MM-DD>/<YYYY-MM-DD>-dashboard.pdf
```

不加 `--out-html`：腳本會自動衍生為同目錄同檔名的 `.html`（`render_portfolio_report.py` 的 `out_pdf.with_suffix('.html')`），不需要另外指定。

**降級是正常行為，不是錯誤**：若終端機找不到 Chrome/Edge，腳本會印 `[warn] 未找到 Chrome/Edge,已輸出 HTML,略過 PDF` 到 stderr，只產出 `.html`、沒有 `.pdf`，但 exit code 仍是 0——這是預期行為，**不要回報成失敗**，在下方「降級記錄」註明即可。腳本執行完會印一段 JSON（含 `pdf_exists`／`pdf_bytes`／`out_html`），用它確認實際產出了什麼，不要憑空假設。

把實際發生的降級情況（若有）記在 `final.md` 「方法學限制」小節末尾新增一句「本期產出限制」說明。

## Step 4：把終版建議 append 到 recommendations.csv

`recommendations.csv` 的欄位（首次執行、檔案不存在或為空時，先寫入這一行表頭再 append 資料列；此後**只 append，不改舊行**）：

```text
rec_id,date,ticker,sleeve,action,target_weight,current_weight,reason,exit_condition,redteam_verdict,notes
```

- `rec_id`：格式 `rec_YYYYMMDD_<TICKER>_<nn>`（`YYYYMMDD` = 本次 `report_date`；`nn` = 當天同一 ticker 的兩位數序號，從 `01` 起算，若同一天同 ticker 已有序號就往上加，避免撞號）。
- `action`：**用 `02-draft.md` 原本的 8 值動作 enum（買入/續抱/加碼/減碼/賣出/換入/換出/觀望），不要用 Step 2 為 `report-data.json` 轉換過的 schema enum**——`recommendations.csv` 是給下一次 `02-draft.md` 讀的人類可讀歷史紀錄，保留「換入」「換出」這種更精確的語意；`report-data.json` 才是給 dashboard 徽章上色用、必須套用 schema enum 的檔案。兩份檔案對同一條建議因此可能用不同的動作措辭，這是刻意設計，不是不一致的錯誤。
- `exit_condition`：對應 draft.md／redteam.md 定稿後的退出條件（等同 `report-data.json` 的 `recommendations[].exit`）。
- `redteam_verdict`：`同意`/`有保留`/`反對` 三選一，對應 Step 1 的裁決。
- `notes`：自由文字，紅隊有保留/反對而你仍採用時，在這裡摘要理由；若這條建議取代了某條更早的建議，寫明「取代 <舊 rec_id>」。

只 append「本次終版仍然主張要做」的建議（含「觀望」——觀望也是一種需要記錄的判斷，方便下次追蹤是否還在觀望同一件事）。

## Step 5：寫 `final.md` 與 `summary-short.md`

`portfolio-advisor/templates/` 目前只有 wrapper packet 與 dashboard 的模板，沒有現成的終稿 Markdown 模板，`final.md`／`summary-short.md` 的章節結構由你依下列清單自訂撰寫：

`final.md` 至少依序包含：

1. 一句話結論（同 `report-data.json` 的 `verdict_one_line`）
2. 組合狀態（sleeve 權重 vs 目標、drift、現金水位；如有 degraded 項目在此重申）
3. Core 持倉逐檔 thesis（定稿版五態 + 依據 + 失效條件）
4. 策略倉建議表（終版，含「最終決定」一欄——買或不買、目標權重多少、紅隊意見是採納還是反駁）
5. Turnover／重疊曝險檢查結果
6. ETF 穿透與公司級曝險（對應 `lookthrough`）
7. 下週事件與應對
8. 「## 紅隊審查摘要」（Step 1 產出的表格；若無紅隊審查，開頭已加警語，此節可省略或寫「本期無紅隊審查記錄」）
9. 本週使用者行動清單（對應 `user_actions`，清楚標示 owner）
10. 主要風險
11. 方法學限制與合規聲明（見 Step 6）

`summary-short.md`（精簡版，供快速瀏覽）依序包含：一句話結論／組合狀態摘要／Core 判斷摘要／策略倉動作表（終版）／紅隊審查一句話摘要／盈虧摘要／本週行動清單／主要風險／完整報告與 dashboard 的路徑。若 `redteam.md` 不存在，第一行加 `⚠️ 本期未經紅隊審查`（同 Step 1 失敗容錯）。

## Step 6：列出全部產物路徑 + 頁尾合規文字

在完成回報中列出本次執行實際產生的所有檔案（不是預期清單，是真的跑出來、你確認存在的檔案），典型情況下應包含：

```text
outputs/portfolio/<YYYY-MM-DD>/report-data.json
outputs/portfolio/<YYYY-MM-DD>/final.md
outputs/portfolio/<YYYY-MM-DD>/summary-short.md
outputs/portfolio/<YYYY-MM-DD>/<YYYY-MM-DD>-dashboard.html
outputs/portfolio/<YYYY-MM-DD>/<YYYY-MM-DD>-dashboard.pdf   （若無瀏覽器則缺席，須註明）
```

`final.md`／`summary-short.md`／`report-data.json` 的 `compliance` 欄，以及回報的最後一行，都附上：

> 本報告僅供研究與教育用途，不構成投資建議；最終決策與下單由使用者本人完成。
