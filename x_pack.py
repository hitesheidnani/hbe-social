"""Weekly X pack: next week's evergreen X posts (3 a day) for manual scheduling in X's free scheduler.

Built every Sunday into posts/x-week-<Monday>/ : images + README.md (renders on GitHub, phone-friendly).
Evergreen only (no daily prices), so the posts can be scheduled days ahead.
"""
import json, datetime as dt
from pathlib import Path

from brand import quote_card, tweet_card
import edu_posts as edu

ROOT = Path(__file__).parent
LIMIT = 270          # X allows 280 characters (emoji count double); keep a margin
TIMES = ["09:00", "13:00", "18:00"]


FOLLOW = "\n\n📲 Instagram & YouTube: hbecapital"


def fit(text, limit=LIMIT):
    """Trim to X's length, cutting at a sentence or word boundary; add the follow line when it fits."""
    if len(text) + len(FOLLOW) <= limit:
        return text + FOLLOW
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    for sep in ("\n\n", ". ", "\n", " "):
        if sep in cut[limit // 2:]:
            cut = cut[:cut.rindex(sep)].rstrip()
            break
    return cut + "…"


def _load(name):
    return json.loads((ROOT / "content" / name).read_text())


def build_week(monday, out_root=None):
    tweets, psych = _load("tweets.json"), _load("psychology.json")
    lessons, mlessons, usq = _load("education.json"), _load("momentum_lessons.json"), _load("us_quotes.json")
    out = Path(out_root or ROOT / "posts") / f"x-week-{monday.isoformat()}"
    out.mkdir(parents=True, exist_ok=True)
    posts = []
    for i in range(7):
        day = monday + dt.timedelta(days=i)
        d = day.toordinal()
        tag = f"{day:%a}"
        # 1. personal card
        t = tweets[(2 * d) % len(tweets)]
        img = tweet_card(t, out / f"{i + 1}{tag}_1_card")
        posts.append((day, TIMES[0], fit("\n\n".join(t) + "\n\n#investing"), [img]))
        # 2. psychology quote
        q = psych[d % len(psych)]
        img = quote_card(q["quote"], "Market psychology", out / f"{i + 1}{tag}_2_quote", author=q.get("author"))
        posts.append((day, TIMES[1], fit(f"\"{q['quote']}\"\n— {q['author']}\n\n{q['note']}\n\n#tradingpsychology"), [img]))
        # 3. rotating evergreen piece
        kind = i % 4
        if kind == 0:
            k = (d // 2) % len(lessons)
            slides = edu.edu_carousel(lessons[k], k + 1, out / f"{i + 1}{tag}_3_mfbasics")
            text = f"MF Basics: {lessons[k]['title']}\n\n{lessons[k]['hook']}\n\n💡 {lessons[k]['takeaway']}\n\n#mutualfunds"
            imgs = slides[:4]
        elif kind == 1:
            k = (d // 7) % len(mlessons)
            slides = edu.edu_carousel(mlessons[k], k + 1, out / f"{i + 1}{tag}_3_momentum", series="MOMENTUM & FACTORS",
                                      foot="generic")
            text = f"{mlessons[k]['title']}\n\n{mlessons[k]['hook']}\n\n💡 {mlessons[k]['takeaway']}\n\n#momentuminvesting"
            imgs = slides[:4]
        elif kind == 2:
            q = usq[d % len(usq)]
            imgs = [quote_card(q["quote"], "Investing wisdom", out / f"{i + 1}{tag}_3_wisdom", author=q["author"])]
            text = f"\"{q['quote']}\"\n— {q['author']}\n\n{q['note']}"
        else:
            m, y = [(10000, 15), (5000, 20), (25000, 10), (10000, 25)][(d // 7) % 4]
            r = edu.compounding_sip(m, y, 0.12, out / f"{i + 1}{tag}_3_compounding")
            imgs = [out / f"{i + 1}{tag}_3_compounding.jpg"]
            text = (f"₹{m:,}/month SIP for {y} years at an assumed 12% ≈ {edu.inr(r['value'])} from "
                    f"{edu.inr(r['invested'])} invested.\n\nHalf the final value comes in the last {r['last_years']} years. "
                    "That's compounding.\n\n(Illustration, not a projection.) #compounding")
        posts.append((day, TIMES[2], fit(text), imgs))

    lines = [f"# X posts for the week of {monday:%d %b %Y}", "",
             "Schedule each one on x.com: **Post** → write/paste the text → attach the image(s) → "
             "**calendar icon** (Schedule) → pick the date & time → **Confirm** → **Schedule**.", "",
             "All posts are educational only. Images already carry the disclaimer.", ""]
    for day, time, text, imgs in posts:
        lines += [f"## {day:%a %d %b} · {time} IST", "", "```", text, "```", ""]
        lines += [f"![image]({Path(p).name})" for p in imgs] + ["", "---", ""]
    (out / "README.md").write_text("\n".join(lines))
    print(f"x pack: {len(posts)} posts -> {out}")
    return out


if __name__ == "__main__":
    import sys
    today = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    build_week(today + dt.timedelta(days=(7 - today.weekday()) % 7 or 7))
