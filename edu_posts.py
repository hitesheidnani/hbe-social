"""Education carousels ('MF Basics') and power-of-compounding cards."""
import textwrap
from pathlib import Path

from brand import (canvas, brand_badge, footer, save, plt, FancyBboxPatch, HANDLE,
                   BG, PANEL, GRID, TEXT, MUTED, ACCENT, GOLD)

ILLUSTRATIVE = ("Illustration only, at an assumed constant {r:.0f}% annual return. Real returns vary, can be "
                "negative, and are not guaranteed. Not a projection for any fund.")


def wrap(text, width):
    return "\n".join(textwrap.fill(p, width) for p in text.split("\n"))


# ---------------------------------------------------------------- education carousel
def edu_carousel(topic, number, out_dir, series="MF BASICS", foot="mf"):
    """Cover + one slide per point + takeaway slide. Returns list of JPEG paths."""
    out_dir = Path(out_dir)
    slides, total = [], len(topic["slides"]) + 2

    def frame(i):
        fig = canvas()
        brand_badge(fig, 0.06, 0.955, size=0.85)
        fig.text(0.94, 0.955, f"{i}/{total}", color=MUTED, fontsize=15, ha="right", va="center")
        fig.text(0.06, 0.885, f"{series} #{number}", color=ACCENT, fontsize=15, weight="semibold")
        return fig

    fig = frame(1)                                                          # cover
    fig.text(0.06, 0.60, wrap(topic["title"], 16), color=TEXT, fontsize=60, weight="heavy",
             va="center", linespacing=1.12)
    fig.text(0.06, 0.34, wrap(topic["hook"], 34), color=MUTED, fontsize=25, va="center", linespacing=1.4)
    fig.text(0.06, 0.21, "Swipe  →", color=GOLD, fontsize=22, weight="bold")
    footer(fig, foot)
    slides.append(save(fig, out_dir / "slide_01"))

    for k, (head, body) in enumerate(topic["slides"], 1):                   # one point per slide
        fig = frame(k + 1)
        fig.text(0.06, 0.78, f"{k:02d}", color=GOLD, fontsize=64, weight="heavy", va="center")
        fig.text(0.06, 0.68, wrap(head, 24), color=TEXT, fontsize=40, weight="bold", va="top", linespacing=1.2)
        n_head = len(wrap(head, 24).splitlines())
        line_y = 0.68 - 0.055 * n_head - 0.02
        fig.add_artist(plt.Line2D([0.06, 0.16], [line_y, line_y], color=ACCENT, lw=3, transform=fig.transFigure))
        fig.text(0.06, line_y - 0.04, wrap(body, 34), color=MUTED, fontsize=28, va="top", linespacing=1.55)
        footer(fig, foot)
        slides.append(save(fig, out_dir / f"slide_{k + 1:02d}"))

    fig = frame(total)                                                      # takeaway + CTA
    fig.text(0.06, 0.74, "KEY TAKEAWAY", color=GOLD, fontsize=18, weight="bold")
    fig.text(0.06, 0.55, wrap(topic["takeaway"], 26), color=TEXT, fontsize=40, weight="bold",
             va="center", linespacing=1.3)
    fig.add_artist(FancyBboxPatch((0.06, 0.17), 0.88, 0.13, boxstyle="round,pad=0,rounding_size=0.02",
                                  transform=fig.transFigure, fc=PANEL, ec=ACCENT, lw=1.5))
    fig.text(0.5, 0.255, f"Follow {HANDLE} for daily investing basics", color=TEXT, fontsize=24,
             weight="semibold", ha="center", va="center")
    fig.text(0.5, 0.205, "Save this post to revisit later", color=MUTED, fontsize=19, ha="center", va="center")
    footer(fig, foot)
    slides.append(save(fig, out_dir / f"slide_{total:02d}"))
    return slides


# ---------------------------------------------------------------- compounding maths
def sip_fv(monthly, rate, years, step=0.0):
    """Value of a monthly SIP (invested at the start of each month), optional yearly step-up."""
    r = (1 + rate) ** (1 / 12) - 1
    value, invested, path = 0.0, 0.0, []
    for y in range(years):
        amt = monthly * (1 + step) ** y
        for _ in range(12):
            value = (value + amt) * (1 + r)
            invested += amt
        path.append((invested, value))
    return value, invested, path


def inr(v):
    """₹ in lakh / crore, Indian style."""
    if v >= 1e7:
        return f"₹{v / 1e7:.2f} crore".replace(".00 ", " ")
    if v >= 1e5:
        return f"₹{v / 1e5:.1f} lakh".replace(".0 ", " ")
    return f"₹{v:,.0f}"


# ---------------------------------------------------------------- compounding cards
def _card_frame(kicker, title, subtitle):
    fig = canvas()
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.895, kicker.upper(), color=ACCENT, fontsize=15, weight="semibold")
    fig.text(0.06, 0.845, title, color=TEXT, fontsize=36, weight="heavy", va="center")
    fig.text(0.06, 0.80, subtitle, color=MUTED, fontsize=15, va="center")
    return fig


def _tiles(fig, items, y=0.215):
    w = 0.88 / len(items)
    for i, (label, value, col) in enumerate(items):
        x = 0.06 + i * w
        fig.add_artist(FancyBboxPatch((x + 0.006, y), w - 0.012, 0.085, boxstyle="round,pad=0,rounding_size=0.012",
                                      transform=fig.transFigure, fc=PANEL, ec=GRID))
        fig.text(x + w / 2, y + 0.058, label, color=MUTED, fontsize=13, ha="center", va="center")
        fig.text(x + w / 2, y + 0.027, value, color=col, fontsize=22, weight="bold", ha="center", va="center")


def _note_and_footer(fig, rate):
    fig.text(0.5, 0.165, wrap(ILLUSTRATIVE.format(r=rate * 100), 110), color=MUTED, fontsize=10.5,
             ha="center", va="center", linespacing=1.4)
    footer(fig, "mf")


def _style(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=12, length=0)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def compounding_sip(monthly, years, rate, out):
    value, invested, path = sip_fv(monthly, rate, years)
    half_year = next(i + 1 for i, (_, v) in enumerate(path) if v >= value / 2)
    fig = _card_frame("Power of compounding", f"₹{monthly:,}/month for {years} years",
                      f"Monthly SIP · assumed {rate * 100:.0f}% a year · illustration")
    fig.text(0.06, 0.735, inr(value), color=GOLD, fontsize=58, weight="heavy", va="center")
    fig.text(0.06, 0.68, f"from {inr(invested)} invested", color=TEXT, fontsize=20, va="center")
    ax = fig.add_axes([0.08, 0.34, 0.86, 0.30])
    _style(ax)
    xs = range(1, years + 1)
    inv = [p[0] / 1e5 for p in path]
    gain = [(p[1] - p[0]) / 1e5 for p in path]
    ax.bar(xs, inv, color="#2A3654", width=0.75, label="Invested")
    ax.bar(xs, gain, bottom=inv, color=ACCENT, width=0.75, label="Growth")
    ax.set_xlabel("Year", color=MUTED, fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"₹{v:,.0f}L" if v < 100 else f"₹{v / 100:.1f}Cr"))
    ax.legend(loc="upper left", frameon=False, labelcolor=MUTED, fontsize=12)
    ax.axvline(half_year - 0.5, color=GOLD, lw=1.2, ls="--")
    ax.text(half_year - 0.3, ax.get_ylim()[1] * 0.92,
            f"Half the final value comes\nin the last {years - half_year + 1} years", color=GOLD, fontsize=12)
    _tiles(fig, [("Invested", inr(invested), TEXT), ("Growth", inr(value - invested), ACCENT),
                 ("Multiple", f"{value / invested:.1f}x", GOLD)])
    _note_and_footer(fig, rate)
    save(fig, out)
    return {"type": "sip", "monthly": monthly, "years": years, "rate": rate, "value": value,
            "invested": invested, "last_years": years - half_year + 1}


def compounding_early(monthly, rate, out, ages=(25, 35), until=60):
    res = [(a, *sip_fv(monthly, rate, until - a)[:2]) for a in ages]
    fig = _card_frame("Power of compounding", "Start early. It's worth it.",
                      f"₹{monthly:,}/month until age {until} · assumed {rate * 100:.0f}% a year · illustration")
    ax = fig.add_axes([0.10, 0.36, 0.84, 0.40])
    _style(ax)
    labels = [f"Start at {a}" for a, _, _ in res]
    vals = [v / 1e7 for _, v, _ in res]
    invs = [i / 1e7 for _, _, i in res]
    ax.bar(labels, invs, color="#2A3654", width=0.5, label="Invested")
    ax.bar(labels, [v - i for v, i in zip(vals, invs)], bottom=invs, color=[ACCENT, MUTED], width=0.5, label="Growth")
    for x, v in enumerate(vals):
        ax.text(x, v * 1.02, inr(v * 1e7), color=GOLD if x == 0 else TEXT, fontsize=22, weight="bold", ha="center")
    ax.set_ylim(0, max(vals) * 1.18)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"₹{v:.0f}Cr"))
    ax.tick_params(axis="x", labelsize=16, labelcolor=TEXT)
    (a1, v1, i1), (a2, v2, i2) = res
    _tiles(fig, [(f"Extra invested from {a1}", inr(i1 - i2), TEXT),
                 ("Extra wealth", inr(v1 - v2), ACCENT), ("Difference", f"{v1 / v2:.1f}x", GOLD)])
    _note_and_footer(fig, rate)
    save(fig, out)
    return {"type": "early", "monthly": monthly, "rate": rate, "ages": ages, "until": until,
            "values": [(a, v, i) for a, v, i in res]}


def compounding_stepup(monthly, years, rate, out, step=0.10):
    flat, flat_inv, flat_path = sip_fv(monthly, rate, years)
    up, up_inv, up_path = sip_fv(monthly, rate, years, step)
    fig = _card_frame("Power of compounding", "Step-up SIP vs flat SIP",
                      f"Start ₹{monthly:,}/month · {years} years · +{step * 100:.0f}% every year · assumed "
                      f"{rate * 100:.0f}% · illustration")
    ax = fig.add_axes([0.10, 0.36, 0.84, 0.40])
    _style(ax)
    xs = range(1, years + 1)
    ax.plot(xs, [p[1] / 1e5 for p in up_path], color=ACCENT, lw=3.5, label=f"Step-up {step * 100:.0f}%/yr")
    ax.plot(xs, [p[1] / 1e5 for p in flat_path], color=MUTED, lw=3, label="Flat SIP")
    ax.fill_between(xs, [p[1] / 1e5 for p in flat_path], [p[1] / 1e5 for p in up_path], color=ACCENT, alpha=0.12)
    ax.text(years, up / 1e5, f"  {inr(up)}", color=ACCENT, fontsize=17, weight="bold", va="center")
    ax.text(years, flat / 1e5, f"  {inr(flat)}", color=TEXT, fontsize=15, va="center")
    ax.set_xlim(1, years * 1.22)
    ax.set_xlabel("Year", color=MUTED, fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"₹{v:,.0f}L" if v < 100 else f"₹{v / 100:.1f}Cr"))
    ax.legend(loc="upper left", frameon=False, labelcolor=MUTED, fontsize=13)
    _tiles(fig, [("Flat SIP", inr(flat), TEXT), ("Step-up SIP", inr(up), ACCENT),
                 ("Extra wealth", inr(up - flat), GOLD)])
    _note_and_footer(fig, rate)
    save(fig, out)
    return {"type": "stepup", "monthly": monthly, "years": years, "rate": rate, "step": step,
            "flat": flat, "flat_inv": flat_inv, "up": up, "up_inv": up_inv}


def compounding_lumpsum(amount, rate, out, horizons=(10, 20, 30)):
    vals = [(y, amount * (1 + rate) ** y) for y in horizons]
    fig = _card_frame("Power of compounding", f"{inr(amount)} invested once",
                      f"One-time investment · assumed {rate * 100:.0f}% a year · illustration")
    ax = fig.add_axes([0.10, 0.36, 0.84, 0.40])
    _style(ax)
    ax.bar([f"{y} years" for y, _ in vals], [v / 1e5 for _, v in vals], color=[GRID, "#2A3654", ACCENT], width=0.55)
    for x, (_, v) in enumerate(vals):
        ax.text(x, v / 1e5 * 1.02, inr(v), color=GOLD if x == 2 else TEXT, fontsize=21, weight="bold", ha="center")
    ax.set_ylim(0, vals[-1][1] / 1e5 * 1.18)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"₹{v:,.0f}L" if v < 100 else f"₹{v / 100:.1f}Cr"))
    ax.tick_params(axis="x", labelsize=16, labelcolor=TEXT)
    double = 72 / (rate * 100)
    _tiles(fig, [("Doubles roughly every", f"{double:.0f} years", TEXT),
                 (f"After {horizons[-1]} years", f"{vals[-1][1] / amount:.0f}x", ACCENT),
                 ("Rule of 72", f"72 ÷ {rate * 100:.0f} ≈ {double:.0f}", GOLD)])
    _note_and_footer(fig, rate)
    save(fig, out)
    return {"type": "lump", "amount": amount, "rate": rate, "values": vals, "double": double}


# ---------------------------------------------------------------- shareable formats
def myth_card(item, out):
    """Myth vs Fact card, written to be forwarded."""
    fig = canvas()
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.885, "MYTH VS FACT", color=ACCENT, fontsize=15, weight="semibold")
    for y0, h, label, col, text, size in ((0.52, 0.31, "MYTH", "#FF5C6C", item["myth"], 34),
                                          (0.19, 0.30, "FACT", "#2ECC8F", item["fact"], 27)):
        fig.add_artist(FancyBboxPatch((0.06, y0), 0.88, h, boxstyle="round,pad=0,rounding_size=0.02",
                                      transform=fig.transFigure, fc=PANEL, ec=col, lw=2))
        fig.text(0.10, y0 + h - 0.045, label, color=col, fontsize=20, weight="heavy", va="center")
        fig.text(0.10, y0 + (h - 0.07) / 2, wrap(text, 30 if size > 30 else 38), color=TEXT, fontsize=size,
                 weight="bold" if label == "MYTH" else "regular", va="center", linespacing=1.3)
    fig.text(0.5, 0.135, f"Send this to {item['send']}", color=GOLD, fontsize=19, weight="bold", ha="center")
    footer(fig, "mf")
    return save(fig, out)


def lakh_card(series, years, out):
    """What ₹1 lakh invested N years ago in each index is worth today (price indices)."""
    rows = []
    for label, pts in series:
        end_d, end = pts[-1]
        target = end_d.replace(year=end_d.year - years)
        prior = [v for d_, v in pts if d_ <= target]
        if prior and (target - pts[0][0]).days >= 0:
            rows.append((label, 1e5 * end / prior[-1], ((end / prior[-1]) ** (1 / years) - 1) * 100))
    rows.sort(key=lambda r: r[1])
    asof = series[0][1][-1][0]
    fig = _card_frame("Then vs now", f"₹1 lakh invested {years} years ago",
                      f"Value today in Nifty indices · price returns, dividends excluded · as of {asof:%d %b %Y}")
    ax = fig.add_axes([0.27, 0.20, 0.67, 0.56])
    _style(ax)
    ax.grid(False)
    bars = ax.barh([r[0] for r in rows], [r[1] / 1e5 for r in rows], color=[ACCENT if i == len(rows) - 1 else "#2A3654"
                                                                         for i in range(len(rows))], height=0.62)
    for b, r in zip(bars, rows):
        ax.text(b.get_width(), b.get_y() + b.get_height() / 2, f"  {inr(r[1])}  ({r[2]:.1f}%/yr)", va="center",
                color=TEXT, fontsize=13.5, weight="bold")
    ax.set_xticks([])
    ax.tick_params(axis="y", colors=TEXT, labelsize=14, length=0)
    ax.set_xlim(0, max(r[1] for r in rows) / 1e5 * 1.6)
    fig.text(0.5, 0.165, "Indices cannot be bought directly; index funds and ETFs have costs and tracking differences.\n"
             "Past performance may or may not be sustained in future.", color=MUTED, fontsize=10.5, ha="center",
             va="center", linespacing=1.4)
    footer(fig, "mf")
    save(fig, out)
    return {"years": years, "asof": asof, "rows": rows[::-1]}


def news_card(headline, points, out, kicker="MARKET NEWS"):
    """Same-day reaction card: headline + up to 4 short points."""
    import datetime as _dt
    fig = canvas()
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.885, f"{kicker} · {_dt.datetime.now(_dt.timezone(_dt.timedelta(hours=5, minutes=30))):%d %b %Y}".upper(),
             color=ACCENT, fontsize=15, weight="semibold")
    head = wrap(headline, 22)
    fig.text(0.06, 0.74, head, color=TEXT, fontsize=46 if len(head.splitlines()) <= 3 else 38, weight="heavy",
             va="center", linespacing=1.15)
    y = 0.56
    for p in points[:4]:
        t = wrap(p, 40)
        fig.text(0.06, y, "→", color=GOLD, fontsize=24, weight="bold", va="top")
        fig.text(0.115, y, t, color=TEXT, fontsize=24, va="top", linespacing=1.35)
        y -= 0.045 * len(t.splitlines()) + 0.03
    footer(fig, "generic")
    return save(fig, out)


def partner_chart_card(image_path, title, partner, out):
    """A partner's chart, shown whole and unedited, with credit to the creator."""
    from PIL import Image
    import numpy as np
    fig = canvas()
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.895, "CHART OF THE DAY", color=ACCENT, fontsize=15, weight="semibold")
    fig.text(0.06, 0.845, wrap(title, 34), color=TEXT, fontsize=30, weight="heavy", va="center", linespacing=1.15)
    im = Image.open(image_path).convert("RGB")
    bw, bh = 0.88, 0.58                                   # box, in figure fractions (canvas is 1080 x 1350)
    ar_box, ar = (bw * 1080) / (bh * 1350), im.width / im.height
    w, h = (bw, bw * 1080 / ar / 1350) if ar >= ar_box else (bh * 1350 * ar / 1080, bh)
    ax = fig.add_axes([0.06 + (bw - w) / 2, 0.19 + (bh - h) / 2, w, h])
    ax.imshow(np.asarray(im))
    ax.axis("off")
    fig.text(0.5, 0.15, f"Chart by {partner['name']} · {partner['handle']} on X", color=GOLD, fontsize=19,
             weight="bold", ha="center")
    fig.text(0.5, 0.118, "Shared with the creator's permission", color=MUTED, fontsize=13, ha="center")
    footer(fig, "generic")
    return save(fig, out)
