"""跨平台渲染環境偵測:headless 瀏覽器(列印 PDF)與 CJK 字型。"""
import os
import platform
import shutil
from pathlib import Path

BROWSER_CANDIDATES = {
    "Windows": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ],
    "Darwin": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ],
    "Linux": ["google-chrome", "chromium", "chromium-browser", "microsoft-edge"],
}

CJK_FONT_CANDIDATES = {
    "Windows": [
        "C:/Windows/Fonts/NotoSansTC-VF.ttf",
        "C:/Windows/Fonts/msjh.ttc",
        "C:/Windows/Fonts/msyh.ttc",
    ],
    "Darwin": [
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ],
    "Linux": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ],
}


def find_browser():
    """回傳可用的 Chrome/Edge/Chromium 執行檔;找不到回傳 None。
    環境變數 BROWSER_BIN 可強制指定;設為 'none' 可測試降級路徑。"""
    env = os.environ.get("BROWSER_BIN")
    if env:
        return None if env.lower() == "none" else env
    system = platform.system()
    for cand in BROWSER_CANDIDATES.get(system, []):
        if Path(cand).exists():
            return cand
        found = shutil.which(cand)
        if found:
            return found
    return None


def find_cjk_font():
    """回傳可用 CJK 字型路徑;找不到回傳 None(呼叫端退回預設字型並警告)。
    環境變數 CJK_FONT 可強制指定。"""
    env = os.environ.get("CJK_FONT")
    if env and Path(env).exists():
        return env
    for cand in CJK_FONT_CANDIDATES.get(platform.system(), []):
        if Path(cand).exists():
            return cand
    return None
