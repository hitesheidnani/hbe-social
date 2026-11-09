"""Mutual fund / PMS / SIF post images built from FundNavigator data.

Data comes from the FundNavigator site's nightly JSON (funds.hbecapital.net/data/*.json),
or from a local checkout when DATA_DIR is set.
"""
import json, os, re, datetime as dt, urllib.request
from pathlib import Path
from statistics import median

from brand import (canvas, brand_badge, footer, save, plt, FancyBboxPatch,
                   BG, PANEL, GRID, TEXT, MUTED, ACCENT, GOLD, UP, DOWN)

DATA_URL = "https://funds.hbecapital.net/data"
DATA_DIR = os.environ.get("DATA_DIR")  # e.g. /home/hbe/projects/fundnavigator/web/public/data

PAST_PERF = "Past performance may or may not be sustained in future."

HORIZON_LABEL = {"1m": "1-month", "3m": "3-month", "6m": "6-month", "1y": "1-year", "2y": "2-year",
                 "3y": "3-year", "4y": "4-year", "5y": "5-year", "7y": "7-year", "10y": "10-year",
                 "15y": "15-year", "si": "since-inception"}

# FundNavigator category -> (short label, benchmark key in dashboard.json)
CATEGORIES = {
    "Equity Scheme - Small Cap Fund": ("Small Cap", "NIFTY SMALLCAP 250"),
    "Equity Scheme - Mid Cap Fund": ("Mid Cap", "NIFTY MIDCAP 150"),
    "Equity Scheme - Large Cap Fund": ("Large Cap", "NIFTY 500"),
    "Equity Scheme - Flexi Cap Fund": ("Flexi Cap", "NIFTY 500"),
    "Equity Scheme - Multi Cap Fund": ("Multi Cap", "NIFTY 500"),
    "Equity Scheme - Large & Mid Cap Fund": ("Large & Mid Cap", "NIFTY 500"),
    "Equity Scheme - Focused Fund": ("Focused", "NIFTY 500"),
    "Equity Scheme - Value Fund": ("Value", "NIFTY 500"),
    "Equity Scheme - ELSS": ("ELSS (Tax Saver)", "NIFTY 500"),
}


DATA_URLS = [DATA_URL, "https://fundnavigator.pages.dev/data"]
_cache = {}


# Nifty 500 is the official benchmark only for some categories; elsewhere it is a broad-market comparison
BROAD_ONLY = {"Large Cap", "Multi Cap", "Large & Mid Cap"}


def load(name):
    if name in _cache:
        return _cache[name]
    if DATA_DIR:
        _cache[name] = json.load(open(Path(DATA_DIR) / name))
        return _cache[name]
    last = None
    for base in DATA_URLS:
        try:
            req = urllib.request.Request(f"{base}/{name}", headers={"User-Agent": "hbe-social/1.0"})
            _cache[name] = json.load(urllib.request.urlopen(req, timeout=60))
            return _cache[name]
        except Exception as e:      # try the next mirror
            last = e
    raise RuntimeError(f"could not load {name}: {last}")


ACRONYMS = {"HDFC", "ICICI", "SBI", "UTI", "HSBC", "DSP", "LIC", "PGIM", "ITI", "JM", "PMS", "LLP", "AMC",
            "IDFC", "IIFL", "BSE", "NSE", "TRI", "ESG", "ELSS", "SIF", "PPFAS", "AAA", "II", "III", "KRIIS", "360"}


def tidy_case(n):
    """Fix SHOUTED words (e.g. 'BANDHAN Small Cap', 'BANK OF INDIA'), keeping known acronyms."""
    out = []
    for w in n.split():
        if w.isupper() and w not in ACRONYMS and (len(w) > 3 or n.isupper()):
            w = w.capitalize()
        out.append(w)
    return " ".join(out).replace("Bank Of India", "Bank of India")


def dedupe(funds):
    """Keep the best-ranked scheme when two schemes share a display name (e.g. merged/legacy plans)."""
    seen, out = set(), []
    for f in funds:
        k = short_name(f["n"]).lower()
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def short_name(n):
    n = re.sub(r"\s*\((erstwhile|formerly|earlier)[^)]*\)?", "", n, flags=re.I)
    n = re.split(r"\s*[-–]\s*(Regular|Growth|Reg\b)", n, flags=re.I)[0]
    n = tidy_case(re.sub(r"\s+", " ", n).strip())
    return n if len(n) <= 40 else n[:38].rstrip() + "…"


def fmt(v, digits=1):
    return "—" if v is None else f"{v:+.{digits}f}%"


def nice_date(s):
    return dt.date.fromisoformat(s).strftime("%d %b %Y")


def header(fig, kicker, title, subtitle):
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.895, kicker.upper(), color=ACCENT, fontsize=15, weight="semibold")
    fig.text(0.06, 0.845, title, color=TEXT, fontsize=36, weight="heavy", va="center")
    fig.text(0.06, 0.800, subtitle, color=MUTED, fontsize=13.5, va="center")


PMS_DISCLAIMER = ("PMS investments are subject to market risks. Returns as reported by providers to APMI; "
                  "not verified by HBE Capital. Educational only, not a recommendation.")


def mf_footer(fig, source, pms=False):
    fig.text(0.5, 0.083, f"{PAST_PERF} Source: {source}", color=MUTED, fontsize=9.5, ha="center")
    footer(fig, "pms" if pms else "mf")


def row(fig, y, h, rank, title, sub, value, highlight=False):
    fig.add_artist(FancyBboxPatch((0.06, y), 0.88, h, boxstyle="round,pad=0,rounding_size=0.012",
                                  transform=fig.transFigure, fc=PANEL if not highlight else BG,
                                  ec=GOLD if highlight else GRID, lw=1.6 if highlight else 1, zorder=-1))
    cy = y + h / 2
    k = min(1.0, 0.55 + h * 6)   # font scale: 1.0 for tall rows, ~0.87 for 10-row cards
    if rank is not None:
        fig.text(0.095, cy, f"{rank}", color=GOLD, fontsize=24 * k, weight="heavy", va="center", ha="center")
    x = 0.14 if rank is not None else 0.09
    fig.text(x, cy + h * 0.17, title, color=TEXT, fontsize=19 * k, weight="semibold", va="center")
    fig.text(x, cy - h * 0.24, sub, color=MUTED, fontsize=12.5 * max(k, 0.9), va="center")
    col = MUTED if value is None else (UP if value >= 0 else DOWN)
    fig.text(0.915, cy, fmt(value), color=col, fontsize=24 * k, weight="bold", va="center", ha="right")


# 10-row layout shared by every ranking card
TOP, RH, GAP = 0.775, 0.053, 0.006
N = 10


def row_y(i):
    """Bottom edge of row i (0-based)."""
    return TOP - (i + 1) * RH - i * GAP


# ---------------------------------------------------------------- templates
def leaderboard(category, horizon, out, n=N, metric="cagr"):
    """Top-n funds in an AMFI category by trailing CAGR (or SIP XIRR) vs the category benchmark."""
    rk, dash = load("rankings.json"), load("dashboard.json")
    label, bkey = CATEGORIES[category]
    funds = [f for f in rk["funds"] if f["k"] == category and f[metric].get(horizon) is not None]
    funds.sort(key=lambda f: f[metric][horizon], reverse=True)
    funds = dedupe(funds)
    if len(funds) < n:
        raise ValueError(f"only {len(funds)} funds with {horizon} history in {category}")
    bench = dash["benchmarks"][bkey]
    bval = bench["TRI"]["tr"].get(horizon) if metric == "cagr" else None
    vals = [f[metric][horizon] for f in funds]
    beat = sum(v > bval for v in vals) if bval is not None else None

    fig = canvas(1080, 1350)
    what = "returns (CAGR)" if metric == "cagr" and horizon not in ("3m", "6m") else (
        "SIP returns (XIRR)" if metric == "xirr" else "returns")
    header(fig, f"{label} funds", f"Top {n} by {HORIZON_LABEL[horizon]} {what.split(' (')[0]}",
           f"{what} · Regular plan, Growth · NAV as of {nice_date(rk['asof'])}")
    for i, f in enumerate(funds[:n]):
        row(fig, row_y(i), RH, i + 1, short_name(f["n"]), f["h"], f[metric][horizon])
    y = row_y(n) - 0.006
    if bval is not None:
        sub = "Broad market, for comparison" if label in BROAD_ONLY else "Category benchmark"
        row(fig, y, RH, None, f"{bench['name']} TRI", sub, bval, highlight=True)
    y -= 0.022
    stat = f"Category median: {fmt(median(vals))}  ·  {len(vals)} funds with {HORIZON_LABEL[horizon]} history"
    if beat is not None:
        stat = (f"{beat} of {len(vals)} funds beat the "
                f"{'Nifty 500' if label in BROAD_ONLY else 'index'}  ·  Median: {fmt(median(vals))}")
    fig.text(0.5, y, stat, color=TEXT, fontsize=13.5, ha="center", weight="medium")
    mf_footer(fig, "AMFI NAVs, NSE Indices. Computed by HBE Capital FundNavigator.")
    save(fig, out)
    return {"category": label, "horizon": horizon, "metric": metric, "asof": rk["asof"],
            "top": [(short_name(f["n"]), f[metric][horizon]) for f in funds[:n]],
            "benchmark": (bench["name"] + " TRI", bval), "broad": label in BROAD_ONLY,
            "beat": beat, "count": len(vals), "median": median(vals)}


def sip_value(xirr_pct, monthly=10000, months=60):
    """Approximate end value of a monthly SIP growing at the given annual XIRR."""
    r = (1 + xirr_pct / 100) ** (1 / 12) - 1
    return sum(monthly * (1 + r) ** (months - k) for k in range(months))


def sip_card(category, out, years=5, monthly=10000, n=N):
    rk = load("rankings.json")
    label, _ = CATEGORIES[category]
    h = f"{years}y"
    funds = [f for f in rk["funds"] if f["k"] == category and f["xirr"].get(h) is not None]
    funds.sort(key=lambda f: f["xirr"][h], reverse=True)
    funds = dedupe(funds)
    invested = monthly * years * 12
    fig = canvas(1080, 1350)
    header(fig, f"{label} funds · SIP", f"₹{monthly:,}/month for {years} years",
           f"₹{invested / 1e5:.1f} lakh invested · top {n} by SIP XIRR · NAV as of {nice_date(rk['asof'])}")
    rows = []
    for i, f in enumerate(funds[:n]):
        v = sip_value(f["xirr"][h], monthly, years * 12)
        rows.append((short_name(f["n"]), f["xirr"][h], v))
        row(fig, row_y(i), RH, i + 1, short_name(f["n"]), f"XIRR {fmt(f['xirr'][h])}", None)
        fig.texts[-1].set_text(f"₹{v / 1e5:.1f} L")
        fig.texts[-1].set_color(UP)
    med = median(f["xirr"][h] for f in funds)
    y = row_y(n - 1) - 0.035
    fig.text(0.5, y, f"Category median SIP XIRR: {fmt(med)}  →  ≈ ₹{sip_value(med, monthly, years * 12) / 1e5:.1f} L",
             color=TEXT, fontsize=15, ha="center", weight="medium")
    fig.text(0.5, y - 0.035, "End values are approximate, computed from each fund's SIP XIRR.",
             color=MUTED, fontsize=11.5, ha="center")
    mf_footer(fig, "AMFI NAVs. Computed by HBE Capital FundNavigator.")
    save(fig, out)
    return {"category": label, "years": years, "monthly": monthly, "asof": rk["asof"], "rows": rows, "median": med}


def pms_leaderboard(horizon, out, n=N, min_aum=100, kind="Equity"):
    p = load("pms.json")
    i = p["horizons"].index(horizon)
    rows = [s for s in p["strategies"] if s["t"] == kind and (s["aum"] or 0) >= min_aum
            and s["r"][i] is not None]
    rows.sort(key=lambda s: s["r"][i], reverse=True)
    fig = canvas(1080, 1350)
    header(fig, f"PMS · {kind}", f"Top {n} by {HORIZON_LABEL[horizon]} returns",
           f"Strategies with AUM ≥ ₹{min_aum} cr · as reported to APMI · month-end {nice_date(p['asof'])}")
    for k, s in enumerate(rows[:n]):
        row(fig, row_y(k), RH, k + 1, short_name(s["n"]), f"{short_name(s['p'])} · AUM ₹{s['aum']:,.0f} cr", s["r"][i])
    y = row_y(n) - 0.006
    bv = lambda b: p["benchmarks"].get(b, [None] * 9)[i] if i < len(p["horizons"]) - 1 else None
    row(fig, y, RH, None, "BSE 500 TRI", f"Benchmark  ·  Nifty 50 TRI {fmt(bv('Nifty 50 TRI'))}",
        bv("BSE 500 TRI"), highlight=True)
    fig.text(0.5, y - 0.022, f"{len(rows)} {kind.lower()} strategies screened · 1Y+ returns annualised · "
             "min. investment ₹50 lakh", color=MUTED, fontsize=12, ha="center")
    mf_footer(fig, "APMI, month-end data.", pms=True)
    save(fig, out)
    return {"horizon": horizon, "asof": p["asof"], "top": [(s["n"], s["p"], s["r"][i]) for s in rows[:n]],
            "screened": len(rows)}


def sif_tracker(out, horizon="3m"):
    rk = load("rankings.json")
    sifs = [f for f in rk["funds"] if f["k"].startswith("SIF")]
    have = [f for f in sifs if f["cagr"].get(horizon) is not None]
    have.sort(key=lambda f: f["cagr"][horizon], reverse=True)
    fig = canvas(1080, 1350)
    header(fig, "Specialised Investment Funds", f"SIF tracker: {HORIZON_LABEL[horizon]} returns",
           f"{len(sifs)} SIF strategies live · Regular, Growth · NAV as of {nice_date(rk['asof'])}")
    n = min(len(have), N)
    for k, f in enumerate(have[:n]):
        row(fig, row_y(k), RH, k + 1, short_name(f["n"]), f["k"].replace("SIF - ", ""), f["cagr"][horizon])
    y = row_y(n - 1) - 0.035
    fig.text(0.5, y, "SIFs are new (2025) and need ₹10 lakh minimum. Short track records, so judge with care.",
             color=MUTED, fontsize=12.5, ha="center")
    mf_footer(fig, "AMFI NAVs. Computed by HBE Capital FundNavigator.")
    save(fig, out)
    return {"horizon": horizon, "asof": rk["asof"], "count": len(sifs), "with_data": len(have),
            "top": [(short_name(f["n"]), f["cagr"][horizon]) for f in have[:n]]}


def momentum_tracker(out, horizon="1y", n=N):
    """Top-n momentum funds (active, index, ETF) by trailing return vs the broad market."""
    rk, dash = load("rankings.json"), load("dashboard.json")
    kind = {"Other Scheme - Index Funds": "Index fund", "Other Scheme - ETFs": "ETF",
            "Other Scheme - FoF Domestic": "Fund of funds"}
    funds = [f for f in rk["funds"] if "momentum" in f["n"].lower() and f["cagr"].get(horizon) is not None]
    funds.sort(key=lambda f: f["cagr"][horizon], reverse=True)
    funds = dedupe(funds)
    total = sum("momentum" in f["n"].lower() for f in rk["funds"])
    bench = dash["benchmarks"]["NIFTY 500"]
    bval = bench["TRI"]["tr"].get(horizon)
    fig = canvas(1080, 1350)
    header(fig, "Momentum investing", f"Momentum funds: {HORIZON_LABEL[horizon]} returns",
           f"Top {n} of {total} momentum funds, index funds & ETFs · NAV as of {nice_date(rk['asof'])}")
    for i, f in enumerate(funds[:n]):
        row(fig, row_y(i), RH, i + 1, short_name(f["n"]), f"{kind.get(f['k'], 'Active fund')} · {f['h']}",
            f["cagr"][horizon])
    y = row_y(n) - 0.006
    row(fig, y, RH, None, "Nifty 500 TRI", "Broad market, for comparison", bval, highlight=True)
    beat = sum(f["cagr"][horizon] > bval for f in funds) if bval is not None else None
    fig.text(0.5, y - 0.022, f"{beat} of {len(funds)} momentum funds beat the broad market over this period",
             color=TEXT, fontsize=13.5, ha="center", weight="medium")
    mf_footer(fig, "AMFI NAVs, NSE Indices. Computed by HBE Capital FundNavigator.")
    save(fig, out)
    return {"horizon": horizon, "asof": rk["asof"], "count": len(funds), "total": total,
            "top": [(short_name(f["n"]), f["cagr"][horizon]) for f in funds[:n]],
            "benchmark": ("Nifty 500 TRI", bval), "beat": beat}
