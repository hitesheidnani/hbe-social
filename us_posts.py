"""US market posts (Yahoo Finance data; completed daily closes only).

  us_close_card      08:30 Tue-Fri: indices, VIX, Magnificent 7, 11 sectors - last session's moves
  us_health          08:30 Sat: index trend vs 50/100/200-day SMA + S&P 500 breadth, Risk-on/Neutral/Risk-off
  us_sector_heatmap  19:00 Mon: 11 S&P sectors (ETF total return), 1y/3y/5y
  us_vs_india        19:00 Tue: S&P 500 in rupees vs Nifty 50, 1/3/5/10 years
  us_drawdown        19:00 Wed: indices & Mag 7 vs all-time and 52-week highs
  us_style           19:00 Thu: growth vs value, large vs small, equal weight, momentum, quality, low vol
  sp500_years        19:00 Fri: S&P 500 calendar-year returns since 1986
  us_weekly_wrap     19:00 Sun: the week for indices, sectors and Mag 7
"""
import csv, io, json, time, datetime as dt, textwrap, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from brand import (canvas, brand_badge, footer, save, plt, FancyBboxPatch,
                   BG, PANEL, GRID, TEXT, MUTED, ACCENT, GOLD, UP, DOWN)

ROOT = Path(__file__).parent
INDICES = [("S&P 500", "^GSPC"), ("Nasdaq 100", "^NDX"), ("Dow Jones", "^DJI"), ("Russell 2000", "^RUT")]
MAG7 = [("Apple", "AAPL"), ("Microsoft", "MSFT"), ("Nvidia", "NVDA"), ("Amazon", "AMZN"),
        ("Alphabet", "GOOGL"), ("Meta", "META"), ("Tesla", "TSLA")]
SECTORS = [("Technology", "XLK"), ("Financials", "XLF"), ("Health Care", "XLV"), ("Cons. Discretionary", "XLY"),
           ("Cons. Staples", "XLP"), ("Energy", "XLE"), ("Industrials", "XLI"), ("Materials", "XLB"),
           ("Utilities", "XLU"), ("Real Estate", "XLRE"), ("Communication", "XLC")]
STYLES = [("S&P 500 Growth", "SPYG", "S&P 500 Value", "SPYV"), ("Large (S&P 500)", "SPY", "Small (Russell 2000)", "IWM"),
          ("Equal-weight S&P", "RSP", "S&P 500", "SPY"), ("Momentum", "MTUM", "S&P 500", "SPY"),
          ("Quality", "QUAL", "S&P 500", "SPY"), ("Low volatility", "USMV", "S&P 500", "SPY")]
CONSTITUENTS_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
US_NOTE = "US data: Yahoo Finance, daily closes."
_cache = {}


# ---------------------------------------------------------------- data
def yahoo(symbol, rng="2y", interval="1d", adjusted=False, tries=3):
    """Ascending [(date, close)] of COMPLETED sessions (today's partial bar, UTC, is dropped)."""
    key = (symbol, rng, interval, adjusted)
    if key in _cache:
        return _cache[key]
    last = None
    for host in ("query1", "query2"):
        for k in range(tries):
            try:
                u = (f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
                     f"?range={rng}&interval={interval}")
                d = json.load(urllib.request.urlopen(
                    urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=25))["chart"]["result"][0]
                closes = (d["indicators"]["adjclose"][0]["adjclose"] if adjusted and d["indicators"].get("adjclose")
                          else d["indicators"]["quote"][0]["close"])
                today = dt.datetime.now(dt.UTC).date()
                pts = [(dt.datetime.fromtimestamp(t, dt.UTC).date(), c) for t, c in zip(d["timestamp"], closes)
                       if c is not None]
                if interval == "1d":
                    pts = [(a, b) for a, b in pts if a < today]
                _cache[key] = pts
                return pts
            except Exception as e:
                last = e
                time.sleep(1.5 * (k + 1))
    raise RuntimeError(f"Yahoo: {symbol} unavailable ({last})")


def pct(a, b):
    return (a / b - 1) * 100


def change(pts, sessions=1):
    return pct(pts[-1][1], pts[-1 - sessions][1])


def cagr(pts, years):
    end_d, end = pts[-1]
    target = end_d - dt.timedelta(days=round(365.25 * years))
    prior = [v for d_, v in pts if d_ <= target]
    if not prior or pts[0][0] > target + dt.timedelta(days=10):
        return None
    return ((end / prior[-1]) ** (1 / years) - 1) * 100


def sma(pts, n):
    return sum(v for _, v in pts[-n:]) / n if len(pts) >= n else None


def week_change(pts):
    """Change over the last 5 sessions (one trading week)."""
    return change(pts, 5) if len(pts) > 5 else None


# ---------------------------------------------------------------- drawing helpers
def header(fig, kicker, title, subtitle):
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.895, kicker.upper(), color=ACCENT, fontsize=15, weight="semibold")
    fig.text(0.06, 0.848, title, color=TEXT, fontsize=34, weight="heavy", va="center")
    fig.text(0.06, 0.805, subtitle, color=MUTED, fontsize=13.5, va="center")


def us_footer(fig, note):
    fig.text(0.5, 0.088, textwrap.fill(f"{note} {US_NOTE} Not a recommendation to buy or sell any security.", 150),
             color=MUTED, fontsize=9.5, ha="center", va="center", linespacing=1.4)
    footer(fig, "generic")


def heat(v, scale):
    import matplotlib.colors as mc
    base, tgt = mc.to_rgb(PANEL), mc.to_rgb(UP if v >= 0 else DOWN)
    a = min(abs(v) / scale, 1.0) * 0.75 + 0.08
    return tuple(b + (t - b) * a for b, t in zip(base, tgt))


def section(fig, y, title):
    fig.text(0.06, y, title, color=GOLD, fontsize=14, weight="bold", va="center")


def tiles(fig, items, top, cols, th, scale, fmt="{:+.2f}%", gap=0.006, left=0.06, width=0.88):
    tw = (width - gap * (cols - 1)) / cols
    for i, (name, v) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = left + c * (tw + gap), top - (r + 1) * th - r * gap
        fig.add_artist(FancyBboxPatch((x, y), tw, th, boxstyle="round,pad=0,rounding_size=0.006",
                                      transform=fig.transFigure, fc=heat(v, scale) if v is not None else PANEL,
                                      ec=BG, lw=1))
        fig.text(x + 0.008, y + th - 0.009, textwrap.fill(name, 15), color=TEXT, fontsize=11, va="top", linespacing=1.1)
        fig.text(x + tw - 0.008, y + 0.009, "–" if v is None else fmt.format(v), color=TEXT, fontsize=15,
                 weight="bold", ha="right", va="bottom")
    rows = -(-len(items) // cols)
    return top - rows * th - (rows - 1) * gap


# ---------------------------------------------------------------- 08:30 US close
def us_close_card(out):
    idx = [(n, yahoo(s)) for n, s in INDICES]
    vix = yahoo("^VIX")
    mag = [(n, change(yahoo(s))) for n, s in MAG7]
    sec = [(n, change(yahoo(s))) for n, s in SECTORS]
    session = idx[0][1][-1][0]
    fig = canvas()
    header(fig, "US market close", f"Wall Street, {session:%a %d %b}",
           f"Last session's moves · indices, Magnificent 7 & S&P sectors · closes as of {session:%d %b %Y}")
    # index strip
    y = 0.765
    w = 0.88 / 5
    for i, (n, pts) in enumerate(idx + [("VIX (fear gauge)", vix)]):
        x = 0.06 + i * w
        v = change(pts)
        col = (UP if v >= 0 else DOWN) if i < 4 else (DOWN if v >= 0 else UP)   # rising VIX = more fear
        fig.add_artist(FancyBboxPatch((x + 0.004, y - 0.095), w - 0.008, 0.095, boxstyle="round,pad=0,rounding_size=0.01",
                                      transform=fig.transFigure, fc=PANEL, ec=GRID))
        fig.text(x + w / 2, y - 0.022, n, color=MUTED, fontsize=11.5, ha="center", va="center")
        fig.text(x + w / 2, y - 0.05, f"{pts[-1][1]:,.0f}" if pts[-1][1] > 100 else f"{pts[-1][1]:.2f}",
                 color=TEXT, fontsize=15, ha="center", va="center", weight="semibold")
        fig.text(x + w / 2, y - 0.077, f"{v:+.2f}%", color=col, fontsize=15, ha="center", va="center", weight="bold")
    # Magnificent 7 bars
    section(fig, 0.635, "Magnificent 7")
    ax = fig.add_axes([0.25, 0.39, 0.69, 0.22])
    ax.set_facecolor(BG)
    mag_sorted = sorted(mag, key=lambda x: x[1])
    ax.barh([n for n, _ in mag_sorted], [v for _, v in mag_sorted],
            color=[UP if v >= 0 else DOWN for _, v in mag_sorted], height=0.62)
    for i, (_, v) in enumerate(mag_sorted):
        ax.text(v + (0.05 if v >= 0 else -0.05), i, f"{v:+.2f}%", va="center", ha="left" if v >= 0 else "right",
                color=TEXT, fontsize=12, weight="bold")
    lim = max(abs(v) for _, v in mag) * 1.45 + 0.3
    ax.set_xlim(-lim, lim)
    ax.axvline(0, color=GRID, lw=1)
    ax.tick_params(axis="y", colors=TEXT, labelsize=13, length=0)
    ax.set_xticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.yaxis.set_tick_params(pad=12)
    fig.text(0.06, 0.5, "", color=TEXT)
    # sectors
    section(fig, 0.36, "S&P 500 sectors")
    tiles(fig, sorted(sec, key=lambda x: x[1], reverse=True), 0.34, 4, 0.052,
          max(1.5, max(abs(v) for _, v in sec)))
    up = sum(v >= 0 for _, v in sec)
    us_footer(fig, f"{up} of 11 sectors up · sectors via SPDR sector ETFs.")
    save(fig, out)
    return {"session": session, "idx": [(n, pts[-1][1], change(pts)) for n, pts in idx],
            "vix": (vix[-1][1], change(vix)), "mag": mag, "sec": sec}


# ---------------------------------------------------------------- 08:30 Saturday: weekly market health
def _breadth(symbols):
    def one(sym):
        try:
            pts = yahoo(sym.replace(".", "-"), "1y")
            return pts if len(pts) > 210 else None
        except Exception:
            return None
    with ThreadPoolExecutor(8) as ex:
        series = [p for p in ex.map(one, symbols) if p]

    def stats(lag):
        n = len(series)
        out = {"n": n}
        for k in (50, 100, 200):
            out[f"above{k}"] = 100 * sum(
                (p[-1 - lag][1] > sum(v for _, v in p[-k - lag:len(p) - lag]) / k) for p in series) / n
        out["adv"] = sum(p[-1 - lag][1] > p[-6 - lag][1] for p in series)
        out["dec"] = n - out["adv"]
        out["nh"] = sum(max(v for _, v in p[-5 - lag:len(p) - lag]) >= max(v for _, v in p[-252 - lag:len(p) - lag])
                        for p in series)
        out["nl"] = sum(min(v for _, v in p[-5 - lag:len(p) - lag]) <= min(v for _, v in p[-252 - lag:len(p) - lag])
                        for p in series)
        return out
    return stats(0), stats(5)


def constituents():
    try:
        txt = urllib.request.urlopen(urllib.request.Request(CONSTITUENTS_URL, headers={"User-Agent": "hbe-social"}),
                                     timeout=30).read().decode()
        (ROOT / "data").mkdir(exist_ok=True)
        (ROOT / "data" / "sp500.csv").write_text(txt)
    except Exception:
        txt = (ROOT / "data" / "sp500.csv").read_text()      # last good copy
    return [r["Symbol"] for r in csv.DictReader(io.StringIO(txt))]


def us_health(out):
    rows = []
    for n, s in INDICES + [("S&P 500 Equal Weight", "RSP")]:
        pts = yahoo(s)
        last = pts[-1][1]
        ma = {k: sma(pts, k) for k in (50, 100, 200)}
        above = {k: last > v for k, v in ma.items()}
        trend = "Bull" if all(above.values()) else ("Bear" if not any(above.values()) else "Caution")
        rows.append((n, last, week_change(pts), above, trend, pts[-1][0]))
    now, prev = _breadth(constituents())
    s_trend = rows[0][4]
    score = ("Risk-on" if s_trend == "Bull" and now["above200"] >= 60 and now["nh"] >= now["nl"] else
             "Risk-off" if s_trend == "Bear" or now["above200"] < 40 else "Neutral")
    col = {"Risk-on": UP, "Neutral": GOLD, "Risk-off": DOWN}[score]
    asof = rows[0][5]
    fig = canvas()
    header(fig, "US market health · weekly", "Is the US market healthy?",
           f"Trend vs 50/100/200-day averages + S&P 500 breadth · week ending {asof:%d %b %Y}")
    fig.add_artist(FancyBboxPatch((0.06, 0.725), 0.88, 0.05, boxstyle="round,pad=0,rounding_size=0.012",
                                  transform=fig.transFigure, fc=col, alpha=0.18, ec=col, lw=1.5))
    fig.text(0.5, 0.75, f"Overall: {score.upper()}", color=col, fontsize=22, weight="heavy", ha="center", va="center")
    # trend table
    hdr_y = 0.69
    cols = [(0.06, "Index", "left"), (0.47, "Week", "right"), (0.585, "50 DMA", "center"), (0.69, "100 DMA", "center"),
            (0.795, "200 DMA", "center"), (0.94, "Trend", "right")]
    for x, lab, ha in cols:
        fig.text(x, hdr_y, lab, color=MUTED, fontsize=12, ha=ha, weight="semibold", va="center")
    y = hdr_y - 0.02
    for n, last, wk, above, trend, _ in rows:
        yc = y - 0.022
        fig.add_artist(FancyBboxPatch((0.05, y - 0.042), 0.90, 0.04, boxstyle="round,pad=0,rounding_size=0.008",
                                      transform=fig.transFigure, fc=PANEL, ec=GRID, lw=0.8, zorder=-1))
        fig.text(0.06 + 0.01, yc, n, color=TEXT, fontsize=14, weight="semibold", va="center")
        fig.text(0.47, yc, f"{wk:+.2f}%", color=UP if wk >= 0 else DOWN, fontsize=14, weight="bold", ha="right", va="center")
        for x, k in ((0.585, 50), (0.69, 100), (0.795, 200)):
            fig.text(x, yc, "●", color=UP if above[k] else DOWN, fontsize=18, ha="center", va="center")
        tc = {"Bull": UP, "Bear": DOWN, "Caution": GOLD}[trend]
        fig.text(0.94, yc, trend, color=tc, fontsize=14, weight="bold", ha="right", va="center")
        y -= 0.046
    # breadth
    section(fig, y - 0.02, f"Breadth: all {now['n']} S&P 500 stocks (this week vs last week)")
    y -= 0.05
    items = [("Above 50-day avg", f"{now['above50']:.0f}%", f"{prev['above50']:.0f}%", now["above50"] >= 50),
             ("Above 100-day avg", f"{now['above100']:.0f}%", f"{prev['above100']:.0f}%", now["above100"] >= 50),
             ("Above 200-day avg", f"{now['above200']:.0f}%", f"{prev['above200']:.0f}%", now["above200"] >= 50),
             ("New 52-week highs vs lows", f"{now['nh']} / {now['nl']}", f"{prev['nh']} / {prev['nl']}", now["nh"] >= now["nl"]),
             ("Advancers vs decliners (week)", f"{now['adv']} / {now['dec']}", f"{prev['adv']} / {prev['dec']}",
              now["adv"] >= now["dec"])]
    for lab, v, pv, good in items:
        yc = y - 0.02
        fig.add_artist(FancyBboxPatch((0.05, y - 0.038), 0.90, 0.036, boxstyle="round,pad=0,rounding_size=0.008",
                                      transform=fig.transFigure, fc=PANEL, ec=GRID, lw=0.8, zorder=-1))
        fig.text(0.07, yc, lab, color=TEXT, fontsize=13.5, va="center")
        fig.text(0.74, yc, v, color=UP if good else DOWN, fontsize=15, weight="bold", ha="right", va="center")
        fig.text(0.93, yc, f"last wk {pv}", color=MUTED, fontsize=11.5, ha="right", va="center")
        y -= 0.042
    us_footer(fig, "Green = above the average, red = below. Bull = above all three; Bear = below all three.")
    save(fig, out)
    return {"asof": asof, "score": score, "rows": rows, "now": now, "prev": prev}


# ---------------------------------------------------------------- 19:00 themes
HZ = {"1y": 1, "3y": 3, "5y": 5}


def us_sector_heatmap(out, horizon="1y"):
    yrs = HZ[horizon]
    items = [(n, cagr(yahoo(s, "10y", adjusted=True), yrs)) for n, s in SECTORS]
    spy = cagr(yahoo("SPY", "10y", adjusted=True), yrs)
    items = sorted([i for i in items if i[1] is not None], key=lambda x: x[1], reverse=True)
    asof = yahoo("SPY", "10y", adjusted=True)[-1][0]
    per = "return" if yrs == 1 else "CAGR"
    fig = canvas()
    header(fig, "US sectors", f"S&P 500 sectors: {yrs}-year {per}",
           f"Total return incl. dividends (SPDR sector ETFs) · best first · as of {asof:%d %b %Y}")
    end = tiles(fig, items, 0.77, 3, 0.12, max(10, max(abs(v) for _, v in items)), fmt="{:+.1f}%")
    fig.add_artist(FancyBboxPatch((0.06, end - 0.075), 0.88, 0.055, boxstyle="round,pad=0,rounding_size=0.01",
                                  transform=fig.transFigure, fc=BG, ec=GOLD, lw=1.5))
    fig.text(0.08, end - 0.0475, "S&P 500 (SPY)", color=TEXT, fontsize=15, weight="semibold", va="center")
    fig.text(0.92, end - 0.0475, f"{spy:+.1f}%", color=UP if spy >= 0 else DOWN, fontsize=17, weight="bold",
             ha="right", va="center")
    beat = sum(v > spy for _, v in items)
    us_footer(fig, f"{beat} of {len(items)} sectors beat the S&P 500 · {'per year' if yrs > 1 else 'last 12 months'}.")
    save(fig, out)
    return {"horizon": horizon, "asof": asof, "items": items, "spy": spy, "beat": beat}


def us_vs_india(out, nifty_points):
    spx = yahoo("^GSPC", "max")
    fx = yahoo("INR=X", "max")
    fxd = dict(fx)
    fx_dates = sorted(fxd)
    import bisect

    def fx_on(d_):
        i = bisect.bisect_right(fx_dates, d_) - 1
        return fxd[fx_dates[i]] if i >= 0 else None
    spx_inr = [(d_, v * fx_on(d_)) for d_, v in spx if d_ >= fx_dates[0] and fx_on(d_)]
    asof = min(spx_inr[-1][0], nifty_points[-1][0])
    cut = lambda pts: [p for p in pts if p[0] <= asof]
    rows = []
    for y_ in (1, 3, 5, 10):
        rows.append((y_, cagr(cut(spx), y_), cagr(cut(spx_inr), y_), cagr(cut(nifty_points), y_),
                     cagr(cut(fx), y_)))
    rows = [r for r in rows if None not in r]
    fig = canvas()
    header(fig, "US vs India", "S&P 500 in rupees vs Nifty 50",
           f"Price returns, per year (CAGR) · rupee returns include USD/INR moves · as of {asof:%d %b %Y}")
    ax = fig.add_axes([0.10, 0.30, 0.84, 0.44])
    ax.set_facecolor(BG)
    import numpy as np
    x = np.arange(len(rows))
    w = 0.26
    series = [("S&P 500 (USD)", [r[1] for r in rows], "#5B6B8C"), ("S&P 500 in ₹", [r[2] for r in rows], ACCENT),
              ("Nifty 50", [r[3] for r in rows], GOLD)]
    for k, (lab, vals, c) in enumerate(series):
        bars = ax.bar(x + (k - 1) * w, vals, w * 0.92, color=c, label=lab)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + (0.4 if v >= 0 else -0.4), f"{v:.1f}%", ha="center",
                    va="bottom" if v >= 0 else "top", color=TEXT, fontsize=11.5, weight="bold")
    ax.set_xticks(x, [f"{r[0]} year{'s' if r[0] > 1 else ''}" for r in rows])
    ax.tick_params(colors=TEXT, labelsize=14, length=0)
    ax.set_yticks([])
    ax.axhline(0, color=GRID, lw=1)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.legend(loc="upper left", frameon=False, labelcolor=TEXT, fontsize=13, ncol=3, bbox_to_anchor=(0, 1.08))
    fxt = "  ·  ".join(f"{r[0]}y: ₹ {'weakened' if r[4] > 0 else 'strengthened'} {abs(r[4]):.1f}%/yr" for r in rows)
    fig.text(0.5, 0.22, f"USD/INR effect — {fxt}", color=MUTED, fontsize=11.5, ha="center")
    us_footer(fig, "Nifty 50: NSE price index. S&P 500: price index, converted at USD/INR.")
    save(fig, out)
    return {"asof": asof, "rows": rows}


def us_drawdown(out):
    rows = []
    for n, s in INDICES + MAG7:
        pts = yahoo(s, "max")
        last_d, last = pts[-1]
        ath_d, ath = max(pts, key=lambda p: p[1])
        yr = [p for p in pts if p[0] > last_d - dt.timedelta(days=365)]
        hi52 = max(v for _, v in yr)
        rows.append((n, pct(last, ath), ath_d, (last_d - ath_d).days, pct(last, hi52), last_d))
    asof = rows[0][5]
    fig = canvas()
    header(fig, "US markets", "How far from the top?",
           f"US indices & Magnificent 7 vs their all-time & 52-week highs · as of {asof:%d %b %Y}")
    xs = [(0.06, "Name", "left"), (0.55, "From ATH", "right"), (0.705, "ATH date", "right"),
          (0.815, "Days", "right"), (0.94, "From 52W hi", "right")]
    y = 0.765
    for x, lab, ha in xs:
        fig.text(x, y, lab, color=MUTED, fontsize=12, ha=ha, weight="semibold")
    y -= 0.015
    for i, (n, dd, ath_d, days, dd52, _) in enumerate(rows):
        if i == len(INDICES):
            section(fig, y - 0.018, "Magnificent 7")
            y -= 0.04
        rh = 0.043
        yc = y - rh / 2
        fig.add_artist(FancyBboxPatch((0.05, y - rh + 0.003), 0.90, rh - 0.006, boxstyle="round,pad=0,rounding_size=0.008",
                                      transform=fig.transFigure, fc=PANEL, ec=GRID, lw=0.8, zorder=-1))
        fig.text(0.07, yc, n, color=TEXT, fontsize=15, weight="semibold", va="center")
        at = dd > -0.5
        fig.text(0.55, yc, "At high" if at else f"{dd:.1f}%", color=UP if at else (DOWN if dd < -10 else GOLD),
                 fontsize=15, weight="bold", ha="right", va="center")
        fig.text(0.705, yc, f"{ath_d:%d %b %y}", color=TEXT, fontsize=13, ha="right", va="center")
        fig.text(0.815, yc, f"{days:,}", color=TEXT, fontsize=13, ha="right", va="center")
        fig.text(0.94, yc, f"{dd52:.1f}%", color=MUTED if dd52 > -5 else DOWN, fontsize=13.5, ha="right", va="center")
        y -= rh
    us_footer(fig, "ATH = all-time closing high · Days = calendar days since the high · prices, not total return.")
    save(fig, out)
    return {"asof": asof, "rows": rows}


def us_style(out, horizon="1y"):
    yrs = HZ[horizon]
    rows = []
    for a, sa, b, sb in STYLES:
        ra = cagr(yahoo(sa, "10y", adjusted=True), yrs)
        rb = cagr(yahoo(sb, "10y", adjusted=True), yrs)
        if ra is not None and rb is not None:
            rows.append((a, ra, b, rb))
    asof = yahoo("SPY", "10y", adjusted=True)[-1][0]
    per = "return" if yrs == 1 else "CAGR"
    fig = canvas()
    header(fig, "US style monitor", f"Which style is winning? ({yrs}-year {per})",
           f"Total return incl. dividends, via US-listed ETFs · as of {asof:%d %b %Y}")
    y = 0.765
    for a, ra, b, rb in rows:
        win_a = ra >= rb
        fig.add_artist(FancyBboxPatch((0.05, y - 0.098), 0.90, 0.092, boxstyle="round,pad=0,rounding_size=0.01",
                                      transform=fig.transFigure, fc=PANEL, ec=GRID, lw=0.8, zorder=-1))
        for k, (lab, v, win) in enumerate(((a, ra, win_a), (b, rb, not win_a))):
            x = 0.08 + k * 0.44
            fig.text(x, y - 0.03, lab, color=TEXT if win else MUTED, fontsize=15, weight="bold" if win else "regular")
            fig.text(x, y - 0.075, f"{v:+.1f}%", color=(UP if v >= 0 else DOWN), fontsize=24, weight="heavy",
                     alpha=1 if win else 0.6)
            if win:
                fig.text(x + 0.30, y - 0.065, "LEADS", color=GOLD, fontsize=12, weight="bold")
        fig.text(0.5, y - 0.05, "vs", color=MUTED, fontsize=14, ha="center", va="center")
        y -= 0.106
    us_footer(fig, f"ETFs: SPYG/SPYV, SPY/IWM, RSP, MTUM, QUAL, USMV · {'per year' if yrs > 1 else 'last 12 months'}.")
    save(fig, out)
    return {"horizon": horizon, "asof": asof, "rows": rows}


def sp500_years(out):
    m = yahoo("^GSPC", "max", "1mo")
    dec = {}
    for d_, v in m:
        dec[d_.year] = v                      # last monthly close of each year
    years = sorted(dec)
    now_d, now_v = yahoo("^GSPC", "1y")[-1]
    rets = [(y_, pct(dec[y_], dec[y_ - 1])) for y_ in years if y_ - 1 in dec and y_ < now_d.year]
    rets = rets[-40:]
    ytd = pct(now_v, dec[now_d.year - 1]) if now_d.year - 1 in dec else None
    fig = canvas()
    header(fig, "S&P 500 · long term", f"{len(rets)} years of S&P 500 returns",
           f"Calendar-year price returns, {rets[0][0]}–{rets[-1][0]} · {now_d.year} YTD to {now_d:%d %b}")
    items = [(str(y_), v) for y_, v in rets] + ([(f"{now_d.year} YTD", ytd)] if ytd is not None else [])
    tiles(fig, items, 0.77, 6, 0.083, 30, fmt="{:+.0f}%", gap=0.005)
    pos = sum(v > 0 for _, v in rets)
    avg = sum(v for _, v in rets) / len(rets)
    us_footer(fig, f"Up in {pos} of {len(rets)} years · average year {avg:+.1f}% · dividends not included.")
    save(fig, out)
    return {"rets": rets, "ytd": ytd, "pos": pos, "avg": avg, "asof": now_d,
            "worst": min(rets, key=lambda x: x[1]), "best": max(rets, key=lambda x: x[1])}


def us_weekly_wrap(out):
    idx = [(n, week_change(yahoo(s))) for n, s in INDICES]
    sec = sorted([(n, week_change(yahoo(s))) for n, s in SECTORS], key=lambda x: x[1], reverse=True)
    mag = sorted([(n, week_change(yahoo(s))) for n, s in MAG7], key=lambda x: x[1], reverse=True)
    end = yahoo("^GSPC")[-1][0]
    start = yahoo("^GSPC")[-6][0]
    fig = canvas()
    header(fig, "US weekly wrap", "The week on Wall Street",
           f"Change over the last 5 sessions · {start:%d %b} → {end:%d %b %Y}")
    section(fig, 0.765, "Indices")
    y = tiles(fig, idx, 0.745, 4, 0.075, max(2, max(abs(v) for _, v in idx)))
    section(fig, y - 0.025, "Magnificent 7")
    y = tiles(fig, mag, y - 0.045, 4, 0.07, max(3, max(abs(v) for _, v in mag)))
    section(fig, y - 0.025, "S&P 500 sectors")
    tiles(fig, sec, y - 0.045, 4, 0.062, max(2, max(abs(v) for _, v in sec)))
    us_footer(fig, "Price change, close to close.")
    save(fig, out)
    return {"start": start, "end": end, "idx": idx, "sec": sec, "mag": mag}
