#!/usr/bin/env python3
"""Render report-data.json into a readable archive PDF using Chrome + system CJK fonts.

Important: This is optimized for opening/reading reliably on Windows/macOS.
Do NOT use ReportLab CID fonts here: Windows PDF viewers may ask to download
Traditional Chinese language packs or render garbled text.

Search/index source of truth remains Markdown + report-data.json. PDF is a view.
"""
from __future__ import annotations
import argparse, html, json, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from render_env import find_browser


def e(x):
    return html.escape(str(x or ""))


# Conservative fallback translation for KNOWN recurring English taxonomy labels
# that the LLM sometimes emits despite language rules. Exact-match only; applied
# solely to structured taxonomy render sites (heatmap position/segment, valuation
# segment, strongest/watch tiles). Free-text fields are never touched.
LABELS = {
    # --- segment taxonomy ---
    "HBM / Memory": "HBM／記憶體",
    "Optical / Networking": "光通訊／網路",
    "Power / Grid / Cooling": "電力／電網／散熱",
    "Hyperscaler cloud AI": "超大規模雲端 AI",
    "GPU / Custom silicon": "GPU／自研晶片",
    "AI app monetization": "AI 應用變現",
    "GPU / AI platform": "GPU／AI 平台",
    "AI apps / monetization": "AI 應用／變現",
    "AI app stories without audited monetization": "AI 應用故事（缺乏經審計變現）",
    # --- position taxonomy ---
    "Overweight but evidence-downgraded": "超配但證據降級",
    "Overweight but no chasing": "超配但不追高",
    "Overweight but valuation discipline": "超配但守估值紀律",
    "Overweight but avoid chasing": "超配但避免追高",
    "Overweight structural bottleneck": "超配（結構性瓶頸）",
    "Structural bottleneck, vendor-bias adjusted": "結構性瓶頸（已調整供應商偏差）",
    "Selective / cash-flow tested": "精選／現金流檢驗",
    "Selective": "精選",
    "Underweight / proof required": "低配／待證明",
    "Underweight / caution": "低配／謹慎",
    # --- single-word positions (defensive) ---
    "Overweight": "超配",
    "Underweight": "低配",
    "Neutral": "中性",
}
_LABELS_CI = {k.lower(): v for k, v in LABELS.items()}


def localize_label(s):
    """Exact-match localization for known recurring taxonomy labels.

    Strip + exact match (case-sensitive first, then case-insensitive fallback).
    Returns the original value unchanged when there is no match.
    """
    key = str(s).strip()
    if key in LABELS:
        return LABELS[key]
    return _LABELS_CI.get(key.lower(), s)


def ul(items):
    return '<ul>' + ''.join(f'<li>{e(x)}</li>' for x in (items or [])) + '</ul>'


def rows(items, cols, loc_cols=()):
    def cell(item, c):
        v = item.get(c, "")
        if c in loc_cols:
            v = localize_label(v)
        return f'<td>{e(v)}</td>'
    return ''.join('<tr>' + ''.join(cell(item, c) for c in cols) + '</tr>' for item in items)


def render_pdf(html_path: Path, pdf_path: Path, browser: str):
    # headless Chrome 對 --print-to-pdf 的相對路徑解析基準不是呼叫端 cwd,
    # 傳相對路徑會靜默寫檔失敗(returncode 仍是 0);先 resolve 成絕對路徑。
    pdf_path = pdf_path.resolve()
    subprocess.run([
        browser,
        '--headless', '--disable-gpu', '--no-pdf-header-footer',
        '--allow-file-access-from-files',
        f'--print-to-pdf={pdf_path}',
        html_path.resolve().as_uri(),
    ], check=True)


def render_html(d):
    dash = d['dashboard']; w = d['watchlist']; f = d['final']; s = d['sources']
    heat = rows(d['heatmap'], ['position','segment','heat_level','signal','tickers'], loc_cols=('position','segment'))
    cont = rows(d['continuity'], ['prior_view','status','evidence','thesis_updated'])
    events = rows(d.get('events', []), ['category','date','headline','why','impact'])
    val = rows(d['valuation']['rows'], ['segment','support','risk_reward','conclusion'], loc_cols=('segment',))
    blue = ''.join(f"<li><b>{e(x['claim'])}</b> — {e(x['evidence'])} <code>{e(x.get('strength',''))}</code></li>" for x in d['debate']['blue'])
    red = ''.join(f"<li><b>{e(x['claim'])}</b> — {e(x['evidence'])} <code>{e(x.get('strength',''))}</code></li>" for x in d['debate']['red'])

    # Use system CJK fonts. Avoid CID fonts and remote Google fonts.
    css = '''
@page { size: A4; margin: 15mm 14mm; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Microsoft JhengHei", "Microsoft YaHei", "Noto Sans TC", "Noto Sans CJK TC", Arial, sans-serif;
  font-size: 11.5px; line-height: 1.62; color: #111827;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1 { font-size: 26px; border-bottom: 2px solid #111827; padding-bottom: 8px; margin: 0 0 12px; }
h2 { font-size: 18px; margin-top: 22px; margin-bottom: 8px; border-left: 4px solid #2F5FE0; padding-left: 8px; page-break-after: avoid; }
h3 { font-size: 14px; color: #2F5FE0; margin: 12px 0 5px; }
p { margin: 5px 0; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 14px; page-break-inside: avoid; }
th, td { border: 1px solid #d8dde6; padding: 6px 7px; vertical-align: top; }
th { background: #eef1f5; text-align: left; color: #33405A; }
blockquote { border-left: 4px solid #2F5FE0; background: #f2f5fd; padding: 8px 12px; margin: 8px 0; }
code { font-family: Consolas, monospace; background: #eef1f5; padding: 1px 4px; border-radius: 3px; }
ul, ol { margin-top: 5px; margin-bottom: 10px; }
li { margin-bottom: 4px; }
.meta { font-family: Consolas, monospace; font-size: 9px; color: #6b7280; text-align: right; margin-bottom: 8px; }
.disclaimer { background: #fcf3f3; border: 1px solid #f1d5d6; padding: 10px; margin-top: 16px; }
'''
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>AI 產業鏈週報 {e(d['date'])} archive</title><style>{css}</style></head><body>
<div class="meta">AI 產業鏈週報 · Value Chain Weekly · {e(d['date'])} · 存檔版 · 研究與教育用途，不構成投資建議</div>
<h1>AI 產業鏈週報 · {e(d['issue'])}</h1>
<blockquote><b>本週一句話判斷：</b>{e(d['verdict_one_line'])}</blockquote>

<h2>01 執行摘要</h2>
<table><tr><th>儀表</th><th>讀數</th><th>理由</th></tr>
<tr><td>AI 基本面</td><td>{e(dash['fundamentals_status'])}</td><td>{e(dash['fundamentals_note'])}</td></tr>
<tr><td>估值狀態</td><td>{e(dash['valuation_status'])}</td><td>{e(dash['valuation_note'])}</td></tr>
<tr><td>泡沫風險</td><td>{e(dash['bubble_risk'])}</td><td>{e(dash['bubble_note'])}</td></tr>
<tr><td>最強板塊</td><td>{e(localize_label(dash['strongest_segment']))}</td><td>{e(dash['strongest_note'])}</td></tr>
<tr><td>最需警戒</td><td>{e(localize_label(dash['watch_segment']))}</td><td>{e(dash['watch_note'])}</td></tr></table>
<p><b>本週反共識：</b>{e(dash['contrarian_view'])}</p>

<h2>02 AI 產業鏈熱力圖</h2>
<table><tr><th>位置</th><th>板塊</th><th>熱度</th><th>訊號</th><th>代表</th></tr>{heat}</table>

<h2>03 與上週判斷的延續 / 修正</h2>
<table><tr><th>上週判斷</th><th>本週狀態</th><th>證據</th><th>Thesis 更新</th></tr>{cont}</table>
<p><b>規則：</b>Thesis 只能因新事實或明確反證改變；單週股價波動只能影響估值狀態或風險報酬。</p>

<h2>04 本週重大事件</h2>
<table><tr><th>類別</th><th>日期</th><th>事件</th><th>重要性</th><th>影響</th></tr>{events}</table>

<h2>05 藍隊 vs 紅隊</h2>
<h3>藍隊</h3><ol>{blue}</ol>
<h3>紅隊</h3><ol>{red}</ol>
<p><b>淨傾向：</b>藍隊 {e(d['debate'].get('net_tilt_blue',50))} / 紅隊 {100-int(d['debate'].get('net_tilt_blue',50))}</p>

<h2>06 估值檢查</h2>
<table><tr><th>板塊</th><th>基本面是否支持估值</th><th>風險報酬</th><th>結論</th></tr>{val}</table>

<h2>07 需求真實性檢查</h2>
<h3>誰正在賺錢</h3>{ul(d['demand'].get('earning',[]))}
<h3>誰仍在燒錢</h3>{ul(d['demand'].get('burning',[]))}
<p><b>CAPEX 是否可持續：</b>{e(d['demand'].get('capex'))}</p>
<p><b>AI 應用是否真的變現：</b>{e(d['demand'].get('monetization'))}</p>

<h2>08 Watchlist 四象限</h2>
<h3>核心長期</h3>{ul(w.get('core',[]))}
<h3>等待回調</h3>{ul(w.get('pullback',[]))}
<h3>預期差</h3>{ul(w.get('mispriced',[]))}
<h3>過熱警戒</h3>{ul(w.get('overheated',[]))}

<h2>09 最終判斷</h2>
<p><b>我現在相信什麼：</b>{e(f.get('believe'))}</p>
<p><b>我懷疑什麼：</b>{e(f.get('doubt'))}</p>
<p><b>市場可能錯估哪裡：</b>{e(f.get('market_mispricing'))}</p>
<p><b>如果我錯了：</b>{e(f.get('if_wrong'))}</p>
<h3>下週觀察信號</h3>{ul(f.get('signals',[]))}
<blockquote>{e(f.get('short'))}</blockquote>

<h2>10 資料來源與聲明</h2>
<h3>一手 / 硬數據</h3>{ul(s.get('hard',[]))}
<h3>觀點來源</h3>{ul(s.get('opinion',[]))}
<h3>市場隱含 / 輔助來源</h3>{ul(s.get('market',[]))}
<div class="disclaimer">本報告為可分享之投資研究筆記，僅供資訊與教育用途，不構成任何證券之買賣建議或投資邀約。所有判斷可能出錯；讀者應自行進行盡職調查並為自身決策負責。</div>
</body></html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out-dir')
    ap.add_argument('--no-pdf', action='store_true')
    args = ap.parse_args()
    data_path = Path(args.data)
    d = json.loads(data_path.read_text(encoding='utf-8'))
    out_dir = Path(args.out_dir) if args.out_dir else data_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / f"{d['date']}-archive.html"
    pdf_path = out_dir / f"{d['date']}-archive.pdf"
    # Backward-compatible name: replace old problematic searchable.pdf with readable archive PDF.
    compat_pdf = out_dir / f"{d['date']}-searchable.pdf"
    html_path.write_text(render_html(d), encoding='utf-8')
    if not args.no_pdf:
        browser = find_browser()
        if browser:
            render_pdf(html_path, pdf_path, browser)
            shutil.copy2(pdf_path, compat_pdf)
        else:
            print('[warn] 未找到 Chrome/Edge,已輸出 HTML,略過 PDF', file=sys.stderr)
    print(json.dumps({'html': str(html_path), 'pdf': str(pdf_path), 'compat_pdf': str(compat_pdf), 'pdf_exists': pdf_path.exists()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
