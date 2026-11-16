"""Share a chart from a named source right now (image shown whole and unedited, with credit).

Usage: python share_chart.py <image> "Title" "Source name" "One or two lines of context" ["hashtags"]
Adds a slot to today's plan; the ticker publishes it within ~10 minutes.
"""
import json, sys, shutil, datetime as dt
from pathlib import Path
import edu_posts as edu
from brand import story_version, EDU

ROOT = Path(__file__).parent
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
image, title, source, note = sys.argv[1], sys.argv[2].strip(), sys.argv[3].strip(), sys.argv[4].strip()
tags = sys.argv[5] if len(sys.argv) > 5 else "#stockmarketindia #investing #markets #equity #emergingmarkets"
now = dt.datetime.now(IST)
folder = ROOT / "posts" / now.date().isoformat()
plan = json.loads((folder / "plan.json").read_text())
slot = f"chart_{now:%H%M}"
src = folder / f"9_{slot}_src{Path(image).suffix.lower()}"
shutil.copy(image, src)
img = edu.partner_chart_card(src, title, None, folder / f"9_{slot}", kicker="CHART WORTH SEEING",
                             credit=f"Source: {source}", note=None)
caption = "\n".join([f"{title} 📊", "", note, "", f"Source and credit: {source}.", "",
                     "💬 What's your take? Comment below.", "📤 Share this with someone tracking the markets.", "",
                     f"⚠️ {EDU} Shared for information; views are the source's own.\nHBE Capital", "", tags])
plan.append({"slot": slot, "time_ist": now.strftime("%H:%M"), "kind": "partner", "image": str(Path(img).relative_to(ROOT)),
             "story_image": str(story_version(img).relative_to(ROOT)), "caption": caption})
plan.sort(key=lambda p: p["time_ist"])
(folder / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
print("queued", slot)
