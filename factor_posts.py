"""Momentum & factor posts from NSE factor indices (price returns, cached in data/indices).

NSE launched most factor indices between 2016 and 2020; earlier history is back-calculated by NSE.
"""
import datetime as dt
import market_posts as mkt
from brand import canvas, brand_badge, footer, save, plt, FancyBboxPatch, BG, PANEL, GRID, TEXT, MUTED, ACCENT, GOLD, UP, DOWN

FACTORS = [("Momentum", "Nifty200 Momentum 30"), ("Quality", "NIFTY200 QUALITY 30"), ("Value", "NIFTY200 VALUE 30"),
           ("Alpha", "NIFTY200 ALPHA 30"), ("Low volatility", "NIFTY100 LOW VOLATILITY 30"), ("Market (Nifty 200)", "Nifty 200")]
NOTE = ("NSE factor indices, price returns. History before each index's launch (mostly 2016-2020) is "
        "back-calculated by NSE.")


def _series():
    look = {r["name"].lower(): r for r in mkt.INDEX_LIST}
    return [(label, mkt.series(look[name.lower()])) for label, name in FACTORS]


def cagr(pts, years):
    end_d, end = pts[-1]
    target = end_d.replace(year=end_d.year - years) if not (end_d.month == 2 and end_d.day == 29) else \
        end_d.replace(year=end_d.year - years, day=28)
    prior = [v for d_, v in pts if d_ <= target]
    if not prior:
        return None
    return ((end / prior[-1]) ** (1 / years) - 1) * 100


def max_dd(pts, since=None):
    peak, worst, wd = 0, 0, None
    for d_, v in pts:
        if since and d_ < since:
            continue
        peak = max(peak, v)
        dd = v / peak - 1
        if dd < worst:
            worst, wd = dd, d_
    return worst * 100, wd


def header(fig, kicker, title, subtitle):
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.895, kicker.upper(), color=ACCENT, fontsize=15, weight="semibold")
    fig.text(0.06, 0.848, title, color=TEXT, fontsize=34, weight="heavy", va="center")
    fig.text(0.06, 0.805, subtitle, color=MUTED, fontsize=13.5, va="center")


def finish(fig, extra, out):
    fig.text(0.5, 0.088, f"{extra} {NOTE}", color=MUTED, fontsize=9.5, ha="center", va="center", wrap=True)
    footer(fig, "generic")
    return save(fig, out)


def factor_scoreboard(out):
    rows = []
    for label, pts in _series():
        common_start = dt.date(2005, 4, 1)
        yrs = (pts[-1][0] - common_start).days / 365.25
        first = [v for d_, v in pts if d_ >= common_start][0]
        rows.append((label, [cagr(pts, y) for y in (1, 3, 5, 10)] + [((pts[-1][1] / first) ** (1 / yrs) - 1) * 100],
                     max_dd(pts, common_start)[0]))
    asof = _series()[0][1][-1][0]
    fig = canvas()
    header(fig, "Momentum & factors", "Factor scoreboard: India",
           f"Nifty 200 factor indices vs the market · CAGR % · as of {asof:%d %b %Y}")
    cols = ["1Y", "3Y", "5Y", "10Y", "Since 2005", "Worst fall"]
    xs = [0.45, 0.535, 0.62, 0.705, 0.815, 0.94]
    y = 0.765
    for x, c in zip(xs, cols):
        fig.text(x, y, c, color=MUTED, fontsize=12, ha="right", weight="semibold")
    y -= 0.02
    mkt_row = rows[-1][1]
    for i, (label, vals, dd) in enumerate(rows):
        rh = 0.07
        is_mkt = i == len(rows) - 1
        fig.add_artist(FancyBboxPatch((0.05, y - rh + 0.004), 0.90, rh - 0.008, boxstyle="round,pad=0,rounding_size=0.01",
                                      transform=fig.transFigure, fc=BG if is_mkt else PANEL,
                                      ec=GOLD if is_mkt else GRID, lw=1.5 if is_mkt else 0.8, zorder=-1))
        yc = y - rh / 2
        fig.text(0.07, yc, label, color=TEXT, fontsize=16, weight="bold", va="center")
        for j, (x, v) in enumerate(zip(xs, vals)):
            beat = (not is_mkt) and v is not None and mkt_row[j] is not None and v > mkt_row[j]
            fig.text(x, yc, "–" if v is None else f"{v:.1f}", color=UP if beat else (TEXT if is_mkt else MUTED),
                     fontsize=16, weight="bold" if beat else "regular", ha="right", va="center")
        fig.text(xs[-1], yc, f"{dd:.0f}%", color=DOWN, fontsize=15, ha="right", va="center")
        y -= rh
    fig.text(0.07, y - 0.03, "Green = beat the market over that period. Worst fall = deepest peak-to-trough drop since 2005.",
             color=MUTED, fontsize=12)
    finish(fig, "Not a recommendation.", out)
    best10 = max(rows[:-1], key=lambda r: r[1][3] or -99)
    return {"asof": asof, "rows": rows, "best10": best10}


def factor_years(out, n_years=12):
    ser = _series()
    asof = ser[0][1][-1][0]
    years = list(range(asof.year - n_years, asof.year)) + [asof.year]

    def yret(pts, y):
        end = [v for d_, v in pts if d_.year == y]
        start = [v for d_, v in pts if d_.year == y - 1]
        return (end[-1] / start[-1] - 1) * 100 if end and start else None
    grid = {(lab, y): yret(pts, y) for lab, pts in ser for y in years}
    fig = canvas()
    header(fig, "Momentum & factors", "Factors take turns",
           f"Calendar-year returns of Nifty 200 factor indices · {years[0]}–{asof.year} (YTD) · best each year outlined")
    labels = [l for l, _ in ser]
    x0, cw = 0.20, 0.74 / len(labels)
    top, rh = 0.765, 0.046
    for j, lab in enumerate(labels):
        fig.text(x0 + j * cw + cw / 2, top, lab.replace(" (Nifty 200)", "\n(Nifty 200)").replace("Low volatility", "Low\nvolatility"),
                 color=MUTED, fontsize=11, ha="center", va="center", weight="semibold")
    for i, y in enumerate(years):
        yy = top - 0.045 - (i + 1) * rh
        fig.text(0.07, yy + rh / 2, f"{y}{' YTD' if y == asof.year else ''}", color=TEXT, fontsize=13.5, va="center")
        vals = [grid[(lab, y)] for lab in labels]
        best = max((v for v in vals[:-1] if v is not None), default=None)
        for j, v in enumerate(vals):
            if v is None:
                continue
            import matplotlib.colors as mc
            base, tgt = mc.to_rgb(PANEL), mc.to_rgb(UP if v >= 0 else DOWN)
            a = min(abs(v) / 50, 1) * 0.75 + 0.08
            col = tuple(b + (t - b) * a for b, t in zip(base, tgt))
            fig.add_artist(FancyBboxPatch((x0 + j * cw + 0.003, yy + 0.003), cw - 0.006, rh - 0.006,
                                          boxstyle="round,pad=0,rounding_size=0.005", transform=fig.transFigure, fc=col,
                                          ec=GOLD if (v == best and j < len(vals) - 1) else BG,
                                          lw=2 if (v == best and j < len(vals) - 1) else 1))
            fig.text(x0 + j * cw + cw / 2, yy + rh / 2, f"{v:+.0f}%", color=TEXT, fontsize=12.5, weight="bold",
                     ha="center", va="center")
    wins = {lab: 0 for lab in labels[:-1]}
    for y in years[:-1]:
        vals = {lab: grid[(lab, y)] for lab in labels[:-1] if grid[(lab, y)] is not None}
        if vals:
            wins[max(vals, key=vals.get)] += 1
    finish(fig, "Not a recommendation.", out)
    return {"asof": asof, "years": years, "wins": wins}


def momentum_drawdown(out):
    ser = dict(_series())
    mom, mkt200 = ser["Momentum"], ser["Market (Nifty 200)"]
    start = dt.date(2005, 4, 1)

    def underwater(pts):
        peak, out_ = 0, []
        for d_, v in pts:
            if d_ < start:
                continue
            peak = max(peak, v)
            out_.append((d_, (v / peak - 1) * 100))
        return out_
    um, uk = underwater(mom), underwater(mkt200)
    asof = mom[-1][0]
    fig = canvas()
    header(fig, "Momentum & factors", "The price of momentum: deeper falls",
           f"Fall from previous peak: Nifty200 Momentum 30 vs Nifty 200 · 2005–{asof.year}")
    ax = fig.add_axes([0.10, 0.36, 0.84, 0.40])
    ax.set_facecolor(BG)
    ax.fill_between([d for d, _ in um], [v for _, v in um], 0, color=ACCENT, alpha=0.35, label="Momentum 30")
    ax.plot([d for d, _ in uk], [v for _, v in uk], color=GOLD, lw=1.6, label="Nifty 200")
    ax.set_ylim(min(v for _, v in um + uk) * 1.08, 2)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.grid(color=GRID, lw=0.8)
    ax.tick_params(colors=MUTED, labelsize=11, length=0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.legend(loc="lower right", frameon=False, labelcolor=TEXT, fontsize=13)
    mdd_m, d_m = max_dd(mom, start)
    mdd_k, d_k = max_dd(mkt200, start)
    rets = (cagr(mom, 10), cagr(mkt200, 10))
    stats = [("Worst fall: Momentum", f"{mdd_m:.0f}%", DOWN), ("Worst fall: Nifty 200", f"{mdd_k:.0f}%", DOWN),
             ("Now: Momentum", f"{um[-1][1]:.1f}%", MUTED), ("Now: Nifty 200", f"{uk[-1][1]:.1f}%", MUTED)]
    w = 0.88 / 4
    for i, (lab, v, c) in enumerate(stats):
        x = 0.06 + i * w
        fig.add_artist(FancyBboxPatch((x + 0.004, 0.22), w - 0.008, 0.09, boxstyle="round,pad=0,rounding_size=0.01",
                                      transform=fig.transFigure, fc=PANEL, ec=GRID))
        fig.text(x + w / 2, 0.285, lab, color=MUTED, fontsize=11.5, ha="center", va="center")
        fig.text(x + w / 2, 0.25, v, color=c, fontsize=20, weight="bold", ha="center", va="center")
    fig.text(0.5, 0.175, f"10-year CAGR: Momentum {rets[0]:.1f}% vs Nifty 200 {rets[1]:.1f}%. Higher returns came with deeper falls.",
             color=TEXT, fontsize=13.5, ha="center")
    finish(fig, "Not a recommendation.", out)
    return {"asof": asof, "mdd_m": mdd_m, "d_m": d_m, "mdd_k": mdd_k, "d_k": d_k, "now_m": um[-1][1],
            "now_k": uk[-1][1], "r10": rets}
