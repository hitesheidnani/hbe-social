"""Build one day's posts: images + captions + schedule -> posts/YYYY-MM-DD/plan.json

Usage:  python daily.py [YYYY-MM-DD]
Daily mix (IST):
  08:00  Market update: key Indian & US indices, gold, oil, US 10Y, USD/INR with 200-DMA trend
  09:00  market psychology quote
  11:00  Market Monitor: Nifty index heatmap (1y/3y/5y) or drawdown-from-high table, by weekday
  12:30  top-10 leaderboard, long horizon (5y / 7y / 10y), rotating category
  15:00  MF Basics carousel (even days) or power-of-compounding illustration (odd days)
  17:30  weekday feature: SIP card (Mon, Fri), SIF (Tue), momentum funds (Wed, Sun), PMS (Thu, Sat)
  20:00  top-10 leaderboard, shorter horizon (1y / 2y / 3y), rotating category
Returns for periods under 1 year are never shown.
"""
import json, sys, datetime as dt
from pathlib import Path

import mf_posts as mf
import edu_posts as edu
import market_posts as mkt
import update_post as upd
from brand import quote_card, story_version, ARN, MF_DISCLAIMER, EDU

ROOT = Path(__file__).parent
SLOTS = {"update": "08:00", "psych": "09:00", "market": "11:00", "long": "12:30", "edu": "15:00", "feature": "17:30", "short": "20:00"}

# 11:00 Market Monitor (Nifty indices, price returns), by weekday: heatmaps rotate 1y/3y/5y week to week
MARKET = {0: ("heat", "Broad Market"), 1: ("heat", "Sectoral"), 2: ("dd", "Broad Market"), 3: ("heat", "Strategy"),
          4: ("heat", "Thematic"), 5: ("dd", "Sectoral"), 6: ("dd", "Thematic|Strategy")}
MAX_INDEX_AGE_DAYS = 5   # skip the market post if NSE data could not be refreshed for this long

# 15:00 alternates: MF Basics carousel (even days) / power-of-compounding card (odd days)
COMPOUNDING = [  # (type, amount, years, rate)
    ("sip", 10000, 10, 0.15), ("early", 10000, None, 0.12), ("sip", 5000, 20, 0.12), ("stepup", 10000, 20, 0.12),
    ("lump", 100000, None, 0.12), ("sip", 25000, 15, 0.15), ("sip", 10000, 30, 0.12), ("early", 5000, None, 0.15),
    ("stepup", 5000, 25, 0.15), ("sip", 50000, 10, 0.12), ("lump", 500000, None, 0.15), ("sip", 10000, 20, 0.15),
    ("sip", 2000, 25, 0.12), ("stepup", 25000, 15, 0.12), ("sip", 15000, 15, 0.12), ("early", 20000, None, 0.12),
]

CATS = [  # rotation order for leaderboards
    "Equity Scheme - Small Cap Fund", "Equity Scheme - Flexi Cap Fund", "Equity Scheme - Mid Cap Fund",
    "Equity Scheme - Large Cap Fund", "Equity Scheme - ELSS", "Equity Scheme - Large & Mid Cap Fund",
    "Equity Scheme - Multi Cap Fund", "Equity Scheme - Value Fund", "Equity Scheme - Focused Fund",
]
SIP_CATS = ["Equity Scheme - Small Cap Fund", "Equity Scheme - Mid Cap Fund", "Equity Scheme - Flexi Cap Fund",
            "Equity Scheme - Large Cap Fund", "Equity Scheme - ELSS", "Equity Scheme - Large & Mid Cap Fund"]
# weekday (Mon=0) -> feature for the 17:30 slot
# Rule: never show returns for periods under 1 year (exception: SIFs, a new category, may use 3m/6m).
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
MF_FOOT = (f"⚠️ {EDU} Past performance may or may not be sustained in future. This is not a recommendation "
           f"to buy or sell any fund. {MF_DISCLAIMER}\nHBE Capital · AMFI-registered Mutual Fund Distributor · {ARN}")
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
            f"⚠️ {EDU}\n\n" + TAGS["psych"])


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
        f"NAV as of {mf.nice_date(r['asof'])}. Regular plan, Growth option."
        + (" Returns under 1 year are absolute, not annualised." if r["horizon"] in ("3m", "6m") else ""), "",
        f"⚠️ {EDU} Past performance may or may not be sustained in future. Not a recommendation. "
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


def cap_edu(t, n):
    points = "\n".join(f"→ {h}" for h, _ in t["slides"])
    return "\n".join([
        f"MF Basics #{n}: {t['title']} 📚", "", t["hook"], "", points, "",
        f"💡 {t['takeaway']}", "",
        "👉 Swipe through, then save this for later 🔖",
        "📤 Share it with someone starting their investing journey",
        "Follow @hbecapital for a new mutual fund lesson every other day.", "",
        f"⚠️ {EDU} {MF_DISCLAIMER}\nHBE Capital · AMFI-registered Mutual Fund Distributor · {ARN}", "",
        t["tags"]])


def cap_comp(r):
    rate = f"{r['rate'] * 100:.0f}%"
    ill = (f"Illustration at an assumed constant {rate} annual return. Real returns vary, can be negative, "
           "and are not guaranteed. Not a projection for any fund.")
    if r["type"] == "sip":
        head = (f"₹{r['monthly']:,} SIP for {r['years']} Years at {rate} = {edu.inr(r['value'])} 🤯 | "
                "Power of Compounding")
        body = [f"Invested: {edu.inr(r['invested'])}", f"Value: {edu.inr(r['value'])}",
                f"Growth: {edu.inr(r['value'] - r['invested'])} ({r['value'] / r['invested']:.1f}x)", "",
                f"Half of the final value is created in just the last {r['last_years']} years. "
                "That's compounding: slow at first, then powerful. The hardest part is staying invested long enough."]
    elif r["type"] == "early":
        (a1, v1, i1), (a2, v2, i2) = r["values"]
        head = f"Start at {a1} vs {a2}: {edu.inr(v1)} vs {edu.inr(v2)} ⏳ | Power of Compounding"
        body = [f"Same ₹{r['monthly']:,}/month SIP until age {r['until']}.",
                f"Starting at {a1}: {edu.inr(i1)} invested → {edu.inr(v1)}",
                f"Starting at {a2}: {edu.inr(i2)} invested → {edu.inr(v2)}", "",
                f"Just {edu.inr(i1 - i2)} more invested, but {v1 / v2:.1f}x the wealth. "
                "The best time to start was yesterday. The next best is today."]
    elif r["type"] == "stepup":
        head = f"Step-Up SIP: {edu.inr(r['up'])} vs {edu.inr(r['flat'])} 📈 | Power of Compounding"
        body = [f"Start with ₹{r['monthly']:,}/month for {r['years']} years.",
                f"Flat SIP: {edu.inr(r['flat_inv'])} invested → {edu.inr(r['flat'])}",
                f"Increase it {r['step'] * 100:.0f}% every year: {edu.inr(r['up_inv'])} invested → {edu.inr(r['up'])}", "",
                "Raise your SIP when your salary rises. It rarely feels like a sacrifice, and it can transform the result."]
    else:
        head = f"{edu.inr(r['amount'])} Invested Once at {rate} for 30 Years 💰 | Power of Compounding"
        body = [f"After {y} years: {edu.inr(v)}" for y, v in r["values"]] + [
                "", f"Rule of 72: at {rate}, money roughly doubles every {r['double']:.0f} years (72 ÷ {r['rate'] * 100:.0f}). "
                "Time is the most powerful ingredient."]
    return "\n".join([head, ""] + body + [
        "", "💬 What would you do with this corpus? Comment below.",
        "🔖 Save this · 📤 Share with a friend who keeps postponing their SIP",
        "Follow @hbecapital for daily mutual fund insights.", "",
        f"⚠️ {EDU} {ill} {MF_DISCLAIMER}\nHBE Capital · AMFI-registered Mutual Fund Distributor · {ARN}", "",
        "#compounding #sip #wealthcreation #mutualfunds #financialfreedom"])


MKT_FOOT = (f"⚠️ {EDU} Index figures are price returns (dividends excluded); indices cannot be invested in "
            "directly. Past performance may or may not be sustained in future. Not a recommendation.\n"
            f"HBE Capital · AMFI-registered Mutual Fund Distributor · {ARN}")
MKT_TAGS = {"Broad Market": "#nifty50 #stockmarketindia #midcap #smallcap #investing",
            "Sectoral": "#sectorrotation #niftysectors #stockmarketindia #nifty #investing",
            "Strategy": "#factorinvesting #momentuminvesting #smartbeta #stockmarketindia #investing",
            "Thematic": "#thematicinvesting #stockmarketindia #nifty #defence #investing"}


def cap_heat(r):
    hz = {"1y": "1-Year", "3y": "3-Year", "5y": "5-Year"}[r["horizon"]]
    per = "" if r["horizon"] == "1y" else " a year (CAGR)"
    return "\n".join([
        f"Nifty {r['category']} Indices: {hz} Returns Heatmap | {r['asof']:%b %Y} 🟩🟥", "",
        f"{r['up']} of {r['count']} {r['category'].lower()} indices are up over {hz.lower()}{per}.", "",
        "🏆 Leaders: " + ", ".join(f"{n} {v:+.1f}%" for n, v in r["best"]),
        "🔻 Laggards: " + ", ".join(f"{n} {v:+.1f}%" for n, v in r["worst"]), "",
        "Leadership rotates. Last period's winners are rarely next period's, which is why diversification "
        "and a disciplined process matter more than chasing the hottest theme.", "",
        f"Data as of {r['asof']:%d %b %Y}. Source: NSE Indices.", "",
        "💬 Which of these surprised you? Comment below.", "🔖 Save this · 📤 Share with a fellow investor", "",
        MKT_FOOT, "", MKT_TAGS[r["category"]]])


def cap_dd(r):
    return "\n".join([
        f"How Far Are Nifty {r['category']} Indices From Their All-Time Highs? | {r['asof']:%b %Y} 📉", "",
        f"{r['near']} of {r['count']} are within 5% of their all-time high; {r['deep']} are down 20% or more.", "",
        "Closest to the top: " + ", ".join(f"{n} ({'at high' if v > -0.5 else f'{v:.1f}%'})" for n, v, _ in r["closest"]),
        "Furthest below: " + ", ".join(f"{n} ({v:.1f}%, {days:,} days since the high)" for n, v, _, days in r["deepest"]), "",
        "Drawdowns are part of investing. Knowing how deep and how long they've been helps you keep perspective, "
        "and avoid panic.", "",
        f"Data as of {r['asof']:%d %b %Y}. ATH = all-time high on daily closes. Source: NSE Indices.", "",
        "🔖 Save this · 📤 Share with someone who checks the market too often", "",
        MKT_FOOT, "", MKT_TAGS[r["category"]]])


def cap_pms(r):
    hz = mf.HORIZON_LABEL[r["horizon"]]
    rows = [(f"{mf.short_name(n)} ({mf.short_name(p)})", pct(v)) for n, p, v in r["top"]]
    return "\n".join([
        f"Top 10 PMS Strategies in India by {hz.title()} Returns | {YEAR} 📈",
        f"Strategies with AUM ≥ ₹100 cr · month-end {mf.nice_date(r['asof'])} · {r['screened']} screened", "",
        numbered(rows), "",
        "Returns as reported by PMS providers to APMI (1Y+ annualised). Minimum investment ₹50 lakh.", "",
        f"⚠️ {EDU} Past performance may or may not be sustained in future. PMS investments are subject to market risks. "
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

    def add(slot, image, caption, kind, rows=None, carousel=None):
        story = story_version(image, label={"psych": "DAILY MINDSET", "edu": "NEW LESSON",
                                            "update": "MORNING UPDATE"}.get(kind, "NEW POST"))
        item = {"slot": slot, "time_ist": SLOTS[slot], "kind": kind,
                "image": str(Path(image).relative_to(ROOT)),
                "story_image": str(story.relative_to(ROOT)), "caption": caption}
        if carousel:
            item["carousel"] = [str(Path(c).relative_to(ROOT)) for c in carousel]
        if rows:   # ranked cards also go out as a countdown Reel (built at publish time)
            item["reel"] = {"rows": rows}
        plan.append(item)

    # 08:00 market update (skipped if too much data is missing)
    try:
        r = upd.market_update(out / "00_update")
        add("update", out / "00_update.jpg", upd.caption(r, EDU), "update")
    except Exception as e:
        print("update: skipped,", e)

    # 09:00 psychology
    quotes = json.loads((ROOT / "content" / "psychology.json").read_text())
    q = quotes[d % len(quotes)]
    add("psych", quote_card(q["quote"], "Market psychology", out / "1_psychology", author=q.get("author")),
        cap_psych(q), "psych")

    # 12:30 long-horizon leaderboard
    r = leaderboard_with_fallback(d % len(CATS), LONG_HORIZONS[(d // len(CATS)) % 3], out / "2_long")
    add("long", out / "2_long.jpg", cap_leader(r), "leaderboard", rows=len(r["top"]))

    # 11:00 Market Monitor (skipped if index data is stale)
    try:
        ms = mkt.all_metrics()
        age = (day - max(m["asof"] for m in ms)).days
        if age > MAX_INDEX_AGE_DAYS:
            print(f"market: index data is {age} days old; skipping the market post")
        else:
            kind, cat = MARKET[day.weekday()]
            if "|" in cat:
                cat = cat.split("|")[(d // 7) % 2]
            f = out / "0_market"
            if kind == "heat":
                r = mkt.heatmap(cat, ["1y", "3y", "5y"][(d // 7) % 3], f, ms)
                add("market", f.with_suffix(".jpg"), cap_heat(r), "heatmap")
            else:
                r = mkt.drawdown_table(cat, f, ms)
                add("market", f.with_suffix(".jpg"), cap_dd(r), "drawdown")
    except Exception as e:      # a market-data problem must never block the fund posts
        print("market: skipped,", e)

    # 15:00 education: MF Basics carousel / compounding illustration, alternating days
    if d % 2 == 0:
        topics = json.loads((ROOT / "content" / "education.json").read_text())
        k = (d // 2) % len(topics)
        slides = edu.edu_carousel(topics[k], k + 1, out / "edu")
        add("edu", slides[0], cap_edu(topics[k], k + 1), "edu", carousel=slides)
    else:
        typ, amt, yrs, rate = COMPOUNDING[(d // 2) % len(COMPOUNDING)]
        f = out / "5_compounding"
        r = {"sip": lambda: edu.compounding_sip(amt, yrs, rate, f),
             "early": lambda: edu.compounding_early(amt, rate, f),
             "stepup": lambda: edu.compounding_stepup(amt, yrs, rate, f),
             "lump": lambda: edu.compounding_lumpsum(amt, rate, f)}[typ]()
        add("edu", f.with_suffix(".jpg"), cap_comp(r), "compounding")

    # 17:30 weekday feature
    feat, arg = FEATURE[day.weekday()]
    if feat == "sip":
        r = mf.sip_card(SIP_CATS[(d // 7) % len(SIP_CATS)], out / "3_feature", years=arg)
        add("feature", out / "3_feature.jpg", cap_sip(r), "sip", rows=len(r["rows"]))
    elif feat == "momentum":
        r = mf.momentum_tracker(out / "3_feature", horizon=arg)
        add("feature", out / "3_feature.jpg", cap_momentum(r), "momentum", rows=len(r["top"]))
    elif feat == "sif":
        # SIFs are new (2025), the one exception to the 1-year rule: longest period with enough history
        funds = [f for f in mf.load("rankings.json")["funds"] if f["k"].startswith("SIF")]
        hz = next((h for h in ("1y", "6m", "3m")
                   if sum(f["cagr"].get(h) is not None for f in funds) >= MIN_SIFS), None)
        if hz:
            r = mf.sif_tracker(out / "3_feature", horizon=hz)
            add("feature", out / "3_feature.jpg", cap_sif(r), "sif", rows=len(r["top"]))
        else:
            r = mf.sip_card(SIP_CATS[(d // 7 + 3) % len(SIP_CATS)], out / "3_feature", years=7)
            add("feature", out / "3_feature.jpg", cap_sip(r), "sip", rows=len(r["rows"]))
    else:
        r = mf.pms_leaderboard(arg, out / "3_feature")
        add("feature", out / "3_feature.jpg", cap_pms(r), "pms", rows=len(r["top"]))

    # 20:00 short-horizon leaderboard (different category from 12:30)
    r = leaderboard_with_fallback((d + 4) % len(CATS), SHORT_HORIZONS[(d // len(CATS)) % 3], out / "4_short")
    add("short", out / "4_short.jpg", cap_leader(r), "leaderboard", rows=len(r["top"]))

    plan.sort(key=lambda p: p["time_ist"])
    for p in plan:
        assert len(p["caption"]) <= 2200, f"{p['slot']} caption too long for Instagram ({len(p['caption'])})"
    (out / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
    print(f"plan: {len(plan)} posts -> {out / 'plan.json'}")
    return plan


if __name__ == "__main__":
    ist_today = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)).date()
    build(dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else ist_today)
