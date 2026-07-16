#!/usr/bin/env python3
"""Render the Portfolio Weekly hi-fi dashboard: inject report-data JSON into the
template, then print an A4 portrait PDF via headless Chrome/Edge.

Usage:
  python render_portfolio_report.py --data <report-data.json> --out-pdf <path> [--out-html <path>]

The template keeps window.REPORT_DATA between BEGIN/END marker comments, so
injection is a simple marker-delimited swap. PDF output needs a Chrome/Edge
binary detected via common/render_env.find_browser(); if none is found the
HTML is still written (to --out-html, or to a persistent path derived from
--out-pdf if --out-html is omitted) and PDF rendering is skipped with a
warning — the HTML output always survives regardless of PDF success.
Rendering waits via --virtual-time-budget so the Chart.js doughnut
(animation:false) and web fonts settle before the print snapshot.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from render_env import find_browser

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "portfolio-dashboard.template.html"
BEGIN = "/*__REPORT_DATA_BEGIN__*/"
END = "/*__REPORT_DATA_END__*/"


def fill_template(data: dict) -> str:
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    if BEGIN not in tmpl or END not in tmpl:
        raise RuntimeError(f"Data markers {BEGIN} / {END} not found in {TEMPLATE}")
    i = tmpl.index(BEGIN) + len(BEGIN)
    j = tmpl.index(END)
    block = "\nwindow.REPORT_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    return tmpl[:i] + block + tmpl[j:]


def render_pdf(html_path: Path, pdf_path: Path, browser: str) -> None:
    pdf_path = pdf_path.resolve()
    profile = Path(tempfile.mkdtemp(prefix="pwk-chrome-"))
    try:
        cmd = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--allow-file-access-from-files",
            "--hide-scrollbars",
            f"--user-data-dir={profile}",
            "--virtual-time-budget=12000",
            f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri(),
        ]
        subprocess.run(cmd, check=True, timeout=120)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render Portfolio Weekly report to A4 PDF")
    ap.add_argument("--data", required=True, help="path to report-data.json")
    ap.add_argument("--out-pdf", required=True, help="output PDF path")
    ap.add_argument("--out-html", help="output HTML path (default: same dir/stem as --out-pdf, .html)")
    args = ap.parse_args()

    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    filled = fill_template(data)

    out_pdf = Path(args.out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    # HTML 一律寫到持久路徑(未指定 --out-html 時,衍生自 --out-pdf 的同目錄/同檔名
    # .html),不再用完就刪的暫存檔——找不到瀏覽器只略過 PDF,HTML 一定要留著。
    html_path = Path(args.out_html) if args.out_html else out_pdf.with_suffix(".html")
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(filled, encoding="utf-8")

    browser = find_browser()
    if browser:
        render_pdf(html_path, out_pdf, browser)
    else:
        print("[warn] 未找到 Chrome/Edge,已輸出 HTML,略過 PDF", file=sys.stderr)

    print(json.dumps({
        "data": str(args.data),
        "out_pdf": str(out_pdf),
        "pdf_exists": out_pdf.exists(),
        "pdf_bytes": out_pdf.stat().st_size if out_pdf.exists() else 0,
        "out_html": str(html_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
