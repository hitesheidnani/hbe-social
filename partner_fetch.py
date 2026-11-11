"""Find a chart by a partner creator (content/chart_partners.json) among the charts featured on The Chart Report.

Only creators who gave permission are used. The chart image is the creator's; The Chart Report is credited as
where it was spotted, and their write-ups are not copied. A handful of polite requests per day.
"""
import html, json, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
BASE = "https://www.thechartreport.com"
UA = {"User-Agent": "HBECapitalBot/1.0 (+https://hbecapital.net)"}
USED = ROOT / "partner_charts" / "used.json"


def _get(url, binary=False):
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    return data if binary else data.decode("utf-8", "ignore")


def recent_posts(limit=4):
    """Latest daily posts, newest first (links look like /11-09-2026 or /11-04-26)."""
    found = {}
    for m, d, y in re.findall(r'thechartreport\.com/(\d{2})-(\d{2})-(\d{2,4})"', _get(BASE + "/")):
        key = (int(y) % 100, int(m), int(d))
        found[key] = f"{BASE}/{m}-{d}-{y}"
    return [found[k] for k in sorted(found, reverse=True)[:limit]]


def charts(post_url):
    """[(handle, status_url, image_url)] in the order the page shows them."""
    out = []
    for b in re.split(r"<hr\s*/?>", _get(post_url)):
        img = re.search(r'href="(https://www\.thechartreport\.com/sites/default/files/[^"]+)"', b)
        x = re.search(r'href="(https://x\.com/([A-Za-z0-9_]+)/status/\d+)', b)
        if img and x and x.group(2).lower() != "thechartreport":
            out.append((x.group(2), x.group(1), html.unescape(img.group(1))))
    return out


def pick(out_dir):
    """Download the first unused chart by a partner. Returns (image_path, partner, status_url) or None."""
    partners = json.loads((ROOT / "content" / "chart_partners.json").read_text())
    used = set(json.loads(USED.read_text())) if USED.exists() else set()
    for post in recent_posts():
        for handle, status, img in charts(post):
            pt = partners.get(handle.lower())
            if not pt or status in used:
                continue
            ext = Path(img.split("?")[0]).suffix or ".jpg"
            dest = Path(out_dir) / f"partner_src{ext}"
            dest.write_bytes(_get(img.replace(" ", "%20"), binary=True))
            used.add(status)
            USED.write_text(json.dumps(sorted(used), indent=1))
            return dest, pt, status
    return None


if __name__ == "__main__":
    for p in recent_posts():
        print(p, [h for h, _, _ in charts(p)])
