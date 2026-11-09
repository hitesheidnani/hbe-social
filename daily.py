"""Build one day's posts: images + captions + schedule -> posts/YYYY-MM-DD/plan.json

Usage:  python daily.py [YYYY-MM-DD]
Daily mix (IST):
  09:00  market psychology quote
  12:30  top-10 leaderboard, long horizon (3y / 5y / 10y), rotating category
  17:30  weekday feature: SIP card (Mon, Fri), SIF (Tue), momentum funds (Wed, Sun), PMS (Thu, Sat)
  20:00  top-10 leaderboard, short horizon (3m / 6m / 1y), rotating category
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
FEATURE = {0: ("sip", 5), 1: ("sif", "3m"), 2: ("momentum", "1y"), 3: ("pms", "1y"),
           4: ("sip", 10), 5: ("pms", "3y"), 6: ("momentum", "6m")}

HASH_BASE = "#mutualfunds #investing #sip #personalfinance #wealthcreation #HBECapital"
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
            "Save this for the next time the market tests your patience. 🔖\n\n"
            "For educational purposes only. Not investment advice.\n\n"
            "#tradingpsychology #markdouglas #tradinginthezone #investingpsychology #riskmanagement #stockmarketindia #HBECapital")


def cap_leader(r):
    hz = mf.HORIZON_LABEL[r["horizon"]]
    kind = "CAGR" if r["horizon"] not in ("3m", "6m") else "absolute returns"
    bname, bval = r["benchmark"]
    lines = [f"Top 10 {r['category']} funds by {hz} returns ({kind}) 📊", "",
             numbered([(n, pct(v)) for n, v in r["top"]]), ""]
    if bval is not None:
        lines += [f"Benchmark ({bname}): {pct(bval)}",
                  f"{r['beat']} of {r['count']} funds beat the index over this period. Median fund: {pct(r['median'])}.", ""]
    lines += [f"Data: Regular plan, Growth option. NAV as of {mf.nice_date(r['asof'])}. "
              "Source: AMFI NAVs and NSE Indices, computed by HBE Capital FundNavigator.", "",
              LINK, "", MF_FOOT, "",
              f"#{r['category'].lower().replace(' ', '').replace('&', '').replace('(taxsaver)', '')}funds {HASH_BASE}"]
    return "\n".join(lines)


def cap_sip(r):
    inv = r["monthly"] * r["years"] * 12
    rows = [(n, f"≈ ₹{v / 1e5:.1f} lakh (XIRR {x:.1f}%)") for n, x, v in r["rows"]]
    return "\n".join([
        f"What did ₹{r['monthly']:,}/month for {r['years']} years become in {r['category']} funds? 💰",
        f"Total invested: ₹{inv / 1e5:.1f} lakh", "",
        numbered(rows), "",
        f"Category median SIP XIRR: {pct(r['median'])}.",
        "End values are approximate, computed from each fund's SIP XIRR. Regular plan, Growth option. "
        f"NAV as of {mf.nice_date(r['asof'])}.", "",
        "The real lesson: staying invested through the ups and downs is what turned the SIP into wealth.", "",
        LINK, "", MF_FOOT, "", f"#sipinvestment #{r['category'].lower().replace(' ', '')}funds {HASH_BASE}"])


def cap_sif(r):
    return "\n".join([
        f"SIF tracker: {mf.HORIZON_LABEL[r['horizon']]} returns 🧭",
        f"{r['count']} Specialised Investment Fund strategies are now live in India.", "",
        numbered([(n, pct(v)) for n, v in r["top"]]), "",
        "SIFs sit between mutual funds and PMS: long-short strategies, ₹10 lakh minimum, regulated by SEBI. "
        "Track records are still short, so judge them with care.",
        f"NAV as of {mf.nice_date(r['asof'])}. Regular plan, Growth option.", "",
        "Past performance may or may not be sustained in future. Not a recommendation. "
        f"Investments are subject to market risks, read all scheme related documents carefully.\n"
        f"HBE Capital · AMFI-registered Mutual Fund Distributor · {ARN}", "",
        "#SIF #specialisedinvestmentfund #longshort #investing #HBECapital"])


def cap_momentum(r):
    hz = mf.HORIZON_LABEL[r["horizon"]]
    bname, bval = r["benchmark"]
    return "\n".join([
        f"Momentum funds: {hz} returns 🚀",
        f"Top 10 of {r['total']} momentum funds, index funds and ETFs in India.", "",
        numbered([(n, pct(v)) for n, v in r["top"]]), "",
        f"Broad market ({bname}): {pct(bval)}. {r['beat']} of {r['count']} momentum funds beat it over this period.", "",
        "What is momentum investing? It buys the stocks that have risen the most over the past 6 to 12 months, "
        "betting that strength tends to persist: buy high, sell higher. It can shine in trending markets and "
        "fall hard when trends reverse, so position size and patience matter.", "",
        f"Regular plan, Growth option. NAV as of {mf.nice_date(r['asof'])}. Returns under 1 year are absolute.", "",
        LINK, "", MF_FOOT, "",
        "#momentuminvesting #momentum #factorinvesting #indexfunds " + HASH_BASE])


def cap_pms(r):
    hz = mf.HORIZON_LABEL[r["horizon"]]
    rows = [(f"{mf.short_name(n)} ({mf.short_name(p)})", pct(v)) for n, p, v in r["top"]]
    return "\n".join([
        f"Top 10 equity PMS strategies by {hz} returns 📈",
        f"Strategies with AUM ≥ ₹100 cr · month-end {mf.nice_date(r['asof'])} · {r['screened']} screened", "",
        numbered(rows), "",
        "Returns as reported by PMS providers to APMI (1Y+ annualised). Minimum investment ₹50 lakh.", "",
        "Past performance may or may not be sustained in future. PMS investments are subject to market risks. "
        "This is not a recommendation to invest in any strategy. Data not independently verified by HBE Capital.", "",
        "#PMS #portfoliomanagement #HNI #wealthmanagement #investing #HBECapital"])


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
    r = leaderboard_with_fallback(d % len(CATS), ["5y", "3y", "10y"][(d // len(CATS)) % 3], out / "2_long")
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
        r = mf.sif_tracker(out / "3_feature", horizon=arg)
        add("feature", out / "3_feature.jpg", cap_sif(r), "sif")
    else:
        r = mf.pms_leaderboard(arg, out / "3_feature")
        add("feature", out / "3_feature.jpg", cap_pms(r), "pms")

    # 20:00 short-horizon leaderboard (different category from 12:30)
    r = leaderboard_with_fallback((d + 4) % len(CATS), ["1y", "6m", "3m"][(d // len(CATS)) % 3], out / "4_short")
    add("short", out / "4_short.jpg", cap_leader(r), "leaderboard")

    for p in plan:
        assert len(p["caption"]) <= 2200, f"{p['slot']} caption too long for Instagram ({len(p['caption'])})"
    (out / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
    print(f"plan: {len(plan)} posts -> {out / 'plan.json'}")
    return plan


if __name__ == "__main__":
    ist_today = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)).date()
    build(dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else ist_today)
