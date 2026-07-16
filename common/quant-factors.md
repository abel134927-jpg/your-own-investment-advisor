# 量化因子計算指引（agent 現場以 yfinance 計算）

## 角色定位

這份指引定義的量化因子，是研究員 agent 於**執行時**用 `yfinance`（免費、無需 API key）現場計算的**研究證據之一**，用途是補強估值快照、佐證或反證主筆的判斷——**不是自動交易訊號**，不能單獨變成 buy/sell 指令，也不會有任何腳本把它寫進渲染管線。ai-weekly 與 portfolio-advisor 的研究員 prompt 都引用本檔作為唯一權威規格；改因子規格只改這一份檔案。

## 五類因子規格（每檔標的皆算）

1. **價格動能**：現價、1 週／1 月／3 月／YTD（year-to-date，年初至今）報酬率、52 週高低點位置（%，`(現價−52週低點)/(52週高點−52週低點)×100`）。史料不足以支撐該區間（例如上市未滿 1 週）就標 `MISSING`。
2. **估值**：trailing P/E、forward P/E（來自 yfinance `Ticker(ticker).info`；抓不到就標 `MISSING`，不得用其他標的的倍數推算）。
3. **波動環境**：`^VIX` 現值 + 近一月趨勢（升／降）。這是宏觀因子，一整份 packet 只算一次，不必每檔標的重複算。
4. **利率**：`^TNX`（美國 10 年期公債殖利率）現值 + 近一月變化，變化幅度以 bps（basis points，基點）或百分點表示（例如 +18bps），不能只寫升／降——利率變化的幅度對判斷有意義。同樣是宏觀因子，只算一次。
5. **週線趨勢**：現價 vs 50 日／200 日均線（站上／跌破），週線 MA10／MA20 多空排列（MA10 > MA20 記多頭排列，反之空頭排列）。**上市未滿 50／200 個交易日，或週線資料不足 20 週，均線會是 `NaN`——一律標 `MISSING`，不得把 NaN 比較的結果（一律是 False）誤植為「跌破」或「空頭排列」。**

## 簡單回測規格（portfolio 模組用）

對每檔持倉與整體組合（按現有權重加權），計算過去 1 年累積報酬 vs SPY（S&P 500 ETF，作為對照基準）、最大回撤（max drawdown）。

**必附警語（不得省略）**：

> 簡化回測：不含入金時序、稅費、滑價；含存活者偏差；過去績效不代表未來。

## Python 範例片段（yfinance 抓價、算報酬／均線／回撤，可直接執行）

單檔查詢遇到例外（網路逾時、限流、ticker 不存在）一律回傳 `MISSING`，**不中斷迴圈**；均線/週線因史料不足產生 `NaN` 時同樣標 `MISSING`，不得把 NaN 比較的結果誤植為「跌破」或「空頭排列」（`price > NaN` 在 Python 永遠是 `False`，靜默就會變成捏造的「跌破」標籤）；`.info`（PE 來源）獨立包一層 try/except，抓不到只讓 PE 兩欄標 `MISSING`，不影響同一檔已算出的其他欄位：

```python
import yfinance as yf

def factor_snapshot(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="1y")["Close"]
    except Exception as e:
        return {"ticker": ticker, "error": f"MISSING - fetch failed: {e}"}
    if hist.empty:
        return {"ticker": ticker, "error": "MISSING - no price history"}
    price = hist.iloc[-1]
    def ret(days):
        return round((price / hist.iloc[-days-1] - 1) * 100, 2) if len(hist) > days else "MISSING"
    def ma_stance(window):
        if len(hist) < window:
            return "MISSING"  # 史料不足，不可用 NaN 比較結果當成「跌破」
        return "站上" if price > hist.rolling(window).mean().iloc[-1] else "跌破"
    weekly = hist.resample("W").last()
    if len(weekly) < 20:
        weekly_stance = "MISSING"
    else:
        wma10, wma20 = weekly.rolling(10).mean().iloc[-1], weekly.rolling(20).mean().iloc[-1]
        weekly_stance = "多頭排列" if wma10 > wma20 else "空頭排列"
    ytd = hist[hist.index.year == hist.index[-1].year]
    try:
        info = yf.Ticker(ticker).info or {}
        pe_trailing, pe_forward = info.get("trailingPE", "MISSING"), info.get("forwardPE", "MISSING")
    except Exception:
        pe_trailing = pe_forward = "MISSING"  # info 抓取失敗只影響 PE，不丟棄其他已算出的欄位
    return {
        "price": round(price, 2),
        "ret_1w": ret(5), "ret_1m": ret(21), "ret_3m": ret(63),
        "ret_ytd": round((price / ytd.iloc[0] - 1) * 100, 2) if len(ytd) > 1 else "MISSING",
        "pos_52w_pct": round((price - hist.min()) / (hist.max() - hist.min()) * 100, 1) if len(hist) > 1 else "MISSING",
        "pe_trailing": pe_trailing, "pe_forward": pe_forward,
        "vs_ma50": ma_stance(50), "vs_ma200": ma_stance(200),
        "weekly_ma_stance": weekly_stance,
    }

def backtest_vs_benchmark(ticker, benchmark="SPY", period="1y"):
    try:
        px = yf.Ticker(ticker).history(period=period)["Close"]
        bench = yf.Ticker(benchmark).history(period=period)["Close"]
    except Exception as e:
        return {"ticker": ticker, "error": f"MISSING - fetch failed: {e}"}
    if px.empty or bench.empty:
        return {"ticker": ticker, "error": "MISSING - no price history"}
    cum_ret = round((px.iloc[-1] / px.iloc[0] - 1) * 100, 2)
    bench_ret = round((bench.iloc[-1] / bench.iloc[0] - 1) * 100, 2)
    drawdown = (px - px.cummax()) / px.cummax()
    return {"cum_return_pct": cum_ret, "vs_spy_pct": round(cum_ret - bench_ret, 2),
            "max_drawdown_pct": round(drawdown.min() * 100, 2)}

def macro_change_bps(ticker):
    """^TNX 的月變化幅度換算成 bps；^VIX 不需要這個，維持升/降 + 現值即可。"""
    try:
        hist = yf.Ticker(ticker).history(period="2mo")["Close"]
    except Exception:
        return "MISSING"
    if len(hist) < 22:
        return "MISSING"
    return round((hist.iloc[-1] - hist.iloc[-22]) * 100, 1)  # ^TNX 現值本身是百分比，乘 100 換算成 bps

# 用法：改 ticker 直接照抄，單檔失敗只讓該檔標 MISSING，繼續下一檔。
for tk in ["NVDA", "^VIX", "^TNX"]:
    print(tk, factor_snapshot(tk))
print("^TNX 近一月變化(bps):", macro_change_bps("^TNX"))
print("VOO vs SPY:", backtest_vs_benchmark("VOO"))
```

**組合級回測**（每檔持倉 + 組合整體，按現有權重加權）：多檔標的的價格序列起始日不一定相同（例如某檔較晚上市），必須先對齊共同起始日再合成，否則加權淨值曲線會失真；`normalized = df / df.iloc[0]` 是「再基準化」——每檔都從 1.0 起算，才能直接乘權重加總，這兩點是新手最容易漏掉的地方。單檔抓價失敗（限流、ticker 不存在）該檔剔除、剩餘權重重新歸一化，`excluded` 欄位如實列出；基準（SPY）的比較窗口必須對齊組合實際回測起點（`window_start`），不能用未截斷的整個 period 去跟被截斷過的組合序列比報酬：

```python
import pandas as pd

def portfolio_backtest(weights, benchmark="SPY", period="1y"):
    # weights 例：{"VOO": 0.4, "QQQ": 0.3, "NVDA": 0.3}（現有持倉權重，依 holdings 實際權重填）
    prices, excluded = {}, []
    for tk in weights:
        try:
            h = yf.Ticker(tk).history(period=period)["Close"]
        except Exception:
            h = None
        if h is None or h.empty:
            excluded.append(tk)  # 抓價失敗或無資料，該檔剔除，不讓整個組合回測 traceback
        else:
            prices[tk] = h
    if not prices:
        return {"error": "MISSING - no usable holdings", "excluded": excluded}
    df = pd.DataFrame(prices).dropna()  # 對齊共同起始日：只保留所有納入標的都有價格的交易日
    if df.empty:
        return {"error": "MISSING - no overlapping price history", "excluded": excluded}
    kept = {tk: w for tk, w in weights.items() if tk in df.columns}
    norm_weights = {tk: w / sum(kept.values()) for tk, w in kept.items()}  # 剔除檔位後權重重新歸一化
    normalized = df / df.iloc[0]  # 再基準化：每檔都從 1.0 起算，才能加權合成
    nav = (normalized * pd.Series(norm_weights)).sum(axis=1)
    cum_ret = round((nav.iloc[-1] / nav.iloc[0] - 1) * 100, 2)
    drawdown = (nav - nav.cummax()) / nav.cummax()
    result = {
        "portfolio_cum_return_pct": cum_ret,
        "max_drawdown_pct": round(drawdown.min() * 100, 2),
        "window_start": str(df.index[0].date()),  # 實際回測起點：可能因對齊/剔除而晚於 period 起點
        "excluded": excluded,
    }
    try:
        bench = yf.Ticker(benchmark).history(period=period)["Close"]
        bench = bench.reindex(df.index).dropna()  # 對齊到組合實際回測窗口，避免跟不同時間窗比較
        if bench.empty:
            raise ValueError("no overlapping benchmark data")
        bench_ret = round((bench.iloc[-1] / bench.iloc[0] - 1) * 100, 2)
        result["vs_spy_pct"] = round(cum_ret - bench_ret, 2)
    except Exception:
        result["vs_spy_pct"] = "MISSING"  # benchmark 抓取失敗，組合自身數字仍照常輸出
    return result

print(portfolio_backtest({"VOO": 0.4, "QQQ": 0.3, "NVDA": 0.3}))
```

## Degraded 規則

- `pip install yfinance` 失敗：整段量化因子標記 degraded，在報告中如實註明「yfinance 安裝失敗，本段量化因子未計算」，**不可腦補數字頂替**，不可讓這件事卡住整個研究流程。
- 個別欄位抓不到（例如某檔沒有 forward PE、`info` 回傳空字典）：該欄位標 `MISSING`，其餘欄位照常填。
- **單檔查詢遇到例外或 traceback**（網路逾時、限流、ticker 打錯或不存在）：該檔全部欄位標 `MISSING`，繼續處理下一檔，**不得中斷整個研究流程**，也不得把原始 traceback 貼進最終報告——只留一句「查詢失敗」的說明即可。
- **均線／週線因史料不足產生 `NaN`**（例如標的上市未滿 200 個交易日）：該欄位標 `MISSING`，不得把 NaN 比較的結果（恆為 False）誤植為「跌破」或「空頭排列」。
- **組合級回測單檔抓價失敗**：該檔剔除出組合、其餘持倉權重重新歸一化後才計算，並在結果的 `excluded` 欄位如實列出被剔除的標的；`window_start`（實際回測起點）可能因對齊/剔除而晚於原本要求的 period 起點，寫進報告時要照實際 `window_start` 標注，不能寫成「過去 1 年」卻其實是截斷後的較短窗口。基準（SPY）抓不到時，組合自身的報酬／回撤數字仍照常輸出，`vs SPY` 欄位標 `MISSING` 即可，不必因為基準缺資料就整段放棄。
- 完全不可用時（例如環境完全沒有網路存取 yfinance 的資料源）：退回 WebSearch 查現值，並在該欄位註明來源與查詢時間點（as-of），不得沿用舊值或用其他標的推算。

## 輸出格式：markdown 因子表

每檔標的一列：

| ticker | 現價 | 1週報酬 | 1月報酬 | 3月報酬 | YTD報酬 | 52週高低位置(%) | trailing PE | forward PE | 現價 vs 50日均線 | 現價 vs 200日均線 | 週線 MA10/MA20 排列 | as-of |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

宏觀因子（整份 packet 只算一次，不隨標的重複）：

| 指標 | 現值 | 近一月趨勢 | 近一月數值變化 | as-of |
|---|---|---|---|---|
| ^VIX | | 升／降 | （選填，維持升/降＋現值即可） | |
| ^TNX（美國10年期殖利率） | | 升／降 | 以 bps 或百分點表示，例如 +18bps | |

簡單回測表（portfolio 模組用；每檔持倉一列 + 一列組合整體）：

| ticker/組合 | 過去1年累積報酬 | vs SPY 累積報酬 | 最大回撤 | as-of |
|---|---|---|---|---|

（回測表下方必附「簡單回測規格」一節列出的警語原文，不得省略。）
