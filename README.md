# hbe-social

Automated Instagram posts for HBE Capital (@hbecapital), built from FundNavigator data.

## Daily schedule (IST)

| Time  | Post |
|-------|------|
| 06:00 | Build: `daily.py` renders the day's cards and captions into `posts/<date>/` |
| 08:00 | Market update: Nifty 50/Bank/Midcap 150/Smallcap 250, S&P 500, Nasdaq 100, Dow, Russell 2000, gold, Brent, US 10Y, USD/INR; 1-day change and 200-DMA trend (`update_post.py`) |
| 09:00 | Market psychology quote (`content/psychology.json`, rotates daily) |
| 11:00 | Market Monitor: Nifty index heatmaps (1y/3y/5y) or drawdown-from-high tables (`market_posts.py`, history in `data/indices/`) |
| 12:30 | Top 10 funds in a category, long horizon (5y / 7y / 10y) |
| 15:00 | MF Basics carousel (even days, `content/education.json`) or power-of-compounding card (odd days) |
| 17:30 | Feature: SIP card (Mon, Fri), SIF tracker (Tue), momentum funds (Wed, Sun), PMS (Thu, Sat) |
| 20:00 | Top 10 funds in a category, 1y / 2y / 3y (never under 1 year, except SIFs) |

Data comes from https://funds.hbecapital.net/data (FundNavigator's nightly refresh).
Instagram fetches each image from this repo's raw URL, which is why the repo is public.

## Run by hand

- Actions → **Build daily posts** → Run workflow (optionally with a date)
- Actions → **Publish to Instagram** → Run workflow, slot `psych` / `long` / `feature` / `short`
- Locally: `DATA_DIR=../fundnavigator/web/public/data python daily.py 2026-11-10`

## Where posts go

- Instagram (post + Story; ranked cards also as a countdown Reel) and the HBE Capital Investments Facebook Page: every slot
- LinkedIn (Hitesh's profile): every slot

## Secrets (Settings → Secrets → Actions)

- `IG_USER_ID`: Instagram business account id
- `META_PAGE_TOKEN`: non-expiring Page token from the "HBE Social Poster" Meta app
- `FB_PAGE_ID`: HBE Capital Investments Facebook Page
- `LI_TOKEN`, `LI_PERSON_URN`: LinkedIn member token (expires every 60 days; regenerate at
  linkedin.com/developers/tools/oauth/token-generator with openid, profile, w_member_social)

## Editing content

- Psychology quotes: `content/psychology.json` (quote, author, note)
- MF Basics lessons: `content/education.json` (title, hook, slides, takeaway, tags)
- Compounding rotation: `COMPOUNDING` in `daily.py`; card designs in `edu_posts.py`
- Fund categories, rotation and captions: `daily.py`
- Card designs: `mf_posts.py`, `brand.py`

All MF posts carry the ARN, the AMFI risk line and "past performance may or may not be sustained in future".
