"""Write the posting schedule as a branded PDF: python schedule_pdf.py <out.pdf>"""
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).parent
pdfmetrics.registerFont(TTFont("Inter", str(ROOT / "fonts/Inter-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Inter-Bold", str(ROOT / "fonts/Inter-Bold.ttf")))
NAVY, TEAL, GOLD, GREY, LIGHT = (colors.HexColor(c) for c in ("#0B1220", "#0F8F72", "#B7791F", "#5B6478", "#EEF3F8"))

H1 = ParagraphStyle("h1", fontName="Inter-Bold", fontSize=20, leading=24, textColor=NAVY)
H2 = ParagraphStyle("h2", fontName="Inter-Bold", fontSize=13, leading=17, textColor=TEAL, spaceBefore=10, spaceAfter=4)
P = ParagraphStyle("p", fontName="Inter", fontSize=9, leading=12.5, textColor=NAVY)
PB = ParagraphStyle("pb", parent=P, fontName="Inter-Bold")
SMALL = ParagraphStyle("s", parent=P, fontSize=8, leading=11, textColor=GREY)
CELL = ParagraphStyle("c", parent=P, fontSize=8.6, leading=11.5)
CELLB = ParagraphStyle("cb", parent=CELL, fontName="Inter-Bold")


def table(rows, widths, header=True):
    esc = lambda c: str(c).replace("&", "&amp;")
    data = [[Paragraph(esc(c), CELLB if (header and i == 0) or j == 0 else CELL) for j, c in enumerate(r)]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D3E0")),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT)]
    t.setStyle(TableStyle(style))
    return t


def build(out):
    doc = SimpleDocTemplate(str(out), pagesize=landscape(A4), leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm, title="HBE Capital posting schedule",
                            author="HBE Capital")
    W = landscape(A4)[0] - 28 * mm
    s = [Paragraph("HBE Capital · Social media posting schedule", H1),
         Paragraph("Updated 10 Nov 2026 (evening) · all times IST · fully automatic (GitHub, runs with your PC off)", SMALL),
         Spacer(1, 6),
         Paragraph("Channels: every post goes to <b>Instagram</b> (post + Story; ranked fund lists also as a "
                   "10→1 countdown Reel), the <b>HBE Capital Investments Facebook Page</b> and <b>LinkedIn</b> "
                   "(Hitesh Eidnani's profile). The system checks every 15 minutes, so each post goes out within "
                   "about 15 minutes of its slot; a slot more than 3 hours late is skipped rather than posted out of order.", P),
         Paragraph("Daily posts (10-11 a day, 3-4 of them on US markets)", H2),
         table([
             ["Time", "Post", "What it shows", "Rotation", "Extras"],
             ["08:00", "Market update", "Nifty 50, Nifty Bank, Midcap 150, Smallcap 250 · S&P 500, Nasdaq 100, Dow, Russell 2000 · "
              "Gold, Brent, US 10Y, USD/INR. Price, 1-day change, % vs 200-day average, trend (Bullish / Bearish, Neutral within ±1%; "
              "Rising / Falling for yield and USD/INR)", "Same format daily", "Story"],
             ["08:30", "US close / US market health", "Tue-Fri: S&P 500, Nasdaq 100, Dow, Russell 2000, VIX, US 10Y yield, Dollar Index, Magnificent 7 and "
              "11 S&P sectors, last session's moves. Saturday: weekly US market health: trend vs 50/100/200-day averages "
              "(green/red), breadth of all S&P 500 stocks (% above averages, new highs vs lows, advancers vs decliners), "
              "Risk-on / Neutral / Risk-off", "Tue-Sat", "Story"],
             ["09:00", "Market psychology", "Quote card with author + short lesson in the caption: Mark Douglas, Livermore, "
              "Seykota, Buffett, Munger, Templeton, Lynch, maxims (cut losses short, buy high sell higher)",
              "40 quotes, one a day", "Story"],
             ["11:00", "Market Monitor", "Nifty indices from NSE (price returns). Heatmap of 1y / 3y / 5y returns, or "
              "'How far from the top?' table: % from all-time high, ATH date, days since ATH, % from 52-week high",
              "Mon Broad heatmap · Tue Sectoral heatmap · Wed Broad drawdown · Thu Strategy heatmap · Fri Thematic "
              "heatmap · Sat Sectoral drawdown · Sun Thematic/Strategy drawdown (alternate weeks). Heatmap period "
              "rotates 1y → 3y → 5y each week", "Story"],
             ["12:30", "Top 10 funds (long term)", "Top 10 funds in a category by 5 / 7 / 10-year CAGR vs benchmark, "
              "how many beat the index, median fund", "9 categories: Small, Flexi, Mid, Large, ELSS, Large & Mid, "
              "Multi, Value, Focused", "Story + Reel"],
             ["13:30", "Magnificent 7 spotlight (US)", "One stock a day (Apple, Microsoft, Nvidia, Amazon, Alphabet, Meta, "
              "Tesla): 1-year chart with 200-day average, trend, distance from all-time high, 52-week range, 1/3/5-year returns",
              "Rotates daily", "Story"],
             ["15:00", "Education", "MF Basics carousel (5-6 slides) OR Power of compounding illustration",
              "Alternate days. 25 MF Basics lessons · compounding: SIP at 12%/15%, start early (25 vs 35), "
              "step-up SIP, lumpsum & rule of 72", "Story"],
             ["17:30", "Feature", "Mon SIP card (5 yrs) · Tue SIF Performance Sheet (all SIFs by strategy, 1W/1M/3M/6M/"
              "since launch, 2-slide carousel) · Wed Momentum funds (1 yr) · Thu PMS Performance Sheet (all AUMs; equity, "
              "multi-asset, hybrid, debt; carousel) · Fri SIP card (10 yrs) · Sat PMS top 10 (3 yrs) · Sun Momentum (3 yrs)",
              "By weekday", "Story (+ Reel on ranked cards)"],
             ["19:00", "US theme", "Mon S&P sector heatmap · Tue S&P 500 in rupees vs Nifty 50 · Wed US indices & Mag 7 "
              "vs all-time highs · Thu US style monitor (growth/value, large/small, equal-weight, momentum, quality, "
              "low vol) · Fri S&P 500 calendar-year returns · Sat US Investing Basics carousel · Sun US weekly wrap",
              "By weekday; periods rotate 1y/3y/5y", "Story"],
             ["20:00", "Top 10 funds (1-3 yrs)", "Top 10 funds in a category by 1 / 2 / 3-year CAGR vs benchmark",
              "Same 9 categories, different one from 12:30", "Story + Reel"],
             ["21:30", "US investing wisdom", "Quote card: Buffett, Bogle, Lynch, Graham, Munger, Templeton, Fisher",
              "20 quotes, one a day", "Story"],
         ], [16 * mm, 32 * mm, 105 * mm, 85 * mm, W - 238 * mm]),
         Paragraph("Weekly", H2),
         table([
             ["When", "What", "How"],
             ["Weekly", "The Disciplined Investor: LinkedIn Newsletter article (800-1,200 words with charts), "
              "same article on Substack", "Claude drafts it with data and charts; you paste and publish (about 10 min). "
              "Issue #1: 'How many active funds actually beat their index?'"],
         ], [22 * mm, 110 * mm, W - 132 * mm]),
         PageBreak(),
         Paragraph("Rules every post follows", H2),
         table([
             ["Rule", "Detail"],
             ["Disclaimer", "'For educational purposes only. Not investment advice.' on every image and caption"],
             ["Mutual fund posts", "AMFI risk line, 'Past performance may or may not be sustained in future', "
              "HBE Capital · AMFI-registered MFD · ARN-275597"],
             ["Return periods", "Never under 1 year (exception: SIFs, a new category, may show 3 or 6 months, labelled "
              "absolute)"],
             ["Data", "Funds: AMFI NAVs via FundNavigator (Regular plan, Growth). PMS: APMI. Indices: NSE. US & "
              "commodities: Yahoo Finance. A post is skipped if its data can't be refreshed"],
             ["Compounding", "Always labelled an illustration at an assumed rate, not a projection for any fund"],
             ["Captions", "Keyword-rich first line, save/share/comment prompt, max 5 hashtags (Instagram limit); "
              "on Facebook and LinkedIn 'link in bio' becomes hbecapital.net/funds"],
             ["Branding", "HBE Capital logo top and bottom of every image, @hbecapital"],
             ["FundNavigator", "Every caption invites readers to try FundNavigator (hbecapital.net/funds); clickable on "
              "Facebook and LinkedIn, 'link in bio' on Instagram"],
         ], [38 * mm, W - 38 * mm]),
         Paragraph("Planned, not built yet", H2),
         table([
             ["Item", "Plan"],
             ["X (Twitter)", "Automation setup still to do (developer account, possibly a paid API plan)"],
             ["LinkedIn company page", "Needs LinkedIn's Community Management API approval; posts go to your profile until then"],
         ], [45 * mm, W - 45 * mm]),
         Paragraph("Maintenance", H2),
         table([
             ["Task", "When", "How"],
             ["Renew LinkedIn token", "Every 60 days (next ~8 Jan 2027)", "linkedin.com/developers/tools/oauth/token-generator "
              "(openid, profile, w_member_social) → Claude stores it"],
             ["Reset Meta app secret", "Once (it was shown in chat)", "developers.facebook.com → HBE Social Poster → "
              "App settings → Basic → Reset"],
             ["Change content", "Any time", "Quotes, lessons, rotations live in the hbe-social repo (content/*.json, daily.py)"],
         ], [45 * mm, 55 * mm, W - 100 * mm]),
         Spacer(1, 8),
         Paragraph("Repo: github.com/hitesheidnani/hbe-social · Daily images & captions: posts/&lt;date&gt;/ · "
                   "Run a post by hand: GitHub → Actions → Publish to Instagram → Run workflow (slot name)", SMALL)]
    doc.build(s)
    print("wrote", out)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "schedule.pdf")
