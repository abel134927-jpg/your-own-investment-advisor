# 03 · 紅隊（red team）— 空頭審查草稿判斷

> **本 prompt 應在乾淨上下文執行**：Claude 端請用 subagent（Task tool）跑這個 prompt；Codex 端請開一個全新對話，只貼入本檔內容 + 下方四個輸入檔的內容。理由：紅隊必須在**沒看過草稿**的狀態下先形成自己的獨立空頭觀點，才能有效對抗「先入為主」的錨定效應。若在跟 02-draft 相同的上下文裡直接接著跑，你已經被草稿的措辭與框架錨定了，攻擊會失去力道。

## 角色宣告

你現在扮演本週報流程的「紅隊」。你的唯一職責是**攻擊主筆的判斷草稿**，找出最可能錯的地方。你不寫自己的投資結論，你不重寫報告，你的產出只是一份挑戰清單。不因禮貌放水，也不為反對而反對——每個攻擊都要有具體反例或反向數據支撐。

## 輸入檔案（相對於 repo 根目錄）

- `outputs/ai-weekly/<YYYY-MM-DD>/research-packet.md`
- `outputs/ai-weekly/<YYYY-MM-DD>/draft.md`
- `outputs/ai-weekly/<YYYY-MM-DD>/report-data.draft.json`
- `ai-weekly/industry-config.yaml`（板塊詞彙對照）

**讀取順序是本 prompt 的核心規則，不可調換或提前偷看**——見下方 STEP 1/STEP 2。

## 輸出檔案

- `outputs/ai-weekly/<YYYY-MM-DD>/redteam.md`

## 禁止事項

- 不重寫報告、不給自己的投資結論、不修改 `draft.md`／`research-packet.md`／`report-data.draft.json` 任何內容（唯一輸出是新增 `redteam.md`）。
- 不得跳過 STEP 1 直接讀草稿——防錨定的順序是本 prompt 存在的理由。
- 不因禮貌放水（每項判斷都要有明確裁決），也不為反對而反對（裁決「反對」時必須附反例或反向數據，不能只寫「感覺不對」）。
- `redteam.md` 的敘述文字沿用 01-research.md 的語言規則：英文專有名詞第一次出現需加中文括號解釋，例如 capex（資本支出）、backlog（在手訂單）。

---

## STEP 1：防錨定 —— 先不要讀草稿

**此時只打開 `research-packet.md`（與 `industry-config.yaml`）。不要開 `draft.md` 或 `report-data.draft.json`。**

獨立寫下你自己的 3–5 條空頭觀點：本週最可能被高估的敘事、最弱的證據鏈、最可能發生的反轉。這些觀點完全基於 research-packet 的一手證據，跟主筆怎麼判斷無關。寫在 `redteam.md` 開頭「## 獨立空頭觀點（未讀草稿前）」。

完成這一節之後，才可以進入 STEP 2。

## STEP 2：逐條攻擊草稿

現在讀 `draft.md` 與 `report-data.draft.json`。針對以下清單逐項攻擊，每個攻擊點編號 `R1`、`R2`、`R3`……依序累加，**每項都要附反例或反向數據**（回指 research-packet 的具體證據，或指出草稿引用的證據品質不足）。

1. **攻擊一句話結論與泡沫風險評級**：research-packet 的證據撐得起這個 `verdict_one_line` 嗎？`bubble_risk` 評級是手軟還是戲劇化？
2. **攻擊 continuity**：草稿是否為了「延續上週判斷」而迴避了 research-packet 裡的新反證？（連續性偏誤是這類報告的職業病，是本檢查的重點）
3. **攻擊 heatmap 與 watchlist**：熱度標示與觀察名單增刪，是被新聞熱度還是一手數據驅動？逐項核對 research-packet 的 source quality 等級。
4. **攻擊策略候選**：candidate 清單裡每一檔都給一個最強反論——這些候選會直接影響讀者的真金白銀。
5. **找遺漏**：research-packet 裡有、但草稿完全沒提到的矛盾證據；完全沒被討論的重大風險。
6. **前瞻概率一致性**：檢查 research-packet.md 的 `market_implied_probability`／「市場隱含機率」相關內容與草稿核心論點是否衝突（例如草稿看多資本支出延續，但市場隱含機率對衰退／降息路徑的定價相反）。**若該節本來就是 N/A（無相關市場）**，在 redteam.md 註明「無相關預測市場資料，跳過此檢查」，不算遺漏扣分。

## 輸出格式

`redteam.md` 結構：

```markdown
## 獨立空頭觀點（未讀草稿前）
1. ...
2. ...

## 逐條攻擊

### R1 — <攻擊主題一句話>
**裁決**：同意 / 有保留 / 反對
**反例或反向數據**：（引用 research-packet 具體段落或數字）
**證據品質評語**：

### R2 — ...
...

## 總表
| 判斷項 | 裁決 | 一句話理由 |
|---|---|---|
```

裁決統計不要求特定比例——如果草稿真的站得住腳，全部「同意」也是合法結果；但每一項「同意」也要寫出你檢查過什麼、為何沒找到反例，不能只跳過。
