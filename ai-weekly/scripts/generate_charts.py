#!/usr/bin/env python3
"""Generate chart assets for AI Industry Chain Weekly.

Input: report-data.json
Output: reports/assets/YYYY-MM-DD/{capex-trend.png,supply-chain-map.svg}
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from render_env import find_cjk_font


def heat_color(n):
    return {1:'#1E3FAE',2:'#2F5FE0',3:'#8A93A4',4:'#C4652A',5:'#CE3B44'}.get(int(n or 3),'#8A93A4')

def e(s):
    return str(s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def load_industry_config(path: Path) -> dict:
    """讀取 industry-config.yaml;找不到檔案回傳空 dict,YAML 格式錯誤時印警告並回傳
    空 dict(呼叫端因此套用內建預設值,不中斷渲染)。"""
    if not path.exists():
        return {}
    try:
        with path.open(encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        print('[warn] industry-config.yaml 解析失敗,改用內建預設板塊', file=sys.stderr)
        return {}

def capex_png(d, out):
    # Pure-PIL bar chart: avoids matplotlib dependency.
    from PIL import Image, ImageDraw, ImageFont
    chart = d.get('charts', {}).get('capex_trend')
    if chart and chart.get('series'):
        periods = [v['period'] for v in chart['series'][0]['values']]
        vals = [sum(s['values'][i]['value'] for s in chart['series']) for i in range(len(periods))]
    else:
        periods = ['25Q1','25Q2','25Q3','25Q4','26Q1','26Q2']
        vals = [210,230,255,280,310,345]
    W,H = 1316,300
    img = Image.new('RGB', (W,H), 'white')
    dr = ImageDraw.Draw(img)
    font_path = find_cjk_font()
    if font_path:
        font = ImageFont.truetype(font_path, 22)
        small = ImageFont.truetype(font_path, 18)
    else:
        print('[warn] 未找到 CJK 字型,圖表退回預設字型', file=sys.stderr)
        font = small = ImageFont.load_default()
    dr.text((38,22), 'Hyperscaler AI CAPEX Trend', fill='#111827', font=font)
    left, top, right, bottom = 80, 72, W-42, H-52
    # grid
    for i in range(5):
        y = top + i*(bottom-top)/4
        dr.line((left,y,right,y), fill='#E4E7EC', width=1)
    maxv = max(vals) * 1.15
    n = len(vals); gap = 26; bw = (right-left - gap*(n+1))/n
    for i,(p,v) in enumerate(zip(periods, vals)):
        x0 = left + gap + i*(bw+gap); x1 = x0 + bw
        y1 = bottom; y0 = bottom - (v/maxv)*(bottom-top)
        dr.rounded_rectangle((x0,y0,x1,y1), radius=8, fill='#2F5FE0')
        dr.text((x0+bw/2-24, bottom+12), p, fill='#5E6980', font=small)
        dr.text((x0+bw/2-22, y0-26), str(v), fill='#111827', font=small)
    dr.text((right-210, 22), 'USD bn proxy / placeholder', fill='#8A93A4', font=small)
    img.save(out)

def supply_chain_svg(d, out, industry_name_en):
    rows = d.get('heatmap', [])[:6]
    w,h = 1316,520
    col_x = [90, 330, 570, 810, 1050]
    y0 = 100
    nodes=[]
    for i,r in enumerate(rows):
        layer = min(i,4)
        x = col_x[layer]
        y = y0 + (i%2)*150 if i<4 else y0 + (i-4)*150
        nodes.append((x,y,r))
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">', '<rect width="100%" height="100%" fill="#0A1120"/>']
    svg.append(f'<text x="48" y="50" fill="#E8EAEE" font-family="IBM Plex Mono,Consolas,monospace" font-size="22" font-weight="700">{e(industry_name_en)} · BOTTLENECK MAP</text>')
    # edges
    for (x1,y1,_),(x2,y2,_) in zip(nodes, nodes[1:]):
        svg.append(f'<path d="M{x1+170},{y1+45} C{x1+230},{y1+45} {x2-60},{y2+45} {x2},{y2+45}" stroke="#2F5FE0" stroke-width="4" fill="none" opacity="0.75"/>')
    for x,y,r in nodes:
        c=heat_color(r.get('heat_level',3))
        svg.append(f'<rect x="{x}" y="{y}" width="190" height="90" rx="16" fill="#111A2E" stroke="{c}" stroke-width="4"/>')
        svg.append(f'<text x="{x+18}" y="{y+34}" fill="#FFFFFF" font-family="Microsoft JhengHei,Noto Sans TC,sans-serif" font-size="22" font-weight="700">{e(r.get("segment"))}</text>')
        svg.append(f'<text x="{x+18}" y="{y+64}" fill="#AEB6C4" font-family="Consolas,monospace" font-size="15">heat {e(r.get("heat_level"))} · {e(r.get("position"))}</text>')
    svg.append('<text x="48" y="485" fill="#8A93A4" font-family="Consolas,monospace" font-size="15">Node border color = weekly heat level. Blue edges = current bottleneck transmission path.</text>')
    svg.append('</svg>')
    out.write_text('\n'.join(svg), encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data', required=True); ap.add_argument('--assets-dir')
    ap.add_argument('--industry-config', default=str(Path(__file__).resolve().parents[1] / 'industry-config.yaml'))
    args=ap.parse_args(); data_path=Path(args.data); d=json.loads(data_path.read_text(encoding='utf-8'))
    config = load_industry_config(Path(args.industry_config))
    industry_name_en = config.get('industry', {}).get('name_en', 'AI Industry Chain')
    if args.assets_dir: assets=Path(args.assets_dir)
    else: assets=data_path.parents[1]/'assets'/d['date']
    assets.mkdir(parents=True, exist_ok=True)
    capex_png(d, assets/'capex-trend.png')
    supply_chain_svg(d, assets/'supply-chain-map.svg', industry_name_en)
    print(json.dumps({'assets_dir':str(assets),'files':[str(assets/'capex-trend.png'),str(assets/'supply-chain-map.svg')]}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()
