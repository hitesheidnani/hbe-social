"""Build one day's posts: images + captions + schedule -> posts/YYYY-MM-DD/plan.json

Usage:  python daily.py [YYYY-MM-DD]
Daily mix (IST):
  09:00  market psychology quote
  12:30  top-10 leaderboard, long horizon (5y / 7y / 10y), rotating category
  17:30  weekday feature: SIP card (Mon, Fri), SIF (Tue), momentum funds (Wed, Sun), PMS (Thu, Sat)
  20:00  top-10 leaderboard, shorter horizon (1y / 2y / 3y), rotating category
Returns for periods under 1 year are never shown.
"""
import json, sys, datetime as dt
from pathlib import Path

import mf_posts as mf
from brand import quote_card, ARN, MF_DISCLAIMER

ROOT = Path(__file__).parent
SLOTS = {"psych": "09:00", "long": "12:30", "feature": "17:30", "short": "20:00"}

CATS = [  # rotation order for leaderboards
    "Equity Scheme - Small Cap Fund", "Equity Scheme - Flexi Cap Fund", "Equity Scheme - Mid Cap Fund",
    "Equity Scheme - Large Cap Fund", "Equity Scheme - ELSS", "Equity Scheme - Large & Mid Cap Fund",
    "Equity Scheme - Multi Cap Fund", "Equity Scheme - Value Fund", "Equity Scheme - Focused Fund",
]
SIP_CATS = ["Equity Scheme - Small Cap Fund", "Equity Scheme - Mid Cap Fund", "Equity Scheme - Flexi Cap Fund",
            "Equity Scheme - Large Cap Fund", "Equity Scheme - ELSS", "Equity Scheme - Large & Mid Cap Fund"]
# weekday (Mon=0) -> feature for the 17:30 slot
# Rule: never show returns for periods under 1 year.
FEATURE = {0: ("sip", 5), 1: ("sif", "1y"), 2: ("momentum", "1y"), 3: ("pms", "1y"),
           4: ("sip", 10), 5: ("pms", "3y"), 6: ("momentum", "3y")}
LONG_HORIZONS = ["5y", "10y", "7y"]
SHORT_HORIZONS = ["1y", "3y", "2y"]
MIN_SIFS = 5   # show the SIF tracker only once this many SIFs have a 1-year record

# Instagram allows at most 5 hashtags; mix broad reach with niche intent.
TAGS = {
    "psych": "#tradingpsychology #stockmarket #investing #markdouglas #mindset",
    "sip": "#sip #mutualfunds #sipinvestment #wealthcreation #personalfinance",
    "momentum": "#momentuminvesting #mutualfunds #indexfunds #stockmarketindia #investing",
    "pms": "#pms #portfoliomanagement #wealthmanagement #stockmarketindia #investing",
    "sif": "#sif #mutualfunds #longshort #wealthmanagement #investing",
}
CAT_TAG = {"Small Cap": "#smallcapfunds", "Mid Cap": "#midcapfunds", "Large Cap": "#largecapfunds",
           "Flexi Cap": "#flexicapfunds", "ELSS (Tax Saver)": "#elss", "Multi Cap": "#multicapfunds",
           "Large & Mid Cap": "#largeandmidcap", "Value": "#valueinvesting", "Focused": "#focusedfunds"}
ENGAGE = "🔖 Save this for your next review · 📤 Share with someone who invests in mutual funds"
YEAR = __import__("datetime").date.today().year
MF_FOOT = (f"Past performance may or may not be sustained in future. This is not a recommendation to buy or "
           f"sell any fund. {MF_DISCLAIMER}\nHBE Capital · AMFI-registered Mutual Fund Distributor · {ARN}")
LINK = "📊 Full rankings for every category: link in bio"


def pct(v):
    return f"{v:.1f}%" if v is not None else "n/a"


def numbered(rows):
    return "\n".join(f"{i}. {n}: {v}" for i, (n, v) in enumerate(rows, 1))


# ---------------------------------------------------------------- captions
def cap_psych(item):
    by = f"\n— {item['author']}" if item.get("author") else ""
    return (f"\"{item['quote']}\"{by}\n\n{item['note']}\n\n"
            "💬 Which rule do you struggle with most? Tell us below.\n"
            "🔖 Save this for the next time the market tests your patience.\n\n"
            "Follow @hbecapital for daily trading psychology and mutual fund data.\n\n"
            "For educational purposes only. Not investment advice.\n\n" + TAGS["psych"])


def cap_leader(r):
    hz = mf.HORIZON_LABEL[r["horizon"]]
    kind = "CAGR"
    bname, bval = r["benchmark"]
    lines = [f"Top 10 {r['category']} Mutual Funds by {hz.title()} Returns | India {YEAR} 📊", "",
             numbered([(n, pct(v)) for n, v in r["top"]]), ""]
    if bval is not None:
        label = "Broad market, for comparison" if r.get("broad") else "Benchmark"
        lines += [f"{label} ({bname}): {pct(bval)}",
                  f"{r['beat']} of {r['count']} funds beat {'the Nifty 500' if r.get('broad') else 'the index'} over this period. Median fund: {pct(r['median'])}.", ""]
    lines += [f"Data: Regular plan, Growth option. NAV as of {mf.nice_date(r['asof'])}. "
              "Source: AMFI NAVs and NSE Indices, computed by HBE Capital FundNavigator.", "",
              "💬 Which of these do you hold? Comment below.", ENGAGE, LINK, "", MF_FOOT, "",
              f"{CAT_TAG.get(r['category'], '#equityfunds')} #mutualfunds #sip #investing #personalfinance"]
    return "\n".join(lines)


def cap_sip(r):
    inv = r["monthly"] * r["years"] * 12
    rows = [(n, f"≈ ₹{v / 1e5:.1f} lakh (XIRR {x:.1f}%)") for n, x, v in r["rows"]]
    return "\n".join([
        f"₹{r['monthly']:,} SIP for {r['years']} Years in {r['category']} Mutual Funds: What It Became 💰",
        f"Total invested: ₹{inv / 1e5:.1f} lakh", "",
        numbered(rows), "",
        f"Category median SIP XIRR: {pct(r['median'])}.",
        "End values are approximate, computed from each fund's SIP XIRR. Regular plan, Growth option. "
        f"NAV as of {mf.nice_date(r['asof'])}.", "",
        "The real lesson: staying invested through the ups and downs is what turned the SIP into wealth.", "",
        "💬 How long have you been running your SIP? Tell us below.", ENGAGE, LINK, "", MF_FOOT, "", TAGS["sip"]])


def cap_sif(r):
    return "\n".join([
        f"SIF Tracker: Specialised Investment Funds by {mf.HORIZON_LABEL[r['horizon']].title()} Returns | India {YEAR} 🧭",
        f"{r['count']} Specialised Investment Fund strategies are now live in India.", "",
        numbered([(n, pct(v)) for n, v in r["top"]]), "",
        "SIFs sit between mutual funds and PMS: long-short strategies, ₹10 lakh minimum, regulated by SEBI. "
        "Track records are still short, so judge them with care.",
        f"NAV as of {mf.nice_date(r['asof'])}. Regular plan, Growth option.", "",
        "Past performance may or may not be sustained in future. Not a recommendation. "
        f"Investments are subject to market risks, read all scheme related documents carefully.\n"
        f"HBE Capital · AMFI-registered Mutual Fund Distributor · {ARN}", "",
        ENGAGE, "", TAGS["sif"]])


def cap_momentum(r):
    hz = mf.HORIZON_LABEL[r["horizon"]]
    bname, bval = r["benchmark"]
    return "\n".join([
        f"Top Momentum Funds in India by {hz.title()} Returns | {YEAR} 🚀",
        f"Top 10 of {r['total']} momentum funds, index funds and ETFs in India.", "",
        numbered([(n, pct(v)) for n, v in r["top"]]), "",
        f"Broad market ({bname}): {pct(bval)}. {r['beat']} of {r['count']} momentum funds beat it over this period.", "",
        "What is momentum investing? It buys the stocks that have risen the most over the past 6 to 12 months, "
        "betting that strength tends to persist: buy high, sell higher. It can shine in trending markets and "
        "fall hard when trends reverse, so position size and patience matter.", "",
        f"Regular plan, Growth option. NAV as of {mf.nice_date(r['asof'])}.", "",
        "💬 Would you add momentum to your portfolio? Comment below.", ENGAGE, LINK, "", MF_FOOT, "",
        TAGS["momentum"]])


def cap_pms(r):
    hz = mf.HORIZON_LABEL[r["horizon"]]
    rows = [(f"{mf.short_name(n)} ({mf.short_name(p)})", pct(v)) for n, p, v in r["top"]]
    return "\n".join([
        f"Top 10 PMS Strategies in India by {hz.title()} Returns | {YEAR} 📈",
        f"Strategies with AUM ≥ ₹100 cr · month-end {mf.nice_date(r['asof'])} · {r['screened']} screened", "",
        numbered(rows), "",
        "Returns as reported by PMS providers to APMI (1Y+ annualised). Minimum investment ₹50 lakh.", "",
        "Past performance may or may not be sustained in future. PMS investments are subject to market risks. "
        "This is not a recommendation to invest in any strategy. Data not independently verified by HBE Capital.", "",
        "🔖 Save this · 📤 Share with someone exploring PMS", "", TAGS["pms"]])


# ---------------------------------------------------------------- planner
def leaderboard_with_fallback(start, horizon, out):
    for k in range(len(CATS)):
        cat = CATS[(start + k) % len(CATS)]
        try:
            return mf.leaderboard(cat, horizon, out)
        except ValueError as e:      # not enough funds with that much history
            print("skip:", e)
    raise RuntimeError(f"no category has 10 funds with {horizon} history")


def build(day: dt.date):
    d = day.toordinal()
    out = ROOT / "posts" / day.isoformat()
    out.mkdir(parents=True, exist_ok=True)
    plan = []

    def add(slot, image, caption, kind):
        plan.append({"slot": slot, "time_ist": SLOTS[slot], "kind": kind,
                     "image": str(Path(image).relative_to(ROOT)), "caption": caption})

    # 09:00 psychology
    quotes = json.loads((ROOT / "content" / "psychology.json").read_text())
    q = quotes[d % len(quotes)]
    add("psych", quote_card(q["quote"], "Market psychology", out / "1_psychology", author=q.get("author")),
        cap_psych(q), "psych")

    # 12:30 long-horizon leaderboard
    r = leaderboard_with_fallback(d % len(CATS), LONG_HORIZONS[(d // len(CATS)) % 3], out / "2_long")
    add("long", out / "2_long.jpg", cap_leader(r), "leaderboard")

    # 17:30 weekday feature
    feat, arg = FEATURE[day.weekday()]
    if feat == "sip":
        r = mf.sip_card(SIP_CATS[(d // 7) % len(SIP_CATS)], out / "3_feature", years=arg)
        add("feature", out / "3_feature.jpg", cap_sip(r), "sip")
    elif feat == "momentum":
        r = mf.momentum_tracker(out / "3_feature", horizon=arg)
        add("feature", out / "3_feature.jpg", cap_momentum(r), "momentum")
    elif feat == "sif":
        sifs = [f for f in mf.load("rankings.json")["funds"]
                if f["k"].startswith("SIF") and f["cagr"].get(arg) is not None]
        if len(sifs) >= MIN_SIFS:
            r = mf.sif_tracker(out / "3_feature", horizon=arg)
            add("feature", out / "3_feature.jpg", cap_sif(r), "sif")
        else:   # SIFs too new for a 1-year view: SIP card instead
            r = mf.sip_card(SIP_CATS[(d // 7 + 3) % len(SIP_CATS)], out / "3_feature", years=7)
            add("feature", out / "3_feature.jpg", cap_sip(r), "sip")
    else:
        r = mf.pms_leaderboard(arg, out / "3_feature")
        add("feature", out / "3_feature.jpg", cap_pms(r), "pms")

    # 20:00 short-horizon leaderboard (different category from 12:30)
    r = leaderboard_with_fallback((d + 4) % len(CATS), SHORT_HORIZONS[(d // len(CATS)) % 3], out / "4_short")
    add("short", out / "4_short.jpg", cap_leader(r), "leaderboard")

    for p in plan:
        assert len(p["caption"]) <= 2200, f"{p['slot']} caption too long for Instagram ({len(p['caption'])})"
    (out / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
    print(f"plan: {len(plan)} posts -> {out / 'plan.json'}")
    return plan


if __name__ == "__main__":
    ist_today = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)).date()
    build(dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else ist_today)
