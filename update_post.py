"""08:00 IST Market Update: key Indian & US indices, gold, oil, US 10Y yield, USD/INR.

Each row: last close, 1-day change, distance from the 200-day moving average and a trend tag
(above the 200 DMA = bullish/green, below = bearish/red). Indian indices come from the NSE history
cached for the Market Monitor; US and global prices from Yahoo Finance.
"""
import json, time, datetime as dt, urllib.request, urllib.parse

from brand import canvas, brand_badge, footer, save, FancyBboxPatch, BG, PANEL, GRID, TEXT, MUTED, ACCENT, GOLD, UP, DOWN
import market_posts as mkt

INDIA = [("Nifty 50", "Nifty 50"), ("Nifty Bank", "Nifty Bank"),
         ("Nifty Midcap 150", "Nifty Midcap 150"), ("Nifty Smallcap 250", "Nifty Smallcap 250")]
US = [("S&P 500", "^GSPC"), ("Nasdaq 100", "^NDX"), ("Dow Jones", "^DJI"), ("Russell 2000", "^RUT")]
GLOBAL = [("Gold ($/oz)", "GC=F", "px"), ("Brent crude ($)", "BZ=F", "px"),
          ("US 10Y yield", "^TNX", "yield"), ("USD / INR", "INR=X", "fx")]


def yahoo(symbol, tries=3):
    for host in ("query1", "query2"):
        for k in range(tries):
            try:
                u = (f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
                     "?range=1y&interval=1d")
                d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}),
                                                     timeout=20))["chart"]["result"][0]
                # Use completed sessions only. Gold, Brent and USD/INR trade almost 24 hours, so at 8am IST
                # Yahoo already has a partial bar for 'today' (UTC); drop it so every row is a true close.
                today_utc = dt.datetime.now(dt.UTC).date()
                pts = [(dt.datetime.fromtimestamp(t, dt.UTC).date(), c)
                       for t, c in zip(d["timestamp"], d["indicators"]["quote"][0]["close"]) if c is not None]
                return [(d_, c) for d_, c in pts if d_ < today_utc]
            except Exception as e:
                last = e
                time.sleep(2 * (k + 1))
    print(f"update: {symbol} unavailable ({last})")
    return None


def stats(pts, kind="px"):
    if not pts or len(pts) < 200:
        return None
    (d1, p1), (_, p0) = pts[-1], pts[-2]
    dma = sum(p for _, p in pts[-200:]) / 200
    return {"date": d1, "last": p1, "chg": (p1 - p0) * 100 if kind == "yield" else (p1 / p0 - 1) * 100,
            "vs200": (p1 / dma - 1) * 100, "above": p1 > dma, "kind": kind}


def collect():
    rows = {"India": [], "US": [], "Global": []}
    lookup = {r["name"].lower(): r for r in mkt.INDEX_LIST}
    for label, name in INDIA:
        r = lookup.get(name.lower())
        rows["India"].append((label, stats(mkt.series(r)) if r else None))
    for label, sym in US:
        rows["US"].append((label, stats(yahoo(sym))))
    for label, sym, kind in GLOBAL:
        rows["Global"].append((label, stats(yahoo(sym), kind)))
    return rows


def fmt_price(s):
    if s["kind"] == "yield":
        return f"{s['last']:.2f}%"
    return f"{s['last']:,.2f}" if s["last"] < 1000 else f"{s['last']:,.0f}"


def fmt_chg(s):
    return f"{s['chg']:+.0f} bp" if s["kind"] == "yield" else f"{s['chg']:+.2f}%"


NEUTRAL_BAND = 1.0   # within ±1% of the 200 DMA the trend is 'Neutral', so tiny moves don't flip the tag


def trend_tag(s):
    if s["kind"] in ("yield", "fx"):          # rates and currency: direction, not good/bad
        return ("Rising" if s["above"] else "Falling"), GOLD
    if abs(s["vs200"]) < NEUTRAL_BAND:
        return "Neutral", GOLD
    return ("Bullish" if s["above"] else "Bearish"), (UP if s["above"] else DOWN)


def market_update(out, rows=None, day=None):
    rows = rows or collect()
    have = [s for sec in rows.values() for _, s in sec if s]
    if len(have) < 8:
        raise RuntimeError(f"only {len(have)} of 12 instruments available; skipping the update")
    india_d = max((s["date"] for _, s in rows["India"] if s), default=None)
    us_d = max((s["date"] for _, s in rows["US"] if s), default=None)
    today = day or dt.date.today()

    fig = canvas()
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.895, "MARKET UPDATE", color=ACCENT, fontsize=15, weight="semibold")
    fig.text(0.06, 0.848, "Markets at a glance", color=TEXT, fontsize=36, weight="heavy", va="center")
    fig.text(0.06, 0.805, f"{today:%A, %d %b %Y} · last closes · trend vs 200-day average", color=MUTED,
             fontsize=14, va="center")

    cols = [(0.08, "left"), (0.53, "right"), (0.665, "right"), (0.80, "right"), (0.935, "right")]
    y = 0.765
    for (x, ha), label in zip(cols, ["", "Price", "1 day", "vs 200 DMA", "Trend"]):
        fig.text(x, y, label, color=MUTED, fontsize=12, ha=ha, weight="semibold")
    y -= 0.012
    rh = 0.043
    flag = {"India": "INDIA", "US": "UNITED STATES", "Global": "GLOBAL"}
    for sec, items in rows.items():
        fig.text(0.06, y - 0.017, flag[sec], color=GOLD, fontsize=13, weight="bold", va="center")
        y -= 0.034
        for i, (label, s) in enumerate(items):
            yc = y - rh / 2
            fig.add_artist(FancyBboxPatch((0.05, y - rh + 0.003), 0.90, rh - 0.006,
                                          boxstyle="round,pad=0,rounding_size=0.008", transform=fig.transFigure,
                                          fc=PANEL, ec=GRID, lw=0.8, zorder=-1))
            fig.text(0.08, yc, label, color=TEXT, fontsize=16, weight="semibold", va="center")
            if s:
                up = s["chg"] >= 0
                fig.text(0.53, yc, fmt_price(s), color=TEXT, fontsize=15.5, ha="right", va="center")
                fig.text(0.665, yc, fmt_chg(s), color=UP if up else DOWN, fontsize=15, weight="bold",
                         ha="right", va="center")
                fig.text(0.80, yc, f"{s['vs200']:+.1f}%", color=MUTED, fontsize=14, ha="right", va="center")
                tag, col = trend_tag(s)
                fig.add_artist(FancyBboxPatch((0.835, yc - 0.012), 0.10, 0.024,
                                              boxstyle="round,pad=0,rounding_size=0.011", transform=fig.transFigure,
                                              fc=col, ec="none", alpha=0.18))
                fig.text(0.885, yc, tag, color=col, fontsize=12.5, weight="bold", ha="center", va="center")
            else:
                fig.text(0.53, yc, "data unavailable", color=MUTED, fontsize=12, ha="right", va="center")
            y -= rh
        y -= 0.008

    trend_rows = [s for sec in ("India", "US") for _, s in rows[sec] if s] + \
                 [s for _, s in rows["Global"] if s and s["kind"] == "px"]
    bull = sum(s["above"] for s in trend_rows)
    note = (f"{bull} of {len(trend_rows)} indices & commodities above their 200-day average · "
            f"India: NSE close {india_d:%d %b} · US & global: close {us_d:%d %b} · 200-day simple moving average of closes")
    fig.text(0.5, 0.083, note, color=MUTED, fontsize=9.5, ha="center")
    footer(fig, "generic")
    save(fig, out)
    return {"date": today, "india_date": india_d, "us_date": us_d, "bull": bull, "total": len(trend_rows),
            "rows": {sec: [(l, s) for l, s in items] for sec, items in rows.items()}}


def caption(r, edu_line, foot_tags="#stockmarket #nifty50 #sp500 #marketupdate #investing"):
    def line(label, s):
        if not s:
            return f"{label}: n/a"
        dot = "🟡" if abs(s["vs200"]) < NEUTRAL_BAND else ("🟢" if s["above"] else "🔴")
        if s["kind"] in ("yield", "fx"):
            dot = "⬆️" if s["above"] else "⬇️"
        return f"{dot} {label}: {fmt_price(s)} ({fmt_chg(s)})"
    parts = [f"Market Update | {r['date']:%a, %d %b %Y} 🌏", ""]
    for sec, flag in (("India", "🇮🇳 India"), ("US", "🇺🇸 US"), ("Global", "🌍 Global")):
        parts += [flag] + [line(l, s) for l, s in r["rows"][sec]] + [""]
    parts += [f"Trend check: {r['bull']} of {r['total']} indices & commodities are above their 200-day average.",
              "🟢 more than 1% above the 200-day average (bullish) · 🔴 more than 1% below (bearish) · "
              "🟡 within 1% (neutral) · "
              "⬆️⬇️ rates and USD/INR vs their 200-day average.", "",
              f"India: NSE close {r['india_date']:%d %b}. US & global: close {r['us_date']:%d %b}. "
              "Index figures are price levels.", "",
              "🔔 Follow @hbecapital for this update every morning at 8.", "",
              f"⚠️ {edu_line}", "", foot_tags]
    return "\n".join(parts)
