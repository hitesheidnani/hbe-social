"""Turn a ranked fund card (4:5 JPEG) into a ~14 s 9:16 countdown Reel (MP4, H.264 + AAC).

Rows are revealed from #10 up to #1, then the benchmark/summary, then a hold on the full card.
The disclaimer footer stays visible the whole time. Audio is a soft generated pad (no licensed music).
"""
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from brand import ROOT, BG, ACCENT, MUTED, HANDLE
from mf_posts import TOP, RH, GAP

W, H, CARD_Y, FPS = 1080, 1920, 285, 30
CARD_H = 1350
INTRO, STEP, FADE, OUTRO_FADE, HOLD = 1.2, 0.9, 0.3, 0.5, 3.5
SUMMARY_BOTTOM = 0.095          # figure fraction just above the 'Past performance' source line


TONE = "aevalsrc='0.05*sin(2*PI*220*t)+0.04*sin(2*PI*277.2*t)+0.035*sin(2*PI*329.6*t)':s=44100"


def audio_input(secs):
    """ffmpeg input + filter for the soundtrack: a track from music/ (rotating daily) or a soft generated tone."""
    import datetime as dt
    from brand import ROOT
    tracks = sorted((ROOT / "music").glob("*.mp3"))
    if tracks:
        t = tracks[dt.date.today().toordinal() % len(tracks)]
        return (["-stream_loop", "-1", "-t", f"{secs:.2f}", "-i", str(t)],
                f"[1:a]volume=0.8,afade=t=in:d=0.8,afade=t=out:st={secs - 1.5:.2f}:d=1.5[a]")
    return (["-f", "lavfi", "-t", f"{secs:.2f}", "-i", TONE],
            f"[1:a]tremolo=f=0.25:d=0.4,afade=t=in:d=1,afade=t=out:st={secs - 1.5:.2f}:d=1.5[a]")


def _px(frac):
    """Figure fraction (0 = bottom) -> pixel row on the 1080x1350 card."""
    return int(round((1 - frac) * CARD_H))


def _row_box(i):
    bottom = TOP - (i + 1) * RH - i * GAP
    return (0, _px(bottom + RH) - 4, W, _px(bottom) + 4)


def make_reel(card_jpg, rows, out_mp4, hook="WAIT FOR #1"):
    card = Image.open(card_jpg).convert("RGB").resize((W, CARD_H), Image.LANCZOS)
    blank = Image.new("RGB", (W, CARD_H), BG)
    row_boxes = [_row_box(i) for i in range(rows)]
    summary = (0, row_boxes[-1][3], W, _px(SUMMARY_BOTTOM))

    font = ImageFont.truetype(str(ROOT / "fonts" / "Inter-Bold.ttf"), 44)
    small = ImageFont.truetype(str(ROOT / "fonts" / "Inter-Medium.ttf"), 34)

    reveal_at = {i: INTRO + (rows - 1 - i) * STEP for i in range(rows)}   # #10 first, #1 last
    summary_at = INTRO + rows * STEP
    total = summary_at + OUTRO_FADE + HOLD

    def alpha(t, start, dur):
        return max(0.0, min(1.0, (t - start) / dur))

    ff = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
          "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
          *audio_input(total)[0], "-filter_complex", audio_input(total)[1],
          "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
          "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out_mp4)]
    proc = subprocess.Popen(ff, stdin=subprocess.PIPE)

    for f in range(int(total * FPS)):
        t = f / FPS
        frame = card.copy()
        for i, box in enumerate(row_boxes):             # hide rows not yet revealed, fade in the newest
            a = alpha(t, reveal_at[i], FADE)
            if a < 1:
                frame.paste(Image.blend(blank.crop(box), card.crop(box), a), box[:2])
        a = alpha(t, summary_at, OUTRO_FADE)
        if a < 1:
            frame.paste(Image.blend(blank.crop(summary), card.crop(summary), a), summary[:2])

        canvas = Image.new("RGB", (W, H), BG)
        canvas.paste(frame, (0, CARD_Y))
        d = ImageDraw.Draw(canvas)
        top_text = hook if t < summary_at else f"FOLLOW {HANDLE}"
        d.text((W // 2, 200), top_text, font=font, fill=ACCENT, anchor="mm")
        d.text((W // 2, 1700), "Full rankings: link in bio", font=small, fill=MUTED, anchor="mm")
        proc.stdin.write(canvas.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed to encode the Reel")
    return Path(out_mp4), total


if __name__ == "__main__":
    import sys
    print(make_reel(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10, sys.argv[3] if len(sys.argv) > 3 else "reel.mp4"))


def static_reel(card_jpg, out_mp4, secs=8.0):
    """A still card as a 9:16 Reel (card centred on the brand background, soft generated audio)."""
    from brand import story_version
    frame = story_version(card_jpg, footer_text="Follow @hbecapital for more")
    ff = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-loop", "1", "-t", f"{secs}", "-i", str(frame),
          *audio_input(secs)[0],
          "-filter_complex", "[0:v]scale=1080:1920,format=yuv420p[v];" + audio_input(secs)[1], "-map", "[v]", "-map", "[a]", "-r", "30", "-c:v", "libx264",
          "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
          str(out_mp4)]
    subprocess.run(ff, check=True)
    return Path(out_mp4), secs
