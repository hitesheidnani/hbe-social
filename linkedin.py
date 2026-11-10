"""Post images (single or several) with text to Hitesh's LinkedIn profile via the Posts API.

Env: LI_TOKEN (member token with w_member_social, valid 60 days), LI_PERSON_URN (urn:li:person:...)
"""
import json, os, re, datetime as dt, urllib.request, urllib.error
from pathlib import Path

API = "https://api.linkedin.com/rest"
_version = None


def _req(method, url, body=None, headers=None, raw=None):
    h = {"Authorization": f"Bearer {os.environ['LI_TOKEN']}", "X-Restli-Protocol-Version": "2.0.0"}
    if _version:
        h["LinkedIn-Version"] = _version
    h.update(headers or {})
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if body is not None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        resp = urllib.request.urlopen(r, timeout=120)
        txt = resp.read()
        return resp.headers, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LinkedIn {e.code}: {e.read()[:300]!r}") from None


def _pick_version():
    """LinkedIn needs a monthly API version header (YYYYMM); use the newest one it accepts."""
    global _version
    if _version:
        return
    today = dt.date.today()
    last = None
    for k in range(0, 12):
        y, m = today.year, today.month - k
        while m <= 0:
            y, m = y - 1, m + 12
        _version = f"{y}{m:02d}"
        try:
            _req("POST", f"{API}/images?action=initializeUpload",
                 {"initializeUploadRequest": {"owner": os.environ["LI_PERSON_URN"]}})
            return
        except RuntimeError as e:
            last = e
            if "VERSION" not in str(e).upper() and "426" not in str(e):
                raise
    raise RuntimeError(f"no LinkedIn API version accepted: {last}")


def upload_image(path):
    _pick_version()
    _, r = _req("POST", f"{API}/images?action=initializeUpload",
                {"initializeUploadRequest": {"owner": os.environ["LI_PERSON_URN"]}})
    v = r["value"]
    _req("PUT", v["uploadUrl"], raw=Path(path).read_bytes(), headers={"Content-Type": "application/octet-stream"})
    return v["image"]


def little_text(text):
    """LinkedIn's 'little text' format: escape reserved characters, turn #words into real hashtags."""
    out = re.sub(r"[\\|{}@\[\]()<>*_~]", lambda m: "\\" + m.group(0), text)
    tags = []

    def keep(m):                               # real hashtags: #word starting with a letter
        tags.append("{hashtag|\\#|" + m.group(1) + "}")
        return f"\x00{len(tags) - 1}\x00"
    out = re.sub(r"(?<![\w\\])#([A-Za-z]\w*)", keep, out)
    out = out.replace("#", "\\#")              # any other '#' (e.g. 'MF Basics #12') is literal
    return re.sub(r"\x00(\d+)\x00", lambda m: tags[int(m.group(1))], out)


def li_caption(caption):
    """Adapt an Instagram caption for LinkedIn."""
    c = (caption.replace("hbecapital.net/funds (link in bio)", "https://hbecapital.net/funds")
         .replace("link in bio", "https://hbecapital.net/funds").replace("Follow @hbecapital", "Follow HBE Capital"))
    c = c.replace("@hbecapital", "HBE Capital")
    return little_text(c)


def post(image_paths, caption, alt="HBE Capital chart"):
    _pick_version()
    ids = [upload_image(p) for p in image_paths]
    content = ({"media": {"id": ids[0], "altText": alt}} if len(ids) == 1 else
               {"multiImage": {"images": [{"id": i, "altText": alt} for i in ids]}})
    headers, _ = _req("POST", f"{API}/posts", {
        "author": os.environ["LI_PERSON_URN"], "commentary": li_caption(caption), "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "content": content, "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False})
    pid = headers.get("x-restli-id") or headers.get("x-linkedin-id", "")
    return pid, f"https://www.linkedin.com/feed/update/{pid}/"
