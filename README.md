# hbe-social

Automated Instagram posts for HBE Capital (@hbecapital), built from FundNavigator data.

## Daily schedule (IST)

| Time  | Post |
|-------|------|
| 06:00 | Build: `daily.py` renders the day's cards and captions into `posts/<date>/` |
| 09:00 | Market psychology quote (`content/psychology.json`, rotates daily) |
| 12:30 | Top 10 funds in a category, long horizon (3y / 5y / 10y) |
| 17:30 | Feature: SIP card (Mon, Fri), SIF tracker (Tue), momentum funds (Wed, Sun), PMS (Thu, Sat) |
| 20:00 | Top 10 funds in a category, short horizon (3m / 6m / 1y) |

Data comes from https://funds.hbecapital.net/data (FundNavigator's nightly refresh).
Instagram fetches each image from this repo's raw URL, which is why the repo is public.

## Run by hand

- Actions → **Build daily posts** → Run workflow (optionally with a date)
- Actions → **Publish to Instagram** → Run workflow, slot `psych` / `long` / `feature` / `short`
- Locally: `DATA_DIR=../fundnavigator/web/public/data python daily.py 2026-11-10`

## Secrets (Settings → Secrets → Actions)

- `IG_USER_ID`: Instagram business account id
- `META_PAGE_TOKEN`: non-expiring Page token from the "HBE Social Poster" Meta app

## Editing content

- Psychology quotes: `content/psychology.json` (quote, author, note)
- Fund categories, rotation and captions: `daily.py`
- Card designs: `mf_posts.py`, `brand.py`

All MF posts carry the ARN, the AMFI risk line and "past performance may or may not be sustained in future".
