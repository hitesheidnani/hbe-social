"""Publish due posts from today's plan to Instagram.

Runs on a schedule. Each run publishes at most ONE post: the earliest slot whose time (IST)
has passed and that has not been published yet. Results are recorded in posts/<date>/status.json.

Usage:
  python publish.py                      # normal scheduled run
  python publish.py --slot psych         # publish a specific slot now (manual/test)
  python publish.py --dry-run            # show what would be posted
Env: IG_USER_ID, META_PAGE_TOKEN, FB_PAGE_ID, GITHUB_REPOSITORY (owner/name), optional POST_DATE (YYYY-MM-DD)
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error, datetime as dt
from pathlib import Path

ROOT = Path(__file__).parent
GRAPH = "https://graph.facebook.com"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
MAX_LATE_HOURS = 3
FN_URL = "hbecapital.net/funds"
CTA = (f"🧭 Try FundNavigator, our free tool to compare 2,000+ mutual funds, SIFs & PMS: "
       f"{FN_URL} (link in bio)")


def with_cta(caption):
    """Every post invites people to try FundNavigator: replace the old 'link in bio' line, or add the
    invitation just above the disclaimer."""
    lines = caption.split("\n")
    for i, l in enumerate(lines):
        if "link in bio" in l:
            lines[i] = CTA
            return "\n".join(lines)
    for i, l in enumerate(lines):
        if l.startswith("⚠️"):
            return "\n".join(lines[:i] + [CTA, ""] + lines[i:])
    return caption + "\n\n" + CTA


# Every post links to the other channels so people can follow everywhere.
CHANNELS = {
    "instagram": ("Instagram", "@hbecapital", "https://instagram.com/hbecapital"),
    "youtube": ("YouTube", "@hbecapital", "https://youtube.com/@hbecapital"),
    "x": ("X", "@hitesheidnani", "https://x.com/hitesheidnani"),
    "linkedin": ("LinkedIn", "Hitesh Eidnani", "https://linkedin.com/in/hitesheidnani"),
    "facebook": ("Facebook", "HBE Capital Investments", f"https://facebook.com/{os.environ.get('FB_PAGE_ID', '')}"),
}


def follow_line(platform):
    """'Follow us' line listing the other channels: handles on Instagram, clickable links elsewhere."""
    parts = []
    for key, (name, handle, url) in CHANNELS.items():
        if key == platform or (key == "facebook" and platform == "instagram"):
            continue
        if platform == "instagram" or not url or url.endswith("/"):
            parts.append(f"{name} {handle}")
        else:
            parts.append(f"{name}: {url}")
    return "📲 Follow HBE Capital everywhere: " + " · ".join(parts)


def for_platform(caption, platform):
    """Insert the follow line just above the disclaimer (or at the end)."""
    line = follow_line(platform)
    lines = caption.split("\n")
    for i, l in enumerate(lines):
        if l.startswith("⚠️"):
            return "\n".join(lines[:i] + [line, ""] + lines[i:])
    return caption + "\n\n" + line


def web_caption(caption):
    """Facebook / LinkedIn: links are clickable, so drop '(link in bio)' and use a full URL."""
    return caption.replace(f"{FN_URL} (link in bio)", f"https://{FN_URL}").replace("link in bio", f"https://{FN_URL}")
LINKEDIN_SLOTS = None   # None = every slot goes to LinkedIn (user asked for all posts)


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


def post_instagram(image_url, caption=None, story=False):
    ig, token = os.environ["IG_USER_ID"], os.environ["META_PAGE_TOKEN"]
    params = {"image_url": image_url, "access_token": token}
    if story:
        params["media_type"] = "STORIES"
    else:
        params["caption"] = caption
    container = graph("POST", f"{ig}/media", **params)["id"]
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


def post_carousel(image_urls, caption):
    ig, token = os.environ["IG_USER_ID"], os.environ["META_PAGE_TOKEN"]
    children = []
    for u in image_urls:
        cid = graph("POST", f"{ig}/media", image_url=u, is_carousel_item="true", access_token=token)["id"]
        children.append(cid)
    for cid in children:                     # each slide must be processed before the album is created
        for _ in range(30):
            st = graph("GET", cid, fields="status_code", access_token=token).get("status_code")
            if st == "FINISHED":
                break
            if st in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"Instagram could not process a carousel slide ({st})")
            time.sleep(3)
    parent = graph("POST", f"{ig}/media", media_type="CAROUSEL", children=",".join(children),
                   caption=caption, access_token=token)["id"]
    for _ in range(30):
        if graph("GET", parent, fields="status_code", access_token=token).get("status_code") == "FINISHED":
            break
        time.sleep(3)
    media = graph("POST", f"{ig}/media_publish", creation_id=parent, access_token=token)["id"]
    link = graph("GET", media, fields="permalink", access_token=token).get("permalink")
    return media, link


def post_facebook(image_urls, caption):
    """Post to the HBE Capital Investments Facebook Page: one photo, or several photos in one post."""
    page, token = os.environ["FB_PAGE_ID"], os.environ["META_PAGE_TOKEN"]
    caption = web_caption(caption)
    if len(image_urls) == 1:
        r = graph("POST", f"{page}/photos", url=image_urls[0], message=caption, access_token=token)
        post_id = r.get("post_id") or r["id"]
    else:
        ids = [graph("POST", f"{page}/photos", url=u, published="false", access_token=token)["id"] for u in image_urls]
        params = {"message": caption, "access_token": token}
        for i, pid in enumerate(ids):
            params[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
        post_id = graph("POST", f"{page}/feed", **params)["id"]
    return post_id, f"https://www.facebook.com/{post_id}"


def post_reel(mp4, caption, thumb_ms, share_to_feed=False):
    """Upload a local MP4 as a Reel via resumable upload (Reels tab only unless share_to_feed)."""
    ig, token = os.environ["IG_USER_ID"], os.environ["META_PAGE_TOKEN"]
    c = graph("POST", f"{ig}/media", media_type="REELS", upload_type="resumable", caption=caption,
              share_to_feed="true" if share_to_feed else "false", thumb_offset=str(thumb_ms), access_token=token)
    data = Path(mp4).read_bytes()
    req = urllib.request.Request(c["uri"], data=data, method="POST", headers={
        "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(data))})
    try:
        urllib.request.urlopen(req, timeout=300).read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Reel upload failed: {e.read()[:300]!r}") from None
    for _ in range(60):                      # video processing can take a few minutes
        st = graph("GET", c["id"], fields="status_code,status", access_token=token)
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram could not process the Reel: {st.get('status')}")
        time.sleep(10)
    else:
        raise RuntimeError("Reel processing timed out")
    media = graph("POST", f"{ig}/media_publish", creation_id=c["id"], access_token=token)["id"]
    link = graph("GET", media, fields="permalink", access_token=token).get("permalink")
    return media, link


_videos = {}


def video_for(p):
    """MP4 for this slot, or None: countdown Reel for ranked cards, static Reel for personal cards."""
    if p["slot"] in _videos:
        return _videos[p["slot"]]
    import tempfile
    v = None
    if p.get("as_reel"):
        from reel import static_reel
        v, _ = static_reel(ROOT / p["image"], Path(tempfile.mkdtemp()) / "card.mp4")
    elif p.get("reel"):
        from reel import make_reel
        v, _ = make_reel(ROOT / p["image"], p["reel"]["rows"], Path(tempfile.mkdtemp()) / "reel.mp4")
    _videos[p["slot"]] = v
    return v


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
    p = dict(due[0])
    p["caption"] = with_cta(p["caption"])
    repo = os.environ.get("GITHUB_REPOSITORY", "hitesheidnani/hbe-social")
    image_url = f"https://raw.githubusercontent.com/{repo}/main/{p['image']}"
    print(f"Slot {p['slot']} ({p['time_ist']} IST, {p['kind']}): {image_url}")
    if a.dry_run:
        print(p["caption"])
        return

    rec = status.setdefault(p["slot"], {})
    if rec.get("instagram", {}).get("ok") is True:
        print("Feed post already published:", rec["instagram"].get("url"))   # never post twice
    else:
        try:
            if p.get("as_reel"):            # personal cards: post the Reel itself (it also shows in the grid)
                media, link = post_reel(video_for(p), for_platform(p["caption"], "instagram"), 1000, share_to_feed=True)
            elif p.get("carousel"):
                media, link = post_carousel(
                    [f"https://raw.githubusercontent.com/{repo}/main/{c}" for c in p["carousel"]],
                    for_platform(p["caption"], "instagram"))
            else:
                media, link = post_instagram(image_url, for_platform(p["caption"], "instagram"))
            rec["instagram"] = {"ok": True, "id": media, "url": link, "at": now.isoformat(timespec="seconds")}
            print("✅ Posted to Instagram:", link)
        except Exception as e:
            rec["instagram"] = {"ok": False, "error": str(e), "at": now.isoformat(timespec="seconds")}
            print("❌", e)
    # Same post as a Story (a Story failure never undoes the feed post)
    if rec["instagram"]["ok"] and p.get("story_image") and not rec.get("instagram_story", {}).get("ok"):
        try:
            sid, _ = post_instagram(f"https://raw.githubusercontent.com/{repo}/main/{p['story_image']}", story=True)
            rec["instagram_story"] = {"ok": True, "id": sid, "at": now.isoformat(timespec="seconds")}
            print("✅ Posted as a Story")
        except Exception as e:
            rec["instagram_story"] = {"ok": False, "error": str(e), "at": now.isoformat(timespec="seconds")}
            print("⚠️ Story failed:", e)
    # Same post on the Facebook Page (independent of Instagram's result)
    if os.environ.get("FB_PAGE_ID") and not rec.get("facebook", {}).get("ok"):
        urls = ([f"https://raw.githubusercontent.com/{repo}/main/{c}" for c in p["carousel"]]
                if p.get("carousel") else [image_url])
        try:
            fid, flink = post_facebook(urls, for_platform(p["caption"], "facebook"))
            rec["facebook"] = {"ok": True, "id": fid, "url": flink, "at": now.isoformat(timespec="seconds")}
            print("✅ Posted to Facebook Page:", flink)
        except Exception as e:
            rec["facebook"] = {"ok": False, "error": str(e), "at": now.isoformat(timespec="seconds")}
            print("⚠️ Facebook failed:", e)

    # LinkedIn (personal profile), selected slots only
    if (LINKEDIN_SLOTS is None or p["slot"] in LINKEDIN_SLOTS) and os.environ.get("LI_TOKEN") and not rec.get("linkedin", {}).get("ok"):
        try:
            import linkedin
            files = [ROOT / c for c in p["carousel"]] if p.get("carousel") else [ROOT / p["image"]]
            lid, llink = linkedin.post(files, for_platform(p["caption"], "linkedin"))
            rec["linkedin"] = {"ok": True, "id": lid, "url": llink, "at": now.isoformat(timespec="seconds")}
            print("✅ Posted to LinkedIn:", llink)
        except Exception as e:
            rec["linkedin"] = {"ok": False, "error": str(e), "at": now.isoformat(timespec="seconds")}
            print("⚠️ LinkedIn failed:", e)

    # Countdown Reel for ranked cards (Reels tab only)
    if rec["instagram"]["ok"] and p.get("reel") and not rec.get("instagram_reel", {}).get("ok"):
        try:
            mp4 = video_for(p)
            rid, rlink = post_reel(mp4, for_platform(p["caption"], "instagram"), 13000)
            rec["instagram_reel"] = {"ok": True, "id": rid, "url": rlink, "at": now.isoformat(timespec="seconds")}
            print("✅ Posted Reel:", rlink)
        except Exception as e:
            rec["instagram_reel"] = {"ok": False, "error": str(e), "at": now.isoformat(timespec="seconds")}
            print("⚠️ Reel failed:", e)
    # YouTube Short for every video slot (max per day to stay within the free quota)
    if (p.get("reel") or p.get("as_reel")) and os.environ.get("YT_REFRESH_TOKEN") and not rec.get("youtube", {}).get("ok"):
        import youtube
        done_today = sum(1 for r in status.values() if r.get("youtube", {}).get("ok"))
        if done_today < youtube.MAX_PER_DAY:
            try:
                vid, ylink, privacy = youtube.upload_short(video_for(p), for_platform(p["caption"], "youtube"))
                rec["youtube"] = {"ok": True, "id": vid, "url": ylink, "privacy": privacy, "at": now.isoformat(timespec="seconds")}
                print("✅ Uploaded YouTube Short:", ylink, f"({privacy})")
            except Exception as e:
                rec["youtube"] = {"ok": False, "error": str(e), "at": now.isoformat(timespec="seconds")}
                print("⚠️ YouTube failed:", e)
    status_file.write_text(json.dumps(status, indent=1))
    if not rec["instagram"]["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
