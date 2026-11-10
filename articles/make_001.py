"""Issue #1 charts: share of active funds beating their benchmark, by category and period."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from brand import canvas, brand_badge, save, plt, FancyBboxPatch, BG, PANEL, GRID, TEXT, MUTED, ACCENT, GOLD, UP, DOWN, EDU, ARN

DATA, OUT = Path(sys.argv[1]), Path(sys.argv[2])
rk, dash = json.load(open(DATA / "rankings.json")), json.load(open(DATA / "dashboard.json"))
CATS = [("Small Cap", "Equity Scheme - Small Cap Fund", "NIFTY SMALLCAP 250"),
        ("Mid Cap", "Equity Scheme - Mid Cap Fund", "NIFTY MIDCAP 150"),
        ("Flexi Cap", "Equity Scheme - Flexi Cap Fund", "NIFTY 500"),
        ("ELSS", "Equity Scheme - ELSS", "NIFTY 500"),
        ("Value", "Equity Scheme - Value Fund", "NIFTY 500"),
        ("Focused", "Equity Scheme - Focused Fund", "NIFTY 500")]
HZ = ["3y", "5y", "7y", "10y"]
grid = {}
for label, k, b in CATS:
    for h in HZ:
        bv = dash["benchmarks"][b]["TRI"]["tr"][h]
        v = [f["cagr"][h] for f in rk["funds"] if f["k"] == k and f["cagr"].get(h) is not None]
        grid[label, h] = (sum(x > bv for x in v), len(v))
tot = {h: (sum(grid[c[0], h][0] for c in CATS), sum(grid[c[0], h][1] for c in CATS)) for h in HZ}

# --- chart (landscape, for the article body)
fig = canvas(1600, 1000)
brand_badge(fig, 0.04, 0.94, size=0.9)
fig.text(0.04, 0.855, "How many active funds beat their index?", color=TEXT, fontsize=34, weight="heavy", va="center")
fig.text(0.04, 0.80, f"Share of funds with a higher CAGR than their benchmark (TRI) · Regular plans · NAV as of "
         f"{rk['asof'][8:]}-{rk['asof'][5:7]}-{rk['asof'][:4]}", color=MUTED, fontsize=15, va="center")
x0, y0, cw, rh = 0.28, 0.72, 0.17, 0.082
for j, h in enumerate(HZ):
    fig.text(x0 + j * cw + cw / 2, y0, h.replace("y", " years"), color=MUTED, fontsize=16, ha="center", weight="semibold")
rows = [(c[0], c[2]) for c in CATS] + [("All six categories", None)]
for i, (label, b) in enumerate(rows):
    y = y0 - 0.03 - (i + 1) * rh
    bold = b is None
    fig.text(0.04, y + rh / 2 - 0.008, label, color=TEXT, fontsize=19, weight="bold" if bold else "semibold", va="center")
    if b:
        fig.text(0.04, y + rh / 2 - 0.035, f"vs {b.title().replace('Nifty', 'Nifty')} TRI", color=MUTED, fontsize=12, va="center")
    for j, h in enumerate(HZ):
        beat, n = tot[h] if bold else grid[label, h]
        share = beat / n
        col = UP if share >= 0.5 else DOWN
        a = 0.15 + abs(share - 0.5) * 1.3
        fig.add_artist(FancyBboxPatch((x0 + j * cw + 0.006, y + 0.006), cw - 0.012, rh - 0.012,
                                      boxstyle="round,pad=0,rounding_size=0.01", transform=fig.transFigure,
                                      fc=col, alpha=min(a, 0.85), ec=GOLD if bold else "none", lw=2))
        fig.text(x0 + j * cw + cw / 2, y + rh / 2 + 0.008, f"{share * 100:.0f}%", color=TEXT, fontsize=22,
                 weight="bold", ha="center", va="center")
        fig.text(x0 + j * cw + cw / 2, y + rh / 2 - 0.025, f"{beat} of {n}", color=TEXT, fontsize=12.5,
                 ha="center", va="center", alpha=0.85)
fig.text(0.04, 0.05, f"Source: AMFI NAVs, NSE Indices, computed by HBE Capital FundNavigator. Only funds that still exist are "
         f"counted (survivorship bias flatters the results). Past performance may or may not be sustained in future. {EDU} "
         f"AMFI-registered MFD · {ARN}", color=MUTED, fontsize=10.5, va="center", wrap=True)
save(fig, OUT / "chart_beat_rates")

# --- cover image (LinkedIn article cover, 1920x1080)
fig = canvas(1920, 1080)
brand_badge(fig, 0.05, 0.9, size=1.2)
fig.text(0.05, 0.72, "THE DISCIPLINED INVESTOR  ·  ISSUE #1", color=ACCENT, fontsize=24, weight="bold")
fig.text(0.05, 0.50, "How many active funds\nactually beat their index?", color=TEXT, fontsize=64, weight="heavy",
         va="center", linespacing=1.12)
fig.text(0.05, 0.27, f"Over 10 years: {tot['10y'][0]} of {tot['10y'][1]}.", color=GOLD, fontsize=40, weight="bold")
fig.text(0.05, 0.08, "Data-driven notes on mutual funds, markets & investor psychology", color=MUTED, fontsize=22)
save(fig, OUT / "cover")
json.dump({f"{k[0]}|{k[1]}": v for k, v in grid.items()} | {f"ALL|{h}": tot[h] for h in HZ},
          open(OUT / "numbers.json", "w"), indent=1)
print(tot)
