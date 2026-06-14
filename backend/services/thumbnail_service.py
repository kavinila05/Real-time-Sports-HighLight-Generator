"""
Thumbnail Service  (Pillow-powered)
------------------------------------
Generates a broadcast-quality highlight thumbnail:

  • 1280 × 720 HD frame extracted from the video
  • Contrast + sharpness enhancement pass
  • Full-width gradient footer with event title, timestamp,
    sport badge and confidence bar
  • Semi-transparent top ribbon with rank and sport emoji
  • Saved as JPEG at quality 95

Pillow is used for all drawing so text is fully anti-aliased
and the gradient/alpha compositing is clean and precise.
OpenCV is used only for the initial video seek + frame read
because it handles seeking more reliably than moviepy for
single-frame extraction.
"""

import os
import cv2
import numpy as np

from PIL import (
    Image,
    ImageDraw,
    ImageFilter,
    ImageEnhance,
)


# ── Output settings ──────────────────────────────────────────────────
THUMBNAIL_FOLDER = "thumbnails"
THUMB_W  = 1280
THUMB_H  = 720
JPEG_Q   = 95

os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

# ── Sport configuration ───────────────────────────────────────────────
_SPORT_CFG = {
    "cricket":    {"emoji": "🏏", "accent": (139, 92, 246)},   # purple
    "football":   {"emoji": "⚽", "accent": (34,  197, 94)},   # green
    "basketball": {"emoji": "🏀", "accent": (249, 115, 22)},   # orange
    "badminton":  {"emoji": "🏸", "accent": (56,  189, 248)},  # sky-blue
    "unknown":    {"emoji": "🏆", "accent": (139, 92, 246)},
}

def _sport_cfg(sport: str) -> dict:
    k = sport.lower()
    for key in _SPORT_CFG:
        if key in k:
            return _SPORT_CFG[key]
    return _SPORT_CFG["unknown"]


# ── Public API ────────────────────────────────────────────────────────

def generate_thumbnail(
    video_path: str,
    timestamp: float,
    filename: str,
    event_label: str = "",
    sport: str = "",
    rank: int = 0,
    confidence: float = 0.0,
) -> str | None:
    """
    Extract a frame at *timestamp*, enhance it and burn a rich
    overlay, then save to thumbnails/<filename>.

    Parameters
    ----------
    video_path  : path to source video
    timestamp   : seek time in seconds
    filename    : output file name (e.g. "thumb_1.jpg")
    event_label : detected event string
    sport       : clean sport name ("Cricket", "Basketball" …)
    rank        : highlight rank (1 = top)
    confidence  : 0-1 confidence score

    Returns
    -------
    Output path string, or None on failure.
    """
    try:
        # ── 1. Extract frame with OpenCV ──────────────────────────
        frame_bgr = _extract_frame(video_path, timestamp)
        if frame_bgr is None:
            return None

        # ── 2. Convert to Pillow RGB ──────────────────────────────
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb).resize(
            (THUMB_W, THUMB_H), Image.LANCZOS
        )

        # ── 3. Enhance: sharpen + slight contrast boost ───────────
        img = ImageEnhance.Sharpness(img).enhance(1.6)
        img = ImageEnhance.Contrast(img).enhance(1.12)
        img = ImageEnhance.Color(img).enhance(1.08)

        # ── 4. Draw overlays ──────────────────────────────────────
        img = _draw_top_ribbon(img, rank, sport)
        img = _draw_footer(img, event_label, sport, timestamp, confidence)

        # ── 5. Save ───────────────────────────────────────────────
        out_path = os.path.join(THUMBNAIL_FOLDER, filename)
        img.convert("RGB").save(out_path, "JPEG", quality=JPEG_Q, optimize=True)
        return out_path

    except Exception as exc:
        print(f"Thumbnail Error [{filename}]: {exc}")
        return None


# ── Frame extraction ─────────────────────────────────────────────────

def _extract_frame(video_path: str, timestamp: float):
    """Seek to timestamp and read one frame. Returns BGR ndarray or None."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Thumbnail: cannot open {video_path}")
        return None

    # Primary seek: millisecond-based
    cap.set(cv2.CAP_PROP_POS_MSEC, float(timestamp) * 1000.0)
    ok, frame = cap.read()

    # Fallback: try frame-number seek if ms seek gave nothing
    if not ok or frame is None:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        target_frame = int(float(timestamp) * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, target_frame))
        ok, frame = cap.read()

    cap.release()
    return frame if ok and frame is not None else None


# ── Top ribbon (rank + sport emoji) ─────────────────────────────────

def _draw_top_ribbon(img: Image.Image, rank: int, sport: str) -> Image.Image:
    """
    Semi-transparent dark ribbon across the top with:
      left  — rank pill  (#1, #2 …)
      right — sport emoji + name
    """
    cfg    = _sport_cfg(sport)
    accent = cfg["accent"]
    emoji  = cfg["emoji"]

    ribbon_h = 52
    overlay  = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw     = ImageDraw.Draw(overlay)

    # Gradient strip: dark at top, transparent at bottom
    for y in range(ribbon_h):
        alpha = int(180 * (1 - y / ribbon_h))
        draw.line([(0, y), (THUMB_W, y)], fill=(8, 12, 28, alpha))

    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw2 = ImageDraw.Draw(img)

    # Rank pill
    if rank > 0:
        pill_text = f"#{rank}"
        px, py    = 14, 10
        pill_w    = 9 * len(pill_text) + 18
        pill_h    = 28
        _rounded_rect(draw2, px, py, px + pill_w, py + pill_h,
                      radius=8, fill=(*accent, 220))
        draw2.text((px + 9, py + 4), pill_text,
                   fill=(255, 255, 255, 255),
                   font=_font(14, bold=True))

    # Sport name top-right
    sport_clean = sport.strip() or "Sport"
    sport_label = f"{emoji} {sport_clean}"
    sw = _text_width(draw2, sport_label, _font(13))
    draw2.text((THUMB_W - sw - 14, 13), sport_label,
               fill=(240, 240, 255, 220),
               font=_font(13))

    return img.convert("RGB")


# ── Footer gradient ──────────────────────────────────────────────────

def _draw_footer(
    img: Image.Image,
    event_label: str,
    sport: str,
    timestamp: float,
    confidence: float,
) -> Image.Image:
    """
    Gradient footer at the bottom:

      Row 1 (tall): large event title  |  timestamp badge
      Row 2 (slim): confidence bar with percentage
    """
    cfg    = _sport_cfg(sport)
    accent = cfg["accent"]
    ar, ag, ab = accent

    footer_h = 88      # total footer height
    bar_row  = 20      # confidence bar strip height

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    # Gradient: transparent → deep dark over footer_h pixels
    title_h = footer_h - bar_row
    for y in range(footer_h):
        rel   = y / footer_h
        alpha = int(210 * rel)
        draw.line(
            [(0, THUMB_H - footer_h + y), (THUMB_W, THUMB_H - footer_h + y)],
            fill=(6, 8, 20, alpha)
        )

    # ── Accent stripe above the confidence bar ───────────────────
    stripe_y = THUMB_H - bar_row - 2
    draw.line([(0, stripe_y), (THUMB_W, stripe_y)],
              fill=(ar, ag, ab, 120), width=1)

    # ── Confidence bar background ────────────────────────────────
    bar_bg_y = THUMB_H - bar_row
    draw.rectangle([(0, bar_bg_y), (THUMB_W, THUMB_H)],
                   fill=(14, 20, 40, 200))

    # Filled portion
    fill_w = int(THUMB_W * max(0.0, min(1.0, float(confidence))))
    if fill_w > 0:
        # Gradient fill: accent → pink
        for x in range(fill_w):
            t  = x / THUMB_W
            r  = int(ar + (236 - ar) * t)
            g  = int(ag + (72  - ag) * t)
            b  = int(ab + (153 - ab) * t)
            draw.line(
                [(x, bar_bg_y + 2), (x, THUMB_H - 3)],
                fill=(r, g, b, 200)
            )

    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw2 = ImageDraw.Draw(img)

    # ── Event title ──────────────────────────────────────────────
    label = _clean_label(event_label)
    title_y = THUMB_H - footer_h + 10
    # Shadow pass
    draw2.text((12, title_y + 2), label,
               fill=(0, 0, 0, 160), font=_font(26, bold=True))
    # Main text
    draw2.text((12, title_y), label,
               fill=(255, 255, 255, 255), font=_font(26, bold=True))

    # ── Timestamp badge ──────────────────────────────────────────
    secs = float(timestamp)
    ts   = f"{int(secs//60):02d}:{int(secs%60):02d}"

    badge_w, badge_h = 82, 30
    bx = THUMB_W - badge_w - 12
    by = title_y + 4
    _rounded_rect(draw2, bx, by, bx + badge_w, by + badge_h,
                  radius=8, fill=(ar, ag, ab, 200))
    ts_font = _font(15, bold=True)
    try:
        draw2.text((bx + badge_w // 2, by + badge_h // 2), ts,
                   fill=(255, 255, 255, 255),
                   font=ts_font,
                   anchor="mm")
    except Exception:
        # Fallback for bitmap fonts that don't support anchor
        draw2.text((bx + 10, by + 8), ts,
                   fill=(255, 255, 255, 255),
                   font=ts_font)

    # ── Confidence label inside bar ──────────────────────────────
    conf_pct  = f"{round(float(confidence) * 100)}%"
    conf_label = f"Confidence: {conf_pct}"
    cl_y = THUMB_H - bar_row + 3
    draw2.text((12, cl_y), conf_label,
               fill=(200, 200, 220, 220),
               font=_font(11))

    return img.convert("RGB")


# ── Drawing primitives ───────────────────────────────────────────────

def _rounded_rect(draw, x1, y1, x2, y2, radius, fill):
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)


def _text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _font(size: int, bold: bool = False):
    """
    Return a PIL font. Tries to load a system font that supports
    Unicode (for sport emojis). Falls back gracefully to the PIL
    default bitmap font if no system font is available.
    """
    from PIL import ImageFont
    import sys

    # Font candidates per platform
    candidates = []
    if sys.platform == "win32":
        base = r"C:\Windows\Fonts"
        if bold:
            candidates = [
                os.path.join(base, "arialbd.ttf"),
                os.path.join(base, "calibrib.ttf"),
                os.path.join(base, "segoeui.ttf"),
            ]
        else:
            candidates = [
                os.path.join(base, "arial.ttf"),
                os.path.join(base, "calibri.ttf"),
                os.path.join(base, "segoeui.ttf"),
            ]
    else:
        # Linux / macOS fallbacks
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    # Ultimate fallback
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _clean_label(raw: str) -> str:
    """Strip CLIP prompt prefixes and title-case the event name."""
    prefixes = [
        "a cricket ", "a football ", "a basketball ",
        "a badminton ", "players ", "football ",
        "basketball ", "badminton ", "cricket ",
    ]
    label = raw.replace("_", " ").strip()
    low   = label.lower()
    for p in prefixes:
        if low.startswith(p):
            label = label[len(p):]
            break
    return label.title() if label else "Highlight"
