"""Reel scripts (batch 1) and the free guide PDF. python growth_docs.py <social_folder>"""
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).parent
pdfmetrics.registerFont(TTFont("Inter", str(ROOT / "fonts/Inter-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Inter-Bold", str(ROOT / "fonts/Inter-Bold.ttf")))
NAVY, TEAL, GREY = colors.HexColor("#0B1220"), colors.HexColor("#0F8F72"), colors.HexColor("#5B6478")
H1 = ParagraphStyle("h1", fontName="Inter-Bold", fontSize=22, leading=27, textColor=NAVY, spaceAfter=4)
H2 = ParagraphStyle("h2", fontName="Inter-Bold", fontSize=14, leading=18, textColor=TEAL, spaceBefore=12, spaceAfter=4)
P = ParagraphStyle("p", fontName="Inter", fontSize=10.5, leading=15.5, textColor=NAVY, spaceAfter=5)
B = ParagraphStyle("b", parent=P, fontName="Inter-Bold")
S = ParagraphStyle("s", parent=P, fontSize=8.5, leading=12, textColor=GREY)
DISC = ("For educational purposes only. Not investment advice. Mutual fund investments are subject to market risks, "
        "read all scheme related documents carefully. HBE Capital · AMFI-registered Mutual Fund Distributor · ARN-275597")

SCRIPTS = [
 ("Why your SIP feels useless for 5 years", "Your SIP isn't broken. You're just in the boring part.",
  "For the first few years, almost all of your SIP's value is the money you put in. The growth looks tiny, and that's when most people quit. But compounding is back-loaded. In a 20-year SIP, roughly half of the final value shows up in the last five or six years. So the early years aren't wasted. They're the foundation. The only real mistake is stopping before the growth has had time to show.",
  "Compounding is back-loaded", "Your SIP isn't broken, you're in the boring part. Stay."),
 ("The 50% rule nobody tells you", "If your portfolio falls 50%, how much do you need to get back to even?",
  "Most people say fifty percent. It's actually one hundred. Lose half, and you need to double what's left just to break even. That's why professional investors think about the downside first. Avoiding big losses matters more than catching big gains. Before you ask how much can I make, ask how much can I lose, and can I live with it.",
  "-50% needs +100%", "Protect the downside first. The maths demands it."),
 ("Stop checking your portfolio daily", "The more you check your portfolio, the worse your returns can get.",
  "Here's why. Markets are up on a little over half of all days, but over any five-year period they've been up far more often. So if you look daily, you see losses almost half the time, and losses hurt about twice as much as gains feel good. That pain pushes you to sell at the wrong time. Check once a quarter. You'll see the same portfolio, with a lot less noise.",
  "Daily = noise. Quarterly = signal.", "Check less. Stay invested longer."),
 ("What is momentum investing, in 30 seconds", "Buy high, sell higher. Sounds wrong. Here's why it works.",
  "Momentum investing buys the stocks that have been rising the most over the past six to twelve months, and drops them when they stop. It's one of the most researched effects in finance, and it exists because people are slow to react to good news and tend to follow each other. The catch: when trends reverse, momentum falls hard. So it needs rules, a fixed rebalance, and a sensible size in your portfolio.",
  "Rules, rebalance, right size", "Momentum: ride strength, exit weakness, follow the rules."),
 ("Last year's top fund is a trap", "The number one fund last year is rarely number one this year.",
  "Leadership in markets rotates. A fund tops the chart because its style was in favour, and styles change. Investors who chase last year's winner often arrive just as it cools off. A better test: has the fund beaten its benchmark across many periods, and how did it behave in a bad year? Consistency beats one great year.",
  "Chase consistency, not rank", "Stop picking funds from last year's ranking."),
 ("Direct vs Regular: the honest version", "I'm a mutual fund distributor. Here's the honest answer on direct versus regular.",
  "Direct plans cost less, because there's no distributor commission. Regular plans cost a bit more, and that pays for guidance: choosing funds, reviews, paperwork, and someone to stop you from panic-selling in a crash. If you're disciplined and happy doing it all yourself, direct is fine. If you'd value a guide, regular can be worth it. The expensive mistake isn't the plan. It's the panic.",
  "The real cost is behaviour", "Direct or regular? The honest answer from a distributor."),
 ("Three questions before you buy anything", "Ask three questions before any investment. Most people can't answer the third.",
  "One: why am I buying this? Two: what would make me sell? Three: how much can I afford to lose on it? If you can't answer all three, you're not investing, you're hoping. Write the answers down before you put in a rupee. On a bad day, that note will be worth more than any tip.",
  "Why · When to sell · How much", "Three questions. Answer them before you invest."),
 ("Don't stop your SIP in a crash", "The worst time to stop a SIP is exactly when you want to.",
  "When markets fall, your SIP buys more units for the same money. Those cheaper units do the heavy lifting when markets recover. Stop the SIP in a crash, and you skip the sale. Nobody knows when the recovery starts, and the best days often come right after the worst. So the rule is simple: keep the SIP running, especially when it feels uncomfortable.",
  "A crash is a sale", "Keep your SIP running when it hurts most."),
 ("What wealthy families do differently", "Wealthy families ask a different first question about money.",
  "Most investors ask, what will give me the highest return? Families who have kept wealth for generations ask, how do we avoid the big loss? They decide the mix of equity, debt and gold first, they stick to rules, and they review on a schedule, not on headlines. It's less exciting. It also works.",
  "Protect first, then compound", "The first question wealthy families ask."),
 ("The step-up SIP trick", "One small change can roughly double your SIP's final value.",
  "It's called a step-up. Every year, when your income rises, raise your SIP by ten percent. As an illustration at an assumed twelve percent a year, ten thousand a month for twenty years grows to about ninety-two lakh. With a ten percent yearly step-up, it's about one point eight six crore. Same start, same years. Set it once and let it run. This is an illustration, not a promise of returns.",
  "+10% a year", "Step up your SIP every year."),
]

def scripts(out):
    d = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm,
                          title="Reel scripts, batch 1", author="HBE Capital")
    s = [Paragraph("Talking-head Reels: scripts, batch 1", H1),
         Paragraph("10 scripts, 30-45 seconds each. Record 2-3 a week.", P),
         Paragraph("How to record", H2),
         Paragraph("1. Phone upright (vertical), at eye level, window light on your face, quiet room.<br/>"
                   "2. Say the HOOK in the first 2 seconds, looking at the lens. No 'Hi, I'm Hitesh' at the start.<br/>"
                   "3. Speak a little faster than feels natural. One take is fine; small stumbles look human.<br/>"
                   "4. Post from the Instagram app as a Reel: add captions (Instagram's auto-captions), pick a trending "
                   "audio at low volume, paste the caption below. Share the same video to YouTube Shorts and LinkedIn.<br/>"
                   "5. Reply to every comment in the first hour.", P),
         Paragraph("Every caption should end with: " + DISC, S)]
    for i, (title, hook, body, onscreen, cap) in enumerate(SCRIPTS, 1):
        s.append(KeepTogether([Paragraph(f"{i}. {title}", H2),
                               Paragraph(f"<b>Hook (first 2 seconds):</b> {hook}", P),
                               Paragraph(f"<b>Say:</b> {body}", P),
                               Paragraph(f"<b>Text on screen:</b> {onscreen}", P),
                               Paragraph(f"<b>Caption:</b> {cap} Follow @hbecapital for more. "
                                         "#investing #mutualfunds #sip #personalfinance #stockmarketindia", P)]))
    d.build(s)

QUESTIONS = [
 ("What is this money for, and when will I need it?", "The goal and the date decide almost everything else. Money needed within 3 years doesn't belong in equity funds; goals 7+ years away can carry more equity."),
 ("Which category is this fund in, and why that category?", "Large cap, flexi cap, mid cap, small cap, hybrid and debt behave very differently. Pick the category for your goal first, then a fund within it."),
 ("How has it done against its benchmark over 5, 7 and 10 years?", "One strong year means little. Look for funds that have beaten their benchmark (Total Return Index) over several long periods."),
 ("How much did it fall in bad years?", "Check the worst drawdown and how it did in years like 2008, 2011, 2018 and 2020. Ask yourself honestly whether you could have held on."),
 ("What does it cost?", "Compare the expense ratio with other funds in the same category. Costs compound just like returns. Understand the difference between Direct and Regular plans."),
 ("Who manages it, and for how long?", "A long, steady record under the same manager and process is worth more than a recent hot streak under a new one."),
 ("How big is the fund?", "Very small funds can be risky to run; very large small-cap funds can find it hard to stay nimble. Size should fit the category."),
 ("Does it overlap with what I already own?", "Two funds holding the same stocks don't diversify you. Check the top holdings before adding another fund."),
 ("What is the exit load and the tax on gains?", "Know the cost of leaving early and how gains are taxed before you invest, so they don't surprise you later."),
 ("What will I do if it falls 20%?", "Decide now, in calm conditions. If the answer is 'sell', choose a less volatile fund or invest a smaller amount."),
]

def guide(out):
    d = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm,
                          title="10 questions to ask before buying any mutual fund", author="HBE Capital")
    s = [Paragraph("HBE Capital", ParagraphStyle("k", parent=B, textColor=TEAL, fontSize=12)), Spacer(1, 6),
         Paragraph("10 questions to ask before buying any mutual fund", H1),
         Paragraph("A short checklist from Hitesh Eidnani, Managing Partner, HBE Capital. Use it before every new "
                   "investment, and once a year for the funds you already hold.", P), Spacer(1, 6)]
    for i, (q, a) in enumerate(QUESTIONS, 1):
        s.append(KeepTogether([Paragraph(f"{i}. {q}", H2), Paragraph(a, P)]))
    s += [Spacer(1, 10), Paragraph("Check the numbers yourself", H2),
          Paragraph("FundNavigator, our free tool, shows returns against benchmarks, calendar-year performance, risk and "
                    "rankings for 2,000+ mutual funds, SIFs and PMS: <b>hbecapital.net/funds</b>", P),
          Paragraph("Follow HBE Capital: Instagram and YouTube @hbecapital · X @hitesheidnani · "
                    "LinkedIn linkedin.com/in/hitesheidnani", P), Spacer(1, 10), Paragraph(DISC + " Past performance may or "
                    "may not be sustained in future. This checklist is general information, not a recommendation of any fund.", S)]
    d.build(s)

if __name__ == "__main__":
    base = Path(sys.argv[1])
    scripts(base / "reels" / "Reel scripts - batch 1.pdf")
    guide(base / "lead-magnet" / "10 questions before buying a mutual fund - HBE Capital.pdf")
    guide(ROOT / "assets" / "10-questions-mutual-fund.pdf")
    print("ok")
