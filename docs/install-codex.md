# 安裝指南：Codex（桌面版 / CLI）

本 repo 給 Codex 端的入口是根目錄的 [`AGENTS.md`](../AGENTS.md)。Codex 開啟這個資料夾時會自動讀取 `AGENTS.md` 作為操作指南，你不需要手動貼給它。

## 前置需求

- **Python 3.10 以上**：跑渲染腳本用。
- **Chrome 或 Edge（選用）**：用來把 HTML 報告轉成可搜尋 PDF；沒有的話自動降級成只出 HTML，不是錯誤。
- 這兩項一樣不需要你自己動手：對 Codex 說「讀 README 幫我完成安裝」，它會依 `AGENTS.md` 各模組「② 首次使用 onboarding」的 Step 1（環境自檢）自己跑 `python --version`、`pip install -r requirements.txt`、檢查瀏覽器路徑。若系統根本沒裝 Python，Codex 會請你自行安裝直譯器本身，這一步無法代勞。

## 開啟 repo

1. `git clone` 這個 repo 到本機任一資料夾，或下載 zip 解壓縮。
2. 用 Codex 桌面版或 CLI（`codex` 指令）在這個資料夾底下開啟一個對話 / session（CLI 直接在該資料夾執行 `codex`）。
3. Codex 會自動讀取根目錄的 `AGENTS.md` 作為這個 repo 的操作指南——裡面已經寫清楚兩個模組（`ai-weekly`、`portfolio-advisor`）各自的觸發語、onboarding 步驟、四段執行順序與檔案交接規則。
4. 對 Codex 說「讀 README 幫我完成安裝」，它會依 `AGENTS.md` 對應模組的「② 首次使用 onboarding」自己走完環境自檢 → smoke test，並視你的需求詢問要不要客製產業或建立你的持倉帳本。

## 紅隊必須開新對話

兩個模組的第 3 段（紅隊）都要求在**完全沒看過主對話草稿與推理過程**的狀態下獨立形成空頭觀點，`AGENTS.md` 對應章節（④）已明講操作方式：**開一個全新對話**，不是接著目前這個對話問下去。新對話只貼入以下內容，不可以夾帶主對話目前為止的討論或你對草稿的想法：

**ai-weekly 紅隊（新對話只貼這四份檔案 + prompt，共 5 項）**：

1. `ai-weekly/prompts/03-redteam.md` 的完整內容
2. `outputs/ai-weekly/<date>/research-packet.md`
3. `outputs/ai-weekly/<date>/draft.md`
4. `outputs/ai-weekly/<date>/report-data.draft.json`
5. `ai-weekly/industry-config.yaml`

（四份檔案裡，`research-packet.md`／`draft.md`／`report-data.draft.json` 三份是本次執行產出的檔案；`industry-config.yaml` 是既有的產業設定檔——本來就存在，不是這次執行才產生的——一併貼入是為了讓紅隊知道目前追蹤的產業板塊定義。）

**portfolio-advisor 紅隊（新對話只貼這四份檔案 + prompt）**：

1. `portfolio-advisor/prompts/03-redteam.md` 的完整內容
2. `outputs/portfolio/<date>/packet.md`
3. `outputs/portfolio/<date>/draft.md`
4. `portfolio-advisor/portfolio/portfolio-config.yaml`
5. `portfolio-advisor/portfolio/investment-policy.md`

新對話產出 `redteam.md` 存回對應的 `outputs/` 日期資料夾後，回到（或再開）原本的對話，帶著 `redteam.md` 繼續第 4 段（主筆定稿）。完整規則見 `AGENTS.md` 兩個模組各自的「④ 紅隊必須開新對話」章節。

## 前置需求與常見問題

Python / 瀏覽器前置需求、常見安裝問題（`python` 指令找不到、`pip install` 失敗、找不到 Chrome/Edge 導致沒有 PDF、CJK 字型缺字）與 [`docs/install-claude.md`](install-claude.md) 的「常見安裝問題」一節完全通用，不分 Claude 或 Codex，直接參照該節即可。
