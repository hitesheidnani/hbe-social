"""HBE Capital visual identity: colours, fonts, logo, footer, saving."""
import os, textwrap
from pathlib import Path

ROOT = Path(__file__).parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplcache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

for f in (ROOT / "fonts").glob("*.ttf"):
    fm.fontManager.addfont(str(f))
plt.rcParams["font.family"] = "Inter"

BRAND = "HBE Capital"
HANDLE = "@hbecapital"
ARN = "ARN-275597"
MF_DISCLAIMER = ("Mutual fund investments are subject to market risks, "
                 "read all scheme related documents carefully.")
EDU = "For educational purposes only. Not investment advice."
GENERIC_DISCLAIMER = (f"{EDU} Not a recommendation to buy or sell. "
                      "Past performance does not guarantee future results.")

BG, PANEL, GRID = "#0B1220", "#121B2E", "#1E2A44"
TEXT, MUTED = "#E8EEF9", "#8A97B3"
ACCENT, GOLD = "#3DD9B3", "#F5B841"
UP, DOWN = "#2ECC8F", "#FF5C6C"

W, H = 1080, 1350          # Instagram portrait (4:5)
EXPORT_WIDTH = 1440        # Instagram's maximum; sharper than 1080


def canvas(w=W, h=H):
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    return fig


def brand_badge(fig, x, y, size=1.0):
    """'HBE' logo tile + 'HBE Capital' wordmark. (x, y) = left edge, vertical centre."""
    fw, fh = fig.get_size_inches() * 100
    bw, bh = 64 * size / fw, 64 * size / fh
    fig.add_artist(FancyBboxPatch((x, y - bh / 2), bw, bh, boxstyle=f"round,pad=0,rounding_size={0.18 * bw}",
                                  transform=fig.transFigure, fc=ACCENT, ec="none", zorder=5))
    fig.text(x + bw / 2, y, "HBE", color=BG, fontsize=15 * size, weight="heavy", ha="center", va="center", zorder=6)
    fig.text(x + bw + 16 * size / fw, y, BRAND, color=TEXT, fontsize=20 * size, weight="bold", va="center")


def footer(fig, kind="generic"):
    """kind: 'mf' (AMFI line + ARN), 'pms', or 'generic'."""
    brand_badge(fig, 0.05, 0.045, size=0.7)
    fig.text(0.95, 0.045, HANDLE, color=MUTED, fontsize=14, ha="right", va="center")
    note = {
        "mf": f"{MF_DISCLAIMER} {EDU} AMFI-registered MF Distributor · {ARN}",
        "pms": ("PMS investments are subject to market risks. Returns as reported to APMI, not verified by "
                f"HBE Capital. {EDU}"),
        "generic": GENERIC_DISCLAIMER,
    }[kind]
    fig.text(0.5, 0.012, note, color=MUTED, fontsize=7.5, ha="center", alpha=.85)


def save(fig, out):
    """Save as JPEG (the only format the Instagram API accepts) at 1440 px wide."""
    out = Path(out).with_suffix(".jpg")
    out.parent.mkdir(parents=True, exist_ok=True)
    dpi = EXPORT_WIDTH / fig.get_size_inches()[0]
    fig.savefig(out, dpi=dpi, facecolor=BG, pil_kwargs={"quality": 92, "optimize": True})
    plt.close(fig)
    print("wrote", out)
    return out


def quote_card(text, tag, out, author=None):
    fig = canvas()
    brand_badge(fig, 0.06, 0.955, size=0.85)
    fig.text(0.06, 0.885, tag.upper(), color=ACCENT, fontsize=15, weight="semibold")
    fig.text(0.06, 0.78, "“", color=GOLD, fontsize=150, weight="heavy", va="center")
    wrapped = textwrap.fill(text, width=24)
    n = len(wrapped.splitlines())
    if n > 6:
        wrapped = textwrap.fill(text, width=30)
        n = len(wrapped.splitlines())
    size = 60 if n <= 2 else (46 if n <= 5 else (38 if n <= 7 else 32))
    fig.text(0.07, 0.48, wrapped, color=TEXT, fontsize=size, weight="bold", va="center", linespacing=1.3)
    if author:
        fig.text(0.07, 0.2, f"— {author}", color=GOLD, fontsize=20, weight="semibold")
    fig.add_artist(plt.Line2D([0.07, 0.19], [0.16, 0.16], color=GOLD, lw=3, transform=fig.transFigure))
    footer(fig)
    return save(fig, out)


def story_version(card_path, label="NEW POST", footer_text="See the full post on our profile"):
    """Make a 1080x1920 Instagram Story image from a 4:5 card: card centred, brand background,
    short prompts above and below, all inside the Story safe zone."""
    from PIL import Image, ImageDraw, ImageFont
    card_path = Path(card_path)
    card = Image.open(card_path).convert("RGB").resize((1080, 1350), Image.LANCZOS)
    story = Image.new("RGB", (1080, 1920), BG)
    story.paste(card, (0, 285))
    d = ImageDraw.Draw(story)
    bold = ImageFont.truetype(str(ROOT / "fonts" / "Inter-Bold.ttf"), 40)
    reg = ImageFont.truetype(str(ROOT / "fonts" / "Inter-Medium.ttf"), 34)
    # (no heading above the card: the card already carries the HBE Capital logo)
    d.text((540, 1700), footer_text, font=reg, fill=MUTED, anchor="mm")
    out = card_path.with_name(card_path.stem + "_story.jpg")
    story.save(out, quality=92, optimize=True)
    return out


PERSON = "Hitesh Eidnani"
PERSON_TITLE = "Managing Partner, HBE Capital"


def _avatar(size=220):
    """Circular crop of assets/headshot.jpg (face-centred)."""
    from PIL import Image, ImageDraw
    import numpy as np
    im = Image.open(ROOT / "assets" / "headshot.jpg").convert("RGB")
    w, h = im.size
    side = int(min(w, h) * 0.62)
    cx, cy = int(w * 0.54), int(h * 0.27)                # face sits slightly right of centre, upper third
    box = (max(cx - side // 2, 0), max(cy - side // 2, 0))
    im = im.crop((box[0], box[1], box[0] + side, box[1] + side)).resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    rgba = im.convert("RGBA")
    rgba.putalpha(mask)
    return np.asarray(rgba)


def tweet_card(paragraphs, out):
    """Personal 'tweet-style' card: photo, name, title, ARN, then a short punchy message.
    The text is measured after layout and shrunk until it fits; the whole block is centred vertically."""
    def wrap_para(p, width):
        return "\n".join(textwrap.fill(line, width) for line in p.split("\n"))
    head_h, gap, bottom_limit = 0.15, 0.05, 0.13
    for size, width in ((40, 28), (36, 31), (32, 35), (29, 38), (26, 42)):
        fig = canvas()
        text = "\n\n".join(wrap_para(p, width) for p in paragraphs)
        t = fig.text(0.08, 0.5, text, color=TEXT, fontsize=size, va="top", linespacing=1.35)
        fig.canvas.draw()
        text_h = t.get_window_extent(fig.canvas.get_renderer()).height / fig.bbox.height
        group = head_h + gap + text_h
        if group <= 0.9 - bottom_limit:
            break
        plt.close(fig)
    top = min(0.9, 0.5 + group / 2 + 0.03)
    t.set_y(top - head_h - gap)
    ax = fig.add_axes([0.075, top - head_h, head_h * 1350 / 1080, head_h])
    ax.imshow(_avatar())
    ax.axis("off")
    fig.text(0.29, top - 0.04, PERSON, color=TEXT, fontsize=34, weight="heavy", va="center")
    fig.text(0.29, top - 0.085, PERSON_TITLE, color=MUTED, fontsize=19, va="center")
    fig.text(0.29, top - 0.118, f"AMFI-registered MF Distributor · {ARN}", color=MUTED, fontsize=15, va="center")
    footer(fig)
    return save(fig, out)
