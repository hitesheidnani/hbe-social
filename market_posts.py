"""Market Monitor posts: Nifty index heatmaps and drawdown tables, from NSE index history.

History lives in data/indices/<NSE name>.json (seeded from the momobacktest cache, committed);
each run tops up the last few days from niftyindices.com. All figures are PRICE returns
(dividends not included), matching the Market Monitor.
"""
import json, datetime as dt, textwrap
from pathlib import Path

import requests

from brand import (canvas, brand_badge, footer, save, plt, FancyBboxPatch,
                   BG, PANEL, GRID, TEXT, MUTED, ACCENT, GOLD, UP, DOWN)

ROOT = Path(__file__).parent
CACHE = ROOT / "data" / "indices"
INDEX_LIST = json.loads((ROOT / "content" / "indices.json").read_text())
BASE = "https://www.niftyindices.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
_s = None


# ---------------------------------------------------------------- data
def _sess():
    global _s
    if _s is None:
        _s = requests.Session()
        _s.headers["User-Agent"] = UA
        _s.get(f"{BASE}/reports/historical-data", timeout=30)
    return _s


def _fetch(name, a, b):
    h = {"Content-Type": "application/json; charset=utf-8", "Accept": "application/json, text/javascript, */*; q=0.01",
         "Referer": f"{BASE}/reports/historical-data", "X-Requested-With": "XMLHttpRequest", "Origin": BASE}
    body = {"cinfo": "{'name':'%s','startDate':'%s','endDate':'%s','indexName':'%s'}"
            % (name, a.strftime("%d-%b-%Y"), b.strftime("%d-%b-%Y"), name)}
    r = _sess().post(f"{BASE}/BackPage/getHistoricaldatatabletoString", headers=h, data=json.dumps(body), timeout=60)
    r.raise_for_status()
    rows = r.json()
    if isinstance(rows, dict) and "d" in rows:
        rows = json.loads(rows["d"])
    out = {}
    for row in rows:
        try:
            d = dt.datetime.strptime(row["HistoricalDate"], "%d %b %Y").date()
            v = float(row["CLOSE"])
        except Exception:
            continue
        if v > 0:
            out[d.isoformat()] = v
    return out


def update_all():
    """Top up every cached index with the last ~10 days. Failures keep the cached history."""
    ok = fail = 0
    for r in INDEX_LIST:
        p = CACHE / r["file"]
        data = json.loads(p.read_text())
        start = dt.date.fromisoformat(max(data)) - dt.timedelta(days=10)
        try:
            data.update(_fetch(r["nse"], start, dt.date.today()))
            p.write_text(json.dumps(dict(sorted(data.items()))))
            ok += 1
        except Exception as e:
            fail += 1
            print(f"indices: {r['name']} top-up failed ({e})")
    print(f"indices: {ok} updated, {fail} failed")


def series(r):
    data = json.loads((CACHE / r["file"]).read_text())
    return [(dt.date.fromisoformat(k), v) for k, v in sorted(data.items())]


def metrics(r):
    s = series(r)
    last_d, last = s[-1]

    def back(years):
        target = last_d.replace(year=last_d.year - years) if not (last_d.month == 2 and last_d.day == 29) \
            else last_d.replace(year=last_d.year - years, day=28)
        prior = [v for d, v in s if d <= target]
        if not prior or s[0][0] > target - dt.timedelta(days=7):
            return None
        return ((last / prior[-1]) ** (1 / years) - 1) * 100

    ath_d, ath = max(s, key=lambda x: x[1])
    yr = [(d, v) for d, v in s if d > last_d - dt.timedelta(days=365)]
    hi52_d, hi52 = max(yr, key=lambda x: x[1])
    return {**r, "asof": last_d, "last": last, "1y": back(1), "3y": back(3), "5y": back(5),
            "ath": ath, "ath_date": ath_d, "dd": (last / ath - 1) * 100, "dd_days": (last_d - ath_d).days,
            "hi52": hi52, "hi52_date": hi52_d, "dd52": (last / hi52 - 1) * 100, "from": s[0][0]}


def all_metrics():
    return [metrics(r) for r in INDEX_LIST]


# ---------------------------------------------------------------- drawing helpers
KEEP_UPPER = {"IT", "FMCG", "PSU", "CPSE", "PSE", "MNC", "NBFC", "EV", "MQVLV", "LARGEMIDCAP", "MIDSMALLCAP"}
SPECIAL = {"REITS": "REITs", "INVITS": "InvITs", "LARGEMIDCAP": "LargeMidcap", "MIDSMALLCAP": "MidSmallcap",
           "MIDSMALL": "MidSmall", "FLEXICAP": "Flexicap", "LOW-VOLATILITY": "Low Volatility", "EX-BANK": "ex-Bank",
           "NON-CYCLICAL": "Non-Cyclical"}
RENAME = {
    "INDIA CORPORATE GROUP INDEX - ADITYA BIRLA GROUP": "Aditya Birla Group",
    "INDIA CORPORATE GROUP INDEX - MAHINDRA GROUP": "Mahindra Group",
    "INDIA CORPORATE GROUP INDEX - TATA GROUP": "Tata Group",
    "SMALL FINANCE BANKS & MICROFINANCE INSTITUTIONS": "Small Finance Banks & MFIs",
    "500 MULTICAP INDIA MANUFACTURING 50:30:20": "500 Multicap Manufacturing",
    "500 MULTICAP INFRASTRUCTURE 50:30:20": "500 Multicap Infrastructure",
    "COMMERCIAL & TRANSPORT SERVICES": "Commercial & Transport",
    "MidSmallcap400 Momentum Quality 100": "MidSmallcap 400 Mom. Quality 100",
    "Smallcap250 Momentum Quality 100": "Smallcap 250 Mom. Quality 100",
    "Alpha Quality Value LOW-VOLATILITY 30": "Alpha Quality Value Low Vol 30",
    "Total Market Momentum Quality 50": "Total Market Mom. Quality 50",
}


def short(n):
    """Readable index name: drop the leading 'Nifty' (kept for 'Nifty 50' etc.), fix SHOUTED words."""
    n = n.replace("NIFTY", "Nifty").replace("Nifty500", "Nifty 500").replace("Nifty200", "Nifty 200") \
         .replace("Nifty100", "Nifty 100").replace("Nifty50", "Nifty 50")
    body = n[6:] if n.startswith("Nifty ") else n
    body = RENAME.get(body, body)
    words = []
    for w in body.split():
        if w in SPECIAL:
            w = SPECIAL[w]
        elif w.isupper() and w not in KEEP_UPPER and any(c.isalpha() for c in w):
            w = w.capitalize()
        words.append(w)
    body = " ".join(words)
    return f"Nifty {body}" if body[:1].isdigit() else body


def heat_color(v, scale):
    """Green for gains, red for losses, deeper for bigger moves (blended onto the panel colour)."""
    import matplotlib.colors as mc
    base = mc.to_rgb(PANEL)
    tgt = mc.to_rgb(UP if v >= 0 else DOWN)
    a = min(abs(v) / scale, 1.0) * 0.75 + 0.08
    return tuple(b + (t - b) * a for b, t in zip(base, tgt))


def header(fig, kicker, title, subtitle):
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.895, kicker.upper(), color=ACCENT, fontsize=15, weight="semibold")
    fig.text(0.06, 0.845, title, color=TEXT, fontsize=34, weight="heavy", va="center")
    fig.text(0.06, 0.80, subtitle, color=MUTED, fontsize=13.5, va="center")


def market_footer(fig, note):
    fig.text(0.5, 0.083, note, color=MUTED, fontsize=9.5, ha="center")
    footer(fig, "generic")


HZ = {"1y": "1-year", "3y": "3-year", "5y": "5-year"}


# ---------------------------------------------------------------- posts
def heatmap(category, horizon, out, ms=None):
    ms = ms or all_metrics()
    rows = sorted([m for m in ms if m["category"] == category and m[horizon] is not None],
                  key=lambda m: m[horizon], reverse=True)
    asof = max(m["asof"] for m in rows)
    cols = 5 if len(rows) > 20 else 4
    nrow = -(-len(rows) // cols)
    top, bottom = 0.77, 0.115
    gap = 0.006
    tw = (0.88 - gap * (cols - 1)) / cols
    th = min(0.11, (top - bottom - gap * (nrow - 1)) / nrow)
    scale = max(10, max(abs(m[horizon]) for m in rows))
    kind = "CAGR" if horizon != "1y" else "return"
    fig = canvas()
    header(fig, f"Market monitor · {category}", f"{category} indices: {HZ[horizon]} {kind}",
           f"{len(rows)} Nifty indices, best first · price return · as of {asof:%d %b %Y}")
    for i, m in enumerate(rows):
        r, c = divmod(i, cols)
        x = 0.06 + c * (tw + gap)
        y = top - (r + 1) * th - r * gap
        fig.add_artist(FancyBboxPatch((x, y), tw, th, boxstyle="round,pad=0,rounding_size=0.006",
                                      transform=fig.transFigure, fc=heat_color(m[horizon], scale), ec=BG, lw=1))
        name = textwrap.fill(short(m["name"]), 16 if cols == 5 else 20)
        fs = 10.5 if cols == 5 else 12
        fig.text(x + 0.008, y + th - 0.008, name, color=TEXT, fontsize=fs, va="top", linespacing=1.15)
        fig.text(x + tw - 0.008, y + 0.01, f"{m[horizon]:+.1f}%", color=TEXT, fontsize=15 if cols == 5 else 17,
                 weight="bold", ha="right", va="bottom")
    up = sum(m[horizon] >= 0 for m in rows)
    market_footer(fig, f"{up} of {len(rows)} up · {'per year (CAGR)' if horizon != '1y' else 'last 12 months'} · "
                       "price returns, dividends excluded · Source: NSE Indices")
    save(fig, out)
    return {"category": category, "horizon": horizon, "asof": asof, "count": len(rows), "up": up,
            "best": [(short(m["name"]), m[horizon]) for m in rows[:3]],
            "worst": [(short(m["name"]), m[horizon]) for m in rows[-3:][::-1]]}


def drawdown_table(category, out, ms=None, max_rows=16):
    ms = ms or all_metrics()
    rows = sorted([m for m in ms if m["category"] == category], key=lambda m: m["dd"], reverse=True)
    asof = max(m["asof"] for m in rows)
    shown = rows if len(rows) <= max_rows else rows[:max_rows // 2] + rows[-(max_rows // 2):]
    fig = canvas()
    header(fig, f"Market monitor · {category}", "How far from the top?",
           f"{category} indices vs their all-time & 52-week highs · price · as of {asof:%d %b %Y}")
    cols = [(0.06, "Index", "left"), (0.555, "From ATH", "right"), (0.705, "ATH date", "right"),
            (0.815, "Days", "right"), (0.94, "From 52W hi", "right")]
    y = 0.765
    for x, label, ha in cols:
        fig.text(x, y, label, color=MUTED, fontsize=12, ha=ha, weight="semibold")
    rh = min(0.04, (0.765 - 0.13) / (len(shown) + 1))
    y -= 0.012
    for i, m in enumerate(shown):
        if len(rows) > max_rows and i == max_rows // 2:
            fig.text(0.5, y - rh * 0.45, f"· · ·  {len(rows) - max_rows} more  · · ·", color=MUTED,
                     fontsize=11, ha="center", va="center")
            y -= rh * 0.9
        yc = y - rh / 2
        if i % 2 == 0:
            fig.add_artist(FancyBboxPatch((0.05, y - rh), 0.90, rh, boxstyle="round,pad=0,rounding_size=0.004",
                                          transform=fig.transFigure, fc=PANEL, ec="none", zorder=-1))
        at_high = m["dd"] > -0.5
        fig.text(0.06, yc, short(m["name"])[:36], color=TEXT, fontsize=13.5, va="center")
        fig.text(0.555, yc, "At high" if at_high else f"{m['dd']:.1f}%", color=UP if at_high else (
            DOWN if m["dd"] < -10 else GOLD), fontsize=14, weight="bold", ha="right", va="center")
        fig.text(0.705, yc, f"{m['ath_date']:%d %b %y}", color=TEXT, fontsize=12.5, ha="right", va="center")
        fig.text(0.815, yc, f"{m['dd_days']:,}", color=TEXT, fontsize=12.5, ha="right", va="center")
        fig.text(0.94, yc, f"{m['dd52']:.1f}%", color=MUTED if m["dd52"] > -5 else DOWN, fontsize=13,
                 ha="right", va="center")
        y -= rh
    near = sum(m["dd"] > -5 for m in rows)
    deep = sum(m["dd"] <= -20 for m in rows)
    market_footer(fig, f"{near} of {len(rows)} within 5% of their all-time high · {deep} down 20% or more · "
                       "Days = calendar days since the high · Source: NSE Indices")
    save(fig, out)
    return {"category": category, "asof": asof, "count": len(rows), "near": near, "deep": deep,
            "closest": [(short(m["name"]), m["dd"], m["ath_date"]) for m in rows[:3]],
            "deepest": [(short(m["name"]), m["dd"], m["ath_date"], m["dd_days"]) for m in rows[-3:][::-1]]}
