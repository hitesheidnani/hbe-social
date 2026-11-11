"""Upload a vertical MP4 to the HBE Capital YouTube channel as a Short (YouTube Data API v3, free quota).

Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (channel: HBE Capital, hitesh@hbecapital.net).
Note: until Google approves the API audit, uploads from this project are kept PRIVATE by YouTube.
"""
import json, os, re, urllib.parse, urllib.request, urllib.error
from pathlib import Path

MAX_PER_DAY = 5          # 1,600 quota units per upload; free quota is 10,000 a day


def _token():
    body = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                   "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=body),
                                            timeout=30))["access_token"]


def title_from(caption):
    first = caption.strip().splitlines()[0].strip().strip('"')
    first = re.sub(r"\s+", " ", first)
    first = first[:88].rsplit(" ", 1)[0] + "…" if len(first) > 90 else first
    return f"{first} #Shorts"


def upload_short(mp4, caption):
    tok = _token()
    desc = (caption.replace("hbecapital.net/funds (link in bio)", "https://hbecapital.net/funds")
            .replace("link in bio", "https://hbecapital.net/funds"))[:4900]
    meta = {"snippet": {"title": title_from(caption), "description": desc, "categoryId": "27",
                        "tags": ["investing", "mutual funds", "stock market", "HBE Capital"]},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    data = Path(mp4).read_bytes()
    init = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(), method="POST",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(data))})
    try:
        loc = urllib.request.urlopen(init, timeout=60).headers["Location"]
        res = json.load(urllib.request.urlopen(urllib.request.Request(
            loc, data=data, method="PUT", headers={"Content-Type": "video/mp4"}), timeout=600))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"YouTube {e.code}: {e.read()[:300]!r}") from None
    vid = res["id"]
    return vid, f"https://youtube.com/shorts/{vid}", res.get("status", {}).get("privacyStatus")
