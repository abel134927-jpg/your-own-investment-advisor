#!/usr/bin/env python3
"""Render AI Industry Chain Weekly report-data.json into 10-page dashboard HTML/PDF.

Usage:
  python render_report.py --data <report-data.json> --out-dir <reports/ai-industry-chain-weekly>

Requires Chrome/Edge for PDF output on Windows.
"""
from __future__ import annotations

import argparse, html, json, os, subprocess, sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from render_env import find_browser


def e(x) -> str:
    return html.escape(str(x or ""))


# Conservative fallback translation for KNOWN recurring English taxonomy labels
# that the LLM sometimes emits despite language rules. Exact-match only; applied
# solely to structured taxonomy render sites (heatmap position/segment, valuation
# segment, chain-heat strip, strongest/watch tiles). Free-text fields are never
# touched — those are fixed at content generation, not here.
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
# 正規化(strip+lower)後的查找表,比對一律大小寫不敏感;中文譯名(value)維持原樣未動。
_LABEL_MAP = {k.strip().lower(): v for k, v in LABELS.items()}


def load_industry_config(path: Path) -> dict:
    """讀取 industry-config.yaml;找不到檔案回傳空 dict,YAML 格式錯誤時印警告並回傳
    空 dict(呼叫端因此套用內建預設值,不中斷渲染)。"""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        print("[warn] industry-config.yaml 解析失敗,改用內建預設板塊", file=sys.stderr)
        return {}


_REPORT_TITLE = "AI 產業鏈週報"
_INDUSTRY_NAME_ZH = "AI 產業鏈"


def apply_industry_title(config: dict) -> None:
    """以 --industry-config 的 industry.name_zh 覆蓋預設報告標題(格式:{name_zh}週報)。

    用於封面、page-header、<title> 等顯示字串。同時保留原始 name_zh(不含「週報」後綴)
    供封面副標「{name_zh} · 本週論點狀態」、第 02 頁節名「{name_zh}熱力圖」等場景組字使用。
    找不到 config 或缺 name_zh 時,維持預設「AI 產業鏈週報」/「AI 產業鏈」不變(fallback)。
    """
    global _REPORT_TITLE, _INDUSTRY_NAME_ZH
    name_zh = (config or {}).get("industry", {}).get("name_zh")
    if name_zh:
        _REPORT_TITLE = f"{name_zh}週報"
        _INDUSTRY_NAME_ZH = name_zh


def apply_industry_config_labels(config: dict) -> None:
    """以 --industry-config 的 segments 生成 en→zh 對照覆蓋預設 LABELS(大小寫不敏感)。

    en 鍵值一律 strip+lower 正規化後比對,report-data.json 內不論用哪種大小寫
    (含舊版殘留的 "Hyperscaler cloud AI" 等寫法)都能命中 config 覆蓋值;
    未被 config 涵蓋的既有 LABELS 條目(如 position 分類)保留作為 fallback。
    找不到 config 或無 segments 時,查找表維持預設值不變。
    """
    global _LABEL_MAP
    segments = (config or {}).get("segments") or []
    overrides = {
        s["en"].strip().lower(): s["zh"]
        for s in segments
        if s.get("en") and s.get("zh")
    }
    if overrides:
        _LABEL_MAP = {**_LABEL_MAP, **overrides}


def localize_label(s) -> str:
    """Case-insensitive exact-match localization for known recurring taxonomy labels.

    Strip + lower 正規化後比對 _LABEL_MAP。找不到則回傳原值不變。
    """
    key = str(s).strip().lower()
    return _LABEL_MAP.get(key, s)


def badge_class(text: str) -> str:
    text = str(text)
    if any(k in text for k in ["破壞", "推翻", "過熱", "警戒", "高", "risk", "危險", "惡化"]):
        return "risk"
    if any(k in text for k in ["削弱", "偏貴", "中", "等待", "部分", "昂貴", "轉弱"]):
        return "warn"
    if any(k in text for k in ["強化", "未破壞", "穩健", "核心", "可持有", "低", "便宜"]):
        return "ok"
    return "info"


def heat_label(n: int) -> str:
    return {1: "冷", 2: "偏冷", 3: "中性", 4: "偏熱", 5: "過熱"}.get(int(n), "中性")


def heat_color(n: int) -> str:
    return {1: "#1E3FAE", 2: "#2F5FE0", 3: "#8A93A4", 4: "#C4652A", 5: "#CE3B44"}.get(int(n), "#8A93A4")


def meter(n: int) -> str:
    n = int(n)
    return '<div class="meter">' + ''.join(
        f'<i style="background:{heat_color(n) if i <= n else "#E5E9EF"}"></i>' for i in range(1, 6)
    ) + '</div>'


def ul(items) -> str:
    return '<ul>' + ''.join(f'<li>{e(x)}</li>' for x in (items or [])) + '</ul>'


def page(d, n: int, title: str, body: str, kicker: str) -> str:
    return f"""
<section class="page">
  <div class="header mono"><div>{e(_REPORT_TITLE)} · Value Chain Weekly · {e(d['issue'])}</div><div>第 {n:02d} / 10 頁</div></div>
  <div class="kicker mono">{e(kicker)}</div>
  <h2 class="title">{e(title)}</h2>
  {body}
  <div class="footer mono"><span>研究與教育用途，不構成投資建議</span><span>第 {n:02d} / 10 頁</span></div>
</section>"""


CSS = r'''
@page { size: A4 portrait; margin: 0; }
html, body { margin:0; background:#E8EAEE; -webkit-print-color-adjust:exact; print-color-adjust:exact; color:#111827; font-family:'IBM Plex Sans','Noto Sans TC','Microsoft JhengHei',sans-serif; }
body { display:flex; flex-direction:column; align-items:center; gap:20px; padding:24px 0; }
@media print { body { gap:0; padding:0; background:#FBFCFD; } .page { break-after: page; max-height:none; overflow:visible; } }
.page { width:794px; max-height:1123px; box-sizing:border-box; background:#FBFCFD; padding:36px 44px 48px; position:relative; overflow:hidden; display:flex; flex-direction:column; }
.header { display:flex; justify-content:space-between; align-items:baseline; border-bottom:1px solid #E4E7EC; padding-bottom:8px; margin-bottom:16px; font-size:9px; letter-spacing:.12em; color:#8A93A4; text-transform:uppercase; }
.footer { position:absolute; left:48px; right:48px; bottom:16px; display:flex; justify-content:space-between; font-size:8px; letter-spacing:.1em; color:#AEB6C4; }
.mono { font-family:'IBM Plex Mono','Consolas',monospace; }
.kicker { font-size:9px; letter-spacing:.2em; color:#2F5FE0; margin-bottom:4px; }
.title { font-family:'Noto Serif TC','Microsoft JhengHei',serif; font-size:28px; font-weight:650; margin:0 0 12px; line-height:1.2; }
.cover-title { font-family:'Noto Serif TC','Microsoft JhengHei',serif; font-size:46px; line-height:1.05; margin:0; }
.card { background:white; border:1px solid #E4E7EC; border-radius:8px; padding:12px 16px; box-shadow:0 1px 2px rgba(16,23,37,.04); }
.accent { border-left:3px solid #2F5FE0; }
.blue { background:#F2F5FD; border-color:#D3E0FA; }
.red { background:#FCF3F3; border-color:#F1D5D6; }
.green { background:#F1F8F4; border-color:#CFE7DA; }
.yellow { background:#FBF6EA; border-color:#EBDCBB; }
.grid3 { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.verdict { font-family:'Noto Serif TC','Microsoft JhengHei',serif; font-size:22px; line-height:1.4; color:#0F1626; }
.muted { color:#5E6980; }
.small { font-size:11px; line-height:1.55; }
.badge { font-family:'Consolas',monospace; font-size:9px; letter-spacing:.06em; padding:3px 8px; border-radius:3px; white-space:nowrap; display:inline-block; }
.ok { color:#0E7A4B; background:rgba(18,145,90,.10); border:1px solid rgba(18,145,90,.3); }
.warn { color:#9A6A0F; background:rgba(176,124,21,.10); border:1px solid rgba(176,124,21,.3); }
.risk { color:#C0343C; background:rgba(206,59,68,.10); border:1px solid rgba(206,59,68,.3); }
.info { color:#2F5FE0; background:rgba(47,95,224,.08); border:1px solid rgba(47,95,224,.3); }
table { width:100%; border-collapse:separate; border-spacing:0; overflow:hidden; border:1px solid #E4E7EC; border-radius:8px; background:white; font-size:10.5px; }
th { background:#EEF1F5; color:#8A93A4; font-size:8.5px; letter-spacing:.1em; text-align:left; }
td, th { padding:8px 10px; border-bottom:1px solid #EDEFF2; vertical-align:top; }
tr:last-child td { border-bottom:0; }
.meter { display:flex; gap:3px; width:86px; margin-top:3px; }
.meter i { height:8px; flex:1; border-radius:2px; }
.heat-strip { display:grid; grid-template-columns:repeat(6,1fr); gap:6px; }
.heat-item { text-align:center; background:white; border:1px solid #E4E7EC; border-radius:6px; padding:8px 5px; font-size:9.5px; }
.dot { width:10px; height:10px; border-radius:50%; margin:0 auto 5px; }
.thesis-card { background:white; border:1px solid #E4E7EC; border-radius:8px; padding:12px 16px; display:grid; grid-template-columns:1fr auto; gap:10px; margin-bottom:8px; }
.thesis-card p, .arg p, .event p { margin:.3em 0; color:#5E6980; line-height:1.45; font-size:11px; }
.event { display:grid; grid-template-columns:52px 1fr auto; gap:10px; background:white; border:1px solid #E4E7EC; border-radius:6px; padding:9px 12px; margin-bottom:6px; }
.date { color:#8A93A4; font-size:9px; }
.arg { background:white; border:1px solid #E4E7EC; border-radius:8px; padding:12px; margin-bottom:8px; }
.evidence { color:#2F5FE0; }
.redtext { color:#C0343C; }
.quad { display:grid; grid-template-columns:1fr 1fr; grid-template-rows:1fr 1fr; gap:10px; flex:1; }
.quad .card { display:flex; flex-direction:column; gap:6px; }
.final-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:10px; }
li { margin-bottom:4px; font-size:11px; }
.asset { border:1px dashed #C4CBD6; border-radius:8px; background:white; display:flex; align-items:center; justify-content:center; color:#8A93A4; font-size:10px; text-align:center; }
.asset img { max-width:100%; max-height:100%; object-fit:contain; }
.asset.placeholder { background:repeating-linear-gradient(45deg,#fff,#fff 8px,#F1F3F6 8px,#F1F3F6 16px); }
.plot { height:360px; position:relative; border:1px solid #E4E7EC; border-radius:8px; background:linear-gradient(90deg,rgba(18,145,90,.05) 0 50%,rgba(138,147,164,.05) 50%),linear-gradient(0deg,rgba(18,145,90,.05) 0 50%,rgba(176,124,21,.05) 50%); }
.pt { position:absolute; display:flex; align-items:center; gap:6px; font-size:10px; font-weight:600; }
.pt i { width:12px; height:12px; border-radius:50%; border:2px solid white; box-shadow:0 0 0 1px currentColor; background:currentColor; }
ul { margin:4px 0 0 16px; padding:0; }
'''


# 估值 vs 基本面風險地圖預設散點(report-data.json 缺 valuation.map[] 時使用)。
_DEFAULT_VALUATION_POINTS = [
    ('GPU/ASIC', 18, 22, '#C4652A'),
    ('HBM', 30, 38, '#C4652A'),
    ('Optical', 55, 12, '#CE3B44'),
    ('Power', 14, 56, '#12915A'),
    ('Apps', 72, 28, '#CE3B44'),
]
# 四象限中文結論 → 散點顏色(對照 chart-spec.md §5 的四象限色)。
_QUADRANT_COLOR = {
    '優質但貴': '#C4652A',
    '危險區': '#CE3B44',
    '安全邊際區': '#12915A',
    '價值陷阱': '#8A93A4',
    '價值陷阱?': '#8A93A4',
}


def build_valuation_points(d: dict) -> list[tuple[str, float, float, str]]:
    """優先讀 report-data.json 的 valuation.map[]

    schema(見 templates/dashboard-template.html §06):
      {segment, fundamental_risk 0-100, valuation_level 0-100, quadrant}
    X = fundamental_risk(left%),Y = 100 - valuation_level(top%,高估值在上)。
    缺此欄位時退回原本硬編碼的 5 個示範散點。
    """
    raw = d.get('valuation', {}).get('map')
    if raw:
        return [
            (
                p.get('segment', ''),
                p.get('fundamental_risk', 50),
                100 - p.get('valuation_level', 50),
                _QUADRANT_COLOR.get(p.get('quadrant', ''), '#8A93A4'),
            )
            for p in raw
        ]
    return _DEFAULT_VALUATION_POINTS


def render_html(d: dict) -> str:
    heat_rows = ''.join(
        f"<tr><td>{e(localize_label(r['position']))}</td><td><b>{e(localize_label(r['segment']))}</b></td>"
        f"<td><span class='badge {badge_class(heat_label(r['heat_level']))}'>{heat_label(r['heat_level'])} {e(r['heat_level'])}</span></td>"
        f"<td>{meter(r['heat_level'])}</td><td>{e(r['signal'])}<br><span class='muted mono'>{e(r['tickers'])}</span></td></tr>"
        for r in d['heatmap']
    )
    cont_cards = ''.join(
        f"<div class='thesis-card'><div><b>{e(r['prior_view'])}</b><p>{e(r['evidence'])}</p>"
        f"<span class='mono muted'>THESIS 更新：{e(r['thesis_updated'])}</span></div>"
        f"<span class='badge {badge_class(r['status'])}'>{e(r['status'])}</span></div>"
        for r in d['continuity']
    )
    stat_cards = ''
    for sym, label in [('●','● 延續'),('▲','▲ 強化'),('▼','▼ 削弱'),('✕','✕ 推翻'),('◌','◌ 待驗證')]:
        count = sum(1 for r in d['continuity'] if str(r.get('status','')).startswith(sym))
        stat_cards += f'<div class="card" style="text-align:center"><div class="mono" style="font-size:24px;color:#2F5FE0">{count}</div><div class="mono muted">{label}</div></div>'

    events = ''.join(
        f"<div class='event'><span class='mono date'>{e(x.get('date'))}</span><div><b>{e(x.get('headline'))}</b>"
        f"<p>{e(x.get('why'))}</p></div><span class='badge {badge_class(x.get('impact'))}'>{e(x.get('impact'))}</span></div>"
        for x in d.get('events', [])
    )
    blue_cards = ''.join(f"<div class='arg'><b>{e(x['claim'])}</b><p>{e(x['evidence'])}</p><span class='mono evidence'>{e(x['strength'])}</span></div>" for x in d['debate']['blue'])
    red_cards = ''.join(f"<div class='arg'><b>{e(x['claim'])}</b><p>{e(x['evidence'])}</p><span class='mono evidence redtext'>{e(x['strength'])}</span></div>" for x in d['debate']['red'])
    val_rows = ''.join(
        f"<tr><td><b>{e(localize_label(r['segment']))}</b></td><td>{e(r['support'])}</td><td>{e(r['risk_reward'])}</td>"
        f"<td><span class='badge {badge_class(r['conclusion'])}'>{e(r['conclusion'])}</span></td></tr>"
        for r in d['valuation']['rows']
    )
    sources = ''.join(f"<h3>{e(k)}</h3>{ul(v)}" for k, v in [
        ('一手 / 硬數據', d['sources'].get('hard', [])),
        ('觀點來源', d['sources'].get('opinion', [])),
        ('市場隱含 / 輔助來源', d['sources'].get('market', [])),
    ])

    heat_strip = ''.join(
        f"<div class='heat-item'><div class='dot' style='background:{heat_color(r['heat_level'])}'></div><b>{e(localize_label(r['segment']).split('/')[0])}</b><br><span class='mono muted'>{heat_label(r['heat_level'])}</span></div>"
        for r in d['heatmap']
    )
    html_doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>{e(_REPORT_TITLE)} {e(d['date'])}</title><style>{CSS}</style></head><body>
<section class="page">
  <div class="header mono"><div>{e(_REPORT_TITLE)} · Value Chain Weekly · {e(d['issue'])}</div><div>{e(d['date'])}</div></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:32px"><div><div class="kicker mono">本週研究備忘</div><h1 class="cover-title">{e(_REPORT_TITLE)}</h1><div class="mono muted" style="font-size:10px;letter-spacing:.16em;margin-top:10px">{e(_INDUSTRY_NAME_ZH)} · 本週論點狀態</div></div><div class="mono muted" style="text-align:right;font-size:9px;line-height:1.9">結構版本 v1.0<br>可分享研究筆記<br>不構成投資建議</div></div>
  <div class="card accent" style="margin-top:30px"><div class="mono muted" style="font-size:9px;letter-spacing:.2em;margin-bottom:10px">本週一句話判斷</div><div class="verdict">{e(d['verdict_one_line'])}</div></div>
  <div class="grid3" style="margin-top:14px"><div class="card"><div class="mono muted">AI 基本面</div><p><span class="badge {badge_class(d['dashboard']['fundamentals_status'])}">{e(d['dashboard']['fundamentals_status'])}</span></p><p class="small muted">{e(d['dashboard']['fundamentals_note'])}</p></div><div class="card"><div class="mono muted">估值狀態</div><p><span class="badge {badge_class(d['dashboard']['valuation_status'])}">{e(d['dashboard']['valuation_status'])}</span></p><p class="small muted">{e(d['dashboard']['valuation_note'])}</p></div><div class="card"><div class="mono muted">泡沫風險</div><p><span class="badge {badge_class(d['dashboard']['bubble_risk'])}">{e(d['dashboard']['bubble_risk'])}</span></p><p class="small muted">{e(d['dashboard']['bubble_note'])}</p></div></div>
  <div class="grid2" style="margin-top:12px"><div class="card"><div class="mono muted">▲ 最強板塊</div><h3 style="color:#0E7A4B">{e(localize_label(d['dashboard']['strongest_segment']))}</h3><p class="small muted">{e(d['dashboard']['strongest_note'])}</p></div><div class="card"><div class="mono muted">▼ 最需警戒</div><h3 style="color:#C0343C">{e(localize_label(d['dashboard']['watch_segment']))}</h3><p class="small muted">{e(d['dashboard']['watch_note'])}</p></div></div>
  <div class="card blue" style="margin-top:12px"><div class="mono" style="color:#2F5FE0;letter-spacing:.2em;font-size:9px">本週反共識</div><p>{e(d['dashboard']['contrarian_view'])}</p></div>
  <div style="margin-top:auto"><div class="mono muted" style="font-size:9px;letter-spacing:.16em;margin-bottom:8px">產業鏈熱度帶</div><div class="heat-strip">{heat_strip}</div></div>
  <div class="footer mono"><span>研究與教育用途，不構成投資建議</span><span>第 01 / 10 頁</span></div>
</section>"""
    supply_asset = f"../assets/{e(d['date'])}/supply-chain-map.svg"
    capex_asset = f"../assets/{e(d['date'])}/capex-trend.png"
    html_doc += page(d, 2, f'{_INDUSTRY_NAME_ZH}熱力圖', f"<p class='muted'>熱度＝市場擁擠度與定價完美度，不等於基本面好壞。</p><table><tr><th>位置</th><th>板塊</th><th>熱度</th><th>溫度計</th><th>本週關鍵訊號</th></tr>{heat_rows}</table><div class='asset' style='margin-top:16px;height:220px'><img src='{supply_asset}' style='max-width:100%;max-height:100%;object-fit:contain' alt='Supply chain map'></div>", '第 02 節')
    html_doc += page(d, 3, '與上週判斷的延續 / 修正', f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px'>{stat_cards}</div>{cont_cards}<div class='card red' style='margin-top:auto'><b>Thesis 變更規則：不可協商</b><p>Thesis 只能因新事實或明確反證改變；單週股價波動只能影響估值狀態，不能直接改變基本面 thesis。</p></div>", '第 03 節 · 論點追蹤')
    html_doc += page(d, 4, '本週重大事件', events or '<div class="card muted">本週無重大事件。</div>', '第 04 節 · 重大事件')
    tilt = int(d['debate'].get('net_tilt_blue', 50))
    html_doc += page(d, 5, '藍隊 vs 紅隊', f"<p class='muted'>每一條論點必須附證據等級。禁止只列自己相信的一邊。</p><div class='grid2' style='flex:1'><div class='card blue'><h3>藍隊 · 多頭</h3>{blue_cards}</div><div class='card red'><h3>紅隊 · 空頭</h3>{red_cards}</div></div><div class='card' style='margin-top:14px'><b>淨傾向：</b> 藍隊 {tilt} / 紅隊 {100-tilt}<div style='height:10px;border-radius:5px;background:#EEF1F5;margin-top:10px;overflow:hidden'><div style='height:100%;width:{tilt}%;background:#2F5FE0'></div></div></div>", '第 05 節 · 對抗性審查')
    pts = build_valuation_points(d)
    plot = "<div class='plot'><span class='muted mono' style='position:absolute;left:12px;top:10px'>優質但貴</span><span class='muted mono' style='position:absolute;right:12px;top:10px'>危險區</span>" + ''.join([f"<div class='pt' style='left:{x}%;top:{y}%;color:{c}'><i></i>{e(name)}</div>" for name,x,y,c in pts]) + "</div>"
    html_doc += page(d, 6, '估值 vs 基本面風險地圖', f"{plot}<table style='margin-top:16px'><tr><th>板塊</th><th>基本面是否支持估值</th><th>風險報酬</th><th>結論</th></tr>{val_rows}</table><div class='card blue' style='margin-top:auto'>價格是投票機，本報告只對稱重機負責。</div>", '第 06 節 · 估值檢查')
    html_doc += page(d, 7, '需求真實性檢查', f"<div class='grid2'><div class='card'><h3 style='color:#0E7A4B'>誰正在賺錢</h3>{ul(d['demand'].get('earning', []))}</div><div class='card'><h3 style='color:#C0343C'>誰仍在燒錢</h3>{ul(d['demand'].get('burning', []))}</div></div><div class='card' style='margin-top:12px'><h3>CAPEX 是否可持續</h3><p>{e(d['demand'].get('capex'))}</p><div class='asset' style='height:240px;margin-top:10px'><img src='{capex_asset}' style='max-width:100%;max-height:100%;object-fit:contain' alt='CAPEX trend'></div></div><div class='card' style='margin-top:12px'><h3>AI 應用是否真的變現</h3><p>{e(d['demand'].get('monetization'))}</p></div>", '第 07 節 · 需求真實性檢查')
    w = d['watchlist']
    quad = ''.join([f"<div class='card {cls}'><h3>{title}</h3>{ul(w.get(key, []))}</div>" for key,title,cls in [('pullback','等待回調','blue'),('core','核心長期','green'),('overheated','過熱警戒','red'),('mispriced','預期差','yellow')]])
    html_doc += page(d, 8, '觀察名單四象限', f"<p class='muted'>縱軸：長期信念。橫軸：當前價格吸引力。標的進出象限必須留下紀錄。</p><div class='quad'>{quad}</div>", '第 08 節 · 觀察名單')
    f = d['final']
    html_doc += page(d, 9, '最終判斷', f"<div class='final-grid'><div class='card'><h3>我現在相信什麼</h3><p>{e(f.get('believe'))}</p></div><div class='card'><h3>我懷疑什麼</h3><p>{e(f.get('doubt'))}</p></div><div class='card'><h3>市場可能錯估哪裡</h3><p>{e(f.get('market_mispricing'))}</p></div><div class='card'><h3>如果我錯了，最可能錯在哪裡</h3><p>{e(f.get('if_wrong'))}</p></div></div><div class='card accent'><h3>下週最值得觀察的信號</h3>{ul(f.get('signals', []))}</div><div class='card blue' style='margin-top:14px'><b>{e(f.get('short'))}</b></div>", '第 09 節 · 最終判斷')
    html_doc += page(d, 10, '資料來源與聲明', f"<div class='card'>{sources}</div><div class='card red' style='margin-top:16px'><h3>免責聲明</h3><p>本報告為可分享之投資研究筆記，僅供資訊與教育用途，不構成任何證券之買賣建議或投資邀約。文中提及之公司與代號僅為研究框架示例。所有判斷可能出錯；讀者應自行進行盡職調查並為自身決策負責。過往表現不代表未來結果。</p></div>", '第 10 節 · 資料來源與聲明')
    return html_doc + '</body></html>'


def render_pdf(html_path: Path, pdf_path: Path, browser: str) -> None:
    # headless Chrome 對 --print-to-pdf 的相對路徑解析基準不是呼叫端 cwd,
    # 傳相對路徑會靜默寫檔失敗(returncode 仍是 0);先 resolve 成絕對路徑。
    pdf_path = pdf_path.resolve()
    url = html_path.resolve().as_uri()
    cmd = [browser, '--headless', '--disable-gpu', '--no-pdf-header-footer', '--allow-file-access-from-files', f'--print-to-pdf={str(pdf_path)}', url]
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out-dir')
    ap.add_argument('--no-pdf', action='store_true')
    ap.add_argument('--industry-config', default=str(Path(__file__).resolve().parents[1] / 'industry-config.yaml'))
    args = ap.parse_args()
    data_path = Path(args.data)
    d = json.loads(data_path.read_text(encoding='utf-8'))
    industry_config = load_industry_config(Path(args.industry_config))
    apply_industry_config_labels(industry_config)
    apply_industry_title(industry_config)
    out_dir = Path(args.out_dir) if args.out_dir else data_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{d['date']}-dashboard"
    html_path = out_dir / f'{stem}.html'
    pdf_path = out_dir / f'{stem}.pdf'
    html_path.write_text(render_html(d), encoding='utf-8')
    if not args.no_pdf:
        browser = find_browser()
        if browser:
            render_pdf(html_path, pdf_path, browser)
        else:
            print('[warn] 未找到 Chrome/Edge,已輸出 HTML,略過 PDF', file=sys.stderr)
    print(json.dumps({'html': str(html_path), 'pdf': str(pdf_path), 'pdf_exists': pdf_path.exists()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
