# 安裝指南：Claude（Cowork / Claude Code）

本 repo 給 Claude 端的入口是 [`skills/ai-weekly/SKILL.md`](../skills/ai-weekly/SKILL.md) 與 [`skills/portfolio-advisor/SKILL.md`](../skills/portfolio-advisor/SKILL.md)。你不需要自己讀完整份 SKILL.md 才能開始——把 repo 交給 agent、說一句「讀 README 幫我完成安裝」，agent 會自己去讀對應的 SKILL.md 並照著 onboarding 步驟做。這份文件補的是「桌面環境要先設定什麼，agent 才連得上這個 repo」。

## 前置需求

- **Python 3.10 以上**：跑渲染腳本用。
- **Chrome 或 Edge（選用）**：用來把 HTML 報告轉成可搜尋 PDF。沒有的話系統會自動降級成只出 HTML，不是錯誤。
- 以上兩項都不需要你自己手動裝：一旦你對 agent 說「讀 README 幫我完成安裝」，agent 會依 SKILL.md 的 Step 1（環境自檢）自己檢查 Python 版本、跑 `pip install -r requirements.txt`（安裝 `pillow` + `pyyaml`）、檢查瀏覽器是否存在。如果 Python 本身沒裝，agent 會告訴你去裝 Python（例如從 [python.org](https://www.python.org/) 或系統的套件管理員），這一步無法代勞。

## 路徑一：Claude Cowork

1. **把 repo 資料夾加入 Cowork**：在 Cowork 裡新增這個 repo 所在的資料夾為工作目錄（`git clone` 下來的資料夾，或解壓縮 zip 後的資料夾）。
2. **確認檔案與命令權限**：到 Cowork 的 Settings 裡確認這個工作目錄有檔案讀寫權限、以及執行 shell 指令（跑 `python ...` 腳本）的權限。沒有開這兩項，agent 沒辦法跑渲染腳本或寫入 `outputs/`。
3. **skills 自動發現**：`skills/ai-weekly/SKILL.md` 與 `skills/portfolio-advisor/SKILL.md` 各自的檔頭都有 `description` 欄位，Cowork 會依你的訊息內容自動判斷要不要載入對應 skill——你不需要手動指定，直接照 README「快速開始」講觸發語即可（例如「跑本週週報」「初始化我的投資組合」）。若 skill 未被自動載入，直接對 agent 說「讀 `skills/ai-weekly/SKILL.md` 照著做」即可，功能完全相同。
4. 第一次使用，直接說「讀 README 幫我完成安裝」，agent 會自己找到對應 SKILL.md 走完 onboarding（環境自檢 → smoke test → 依你的需求決定要不要換產業 / 建帳本）。

## 路徑二：Claude Code

1. `git clone` 這個 repo 到本機任一資料夾，或下載 zip 解壓縮。
2. 用 Claude Code 開啟這個資料夾，**信任該資料夾**（Claude Code 第一次開啟新專案時會詢問是否信任，選是）。
3. 直接對 Claude 說「讀 README 完成安裝」。Claude Code 會讀 `skills/*/SKILL.md`，依裡面的 onboarding 步驟自己跑環境自檢與 smoke test。
4. 之後日常使用就對 Claude 說觸發語（見 README「兩個模組」一節），不需要每次都重跑 onboarding。

## 常見安裝問題

- **`python` 指令找不到**：改試 `python3`。Windows 上有時要用 `py`。若三者都沒有，代表系統沒裝 Python，需自行安裝（agent 無法代裝直譯器本身）。
- **`pip install` 失敗（權限或網路問題）**：試著加 `--user`，或確認虛擬環境已啟用；純內網/防火牆環境可能需要你自行處理套件鏡像。
- **找不到 Chrome/Edge，PDF 沒有產出**：這是正常降級，不是安裝失敗——`outputs/` 底下仍會有完整的 `.html` 報告，可以直接用瀏覽器打開。若想要 PDF，安裝 Chrome 或 Edge 後重跑即可。
- **Cowork 說沒有權限執行指令**：回到 Settings 確認該工作目錄的檔案與命令權限都已開啟（見上方路徑一 Step 2）。
- **中文字在圖表裡顯示異常（缺字/方框）**：系統找不到 CJK 字型時仍會正常產出圖表，只是字型退回預設字型，不影響報告完整性，可自行安裝 CJK 字型（如 Noto Sans TC）改善顯示。
