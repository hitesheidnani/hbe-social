"""Official-source headline cards. Checks RBI, SEBI, the US Federal Reserve and the US BEA feeds, and queues a
card for each NEW announcement that matches the keyword filters (routine notices are ignored).

Run by the ticker every ~10 minutes. The card shows the official headline and names the source; the caption links
to the full release. No summaries or opinions are added.
  python news_feeds.py            queue new matching items into today's plan
  python news_feeds.py --seed     mark everything currently in the feeds as seen (no posts)
  python news_feeds.py --dry      show what the filters match in the current feeds
"""
import html, json, re, sys, hashlib, datetime as dt, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
SEEN = ROOT / "posts" / "news_seen.json"
MAX_PER_DAY, HOURS = 4, (7, 22)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
      "Accept": "application/rss+xml,application/xml,text/xml,*/*"}

FEEDS = [
    {"key": "rbi", "kicker": "RBI ANNOUNCEMENT", "source": "Reserve Bank of India", "flag": "🇮🇳",
     "url": "https://www.rbi.org.in/pressreleases_rss.xml",
     "include": r"monetary policy|repo rate|governor.s statement|minutes of the monetary policy committee|"
                r"financial stability report|sovereign gold bond|cash reserve ratio|developmental and regulatory|"
                r"annual report|foreign exchange reserves",
     "exclude": r"auction|money market operations|co-operative|cancels|penalty|variable rate",
     "tags": "#rbi #monetarypolicy #reporate #indianeconomy #investing"},
    {"key": "sebi", "kicker": "SEBI ANNOUNCEMENT", "source": "Securities and Exchange Board of India", "flag": "🇮🇳",
     "url": "https://www.sebi.gov.in/sebirss.xml",
     "include": r"mutual fund|specialized investment fund|portfolio manager|investment advis|research analyst|"
                r"board meeting|derivative|ipo\b|kyc|nomination|finfluencer|investor",
     "exclude": r"attachment|prohibitory|recovery|adjudicat|in the matter of|rc no|interim order|settlement order|"
                r"exemption order|show cause|release order|certificate",
     "tags": "#sebi #mutualfunds #stockmarketindia #investors #regulation"},
    {"key": "fed", "kicker": "US FEDERAL RESERVE", "source": "US Federal Reserve", "flag": "🇺🇸",
     "url": "https://www.federalreserve.gov/feeds/press_monetary.xml",
     "include": r"fomc statement|minutes of the federal open market committee|economic projections",
     "exclude": r"discount rate",
     "tags": "#federalreserve #fomc #interestrates #usmarkets #investing"},
    {"key": "bea", "kicker": "US ECONOMIC DATA", "source": "US Bureau of Economic Analysis", "flag": "🇺🇸",
     "url": "https://apps.bea.gov/rss/rss.xml",
     "include": r"^gdp|gross domestic product|personal income and outlays|international trade in goods and services",
     "exclude": r"by state|by county|by industry|metropolitan",
     "tags": "#usgdp #useconomy #inflation #usmarkets #investing"},
]


def fetch(feed):
    x = urllib.request.urlopen(urllib.request.Request(feed["url"], headers=UA), timeout=40).read().decode("utf-8", "ignore")
    out = []
    for it in re.findall(r"<item[^>]*>(.*?)</item>", x, re.S):
        t, l = re.search(r"<title>(.*?)</title>", it, re.S), re.search(r"<link>(.*?)</link>", it, re.S)
        if not t or not l:
            continue
        clean = lambda v: re.sub(r"\s+", " ", html.unescape(re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", "", v))).strip()
        out.append((clean(t.group(1)), clean(l.group(1))))
    return out


def matches(feed, title):
    return re.search(feed["include"], title, re.I) and not re.search(feed["exclude"], title, re.I)


def load_seen():
    return set(json.loads(SEEN.read_text())) if SEEN.exists() else set()


def main(mode=""):
    seen = load_seen()
    now = dt.datetime.now(IST)
    folder = ROOT / "posts" / now.date().isoformat()
    plan_file = folder / "plan.json"
    can_post = mode == "" and plan_file.exists() and HOURS[0] <= now.hour < HOURS[1]
    plan = json.loads(plan_file.read_text()) if plan_file.exists() else []
    posted_today = sum(1 for p in plan if p["slot"].startswith("news_"))
    changed = False
    for feed in FEEDS:
        try:
            items = fetch(feed)
        except Exception as e:
            print(f"news: {feed['key']} unavailable ({e})")
            continue
        for title, link in items:
            if link in seen:
                continue
            hit = matches(feed, title)
            if mode == "--dry":
                if hit:
                    print(f"MATCH {feed['key']}: {title[:110]}")
                continue
            if mode == "--seed" or not hit:
                seen.add(link)                      # routine notices are remembered and never posted
                continue
            if not can_post or posted_today >= MAX_PER_DAY:
                continue                            # leave unseen: it will be picked up when posting is possible
            import edu_posts as edu
            from brand import story_version, EDU
            slot = "news_" + hashlib.md5(link.encode()).hexdigest()[:6]
            head = title if len(title) <= 150 else title[:147].rsplit(" ", 1)[0] + "…"
            img = edu.news_card(head, [f"Official release: {feed['source']}", "Full text: link in the caption"],
                                folder / f"9_{slot}", kicker=feed["kicker"])
            caption = "\n".join([f"{feed['flag']} {title}", "", f"Source: {feed['source']} (official release).",
                                 f"Read the full text: {link}", "",
                                 "We share official announcements as published, without commentary.", "",
                                 f"⚠️ {EDU}\nHBE Capital", "", feed["tags"]])
            plan.append({"slot": slot, "time_ist": now.strftime("%H:%M"), "kind": "news",
                         "image": str(img.relative_to(ROOT)),
                         "story_image": str(story_version(img).relative_to(ROOT)), "caption": caption})
            seen.add(link)
            posted_today += 1
            changed = True
            print("news: queued", feed["key"], "-", title[:90])
    if mode != "--dry":
        SEEN.write_text(json.dumps(sorted(seen), indent=0))
        if changed:
            plan.sort(key=lambda p: p["time_ist"])
            plan_file.write_text(json.dumps(plan, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
