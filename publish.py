"""Publish due posts from today's plan to Instagram.

Runs on a schedule. Each run publishes at most ONE post: the earliest slot whose time (IST)
has passed and that has not been published yet. Results are recorded in posts/<date>/status.json.

Usage:
  python publish.py                      # normal scheduled run
  python publish.py --slot psych         # publish a specific slot now (manual/test)
  python publish.py --dry-run            # show what would be posted
Env: IG_USER_ID, META_PAGE_TOKEN, GITHUB_REPOSITORY (owner/name), optional POST_DATE (YYYY-MM-DD)
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error, datetime as dt
from pathlib import Path

ROOT = Path(__file__).parent
GRAPH = "https://graph.facebook.com"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
MAX_LATE_HOURS = 3


def graph(method, path, **params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    if method == "GET":
        url, data = f"{url}?{data.decode()}", None
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=60))
    except urllib.error.HTTPError as e:
        err = json.load(e).get("error", {})
        raise RuntimeError(f"Instagram API: {err.get('message')} (code {err.get('code')}, "
                           f"subcode {err.get('error_subcode')})") from None


def post_instagram(image_url, caption):
    ig, token = os.environ["IG_USER_ID"], os.environ["META_PAGE_TOKEN"]
    container = graph("POST", f"{ig}/media", image_url=image_url, caption=caption, access_token=token)["id"]
    for _ in range(30):                      # wait until Instagram has fetched and processed the image
        status = graph("GET", container, fields="status_code", access_token=token).get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram could not process the image (status {status})")
        time.sleep(5)
    media = graph("POST", f"{ig}/media_publish", creation_id=container, access_token=token)["id"]
    link = graph("GET", media, fields="permalink", access_token=token).get("permalink")
    return media, link


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    now = dt.datetime.now(IST)
    day = os.environ.get("POST_DATE") or now.date().isoformat()
    folder = ROOT / "posts" / day
    plan_file, status_file = folder / "plan.json", folder / "status.json"
    if not plan_file.exists():
        sys.exit(f"No plan for {day}; did the morning build run?")
    plan = json.loads(plan_file.read_text())
    status = json.loads(status_file.read_text()) if status_file.exists() else {}

    if a.slot:
        due = [p for p in plan if p["slot"] == a.slot]
    else:
        due = []
        for p in plan:
            if status.get(p["slot"], {}).get("instagram", {}).get("ok") is True or p["time_ist"] > now.strftime("%H:%M"):
                continue
            slot_time = dt.datetime.combine(now.date(), dt.time.fromisoformat(p["time_ist"]), IST)
            if now - slot_time > dt.timedelta(hours=MAX_LATE_HOURS):
                # too late: skip rather than post out of order (e.g. a missed morning build)
                status.setdefault(p["slot"], {}).setdefault("instagram", {"ok": None, "skipped": "too late"})
                continue
            due.append(p)
        status_file.write_text(json.dumps(status, indent=1))
    if not due:
        print("Nothing due.")
        return
    p = due[0]
    repo = os.environ.get("GITHUB_REPOSITORY", "hitesheidnani/hbe-social")
    image_url = f"https://raw.githubusercontent.com/{repo}/main/{p['image']}"
    print(f"Slot {p['slot']} ({p['time_ist']} IST, {p['kind']}): {image_url}")
    if a.dry_run:
        print(p["caption"])
        return

    rec = status.setdefault(p["slot"], {})
    try:
        media, link = post_instagram(image_url, p["caption"])
        rec["instagram"] = {"ok": True, "id": media, "url": link, "at": now.isoformat(timespec="seconds")}
        print("✅ Posted to Instagram:", link)
    except Exception as e:
        rec["instagram"] = {"ok": False, "error": str(e), "at": now.isoformat(timespec="seconds")}
        print("❌", e)
    status_file.write_text(json.dumps(status, indent=1))
    if not rec["instagram"]["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
