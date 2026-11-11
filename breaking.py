"""Same-day news post. Adds a slot to today's plan; the ticker publishes it within ~10 minutes.

Usage: python breaking.py "Headline" "Point one | Point two | Point three" ["What it means for investors"]
"""
import json, sys, datetime as dt
from pathlib import Path
import edu_posts as edu
from brand import story_version, EDU

ROOT = Path(__file__).parent
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
headline, points = sys.argv[1].strip(), [p.strip() for p in sys.argv[2].split("|") if p.strip()]
meaning = sys.argv[3].strip() if len(sys.argv) > 3 else ""
now = dt.datetime.now(IST)
folder = ROOT / "posts" / now.date().isoformat()
plan = json.loads((folder / "plan.json").read_text())
slot = f"news_{now:%H%M}"
img = edu.news_card(headline, points, folder / f"9_{slot}")
caption = "\n".join([f"{headline} 📰", ""] + [f"→ {p}" for p in points]
                    + (["", f"What it means for investors: {meaning}"] if meaning else [])
                    + ["", "💬 What's your take? Comment below.", "📤 Share this with someone tracking the markets.", "",
                       f"⚠️ {EDU} This is a factual summary, not a recommendation.\nHBE Capital", "",
                       "#marketnews #stockmarketindia #investing #nifty #personalfinance"])
plan.append({"slot": slot, "time_ist": now.strftime("%H:%M"), "kind": "news", "image": str(img.relative_to(ROOT)),
             "story_image": str(story_version(img, label="NEWS").relative_to(ROOT)), "caption": caption})
plan.sort(key=lambda p: p["time_ist"])
(folder / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
print("queued", slot)
