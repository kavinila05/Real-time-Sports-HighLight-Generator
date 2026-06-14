"""
OCR Agent
---------
Reads scoreboard / overlay text from video frames using
OpenCV's built-in text detection (EAST) or a simple
contour-based approach so no extra Tesseract binary is needed.

For frames that contain clear on-screen score overlays the agent
attempts to extract structured score information. Results are
best-effort; the pipeline remains functional even if OCR finds
nothing.

Current implementation: lightweight contour-based brightness
region detection that flags frames likely to contain score
overlays (bright rectangular regions at common scoreboard
positions). Full text extraction requires `pytesseract` which
is an optional dependency.
"""

import cv2
import numpy as np


# --------------------------------------------------
# Scoreboard zone heuristics (top/bottom 15% of frame)
# --------------------------------------------------

SCOREBOARD_ROW_FRACTION = 0.15


def detect_scoreboard_regions(frame_bgr):
    """
    Heuristically detect regions that look like a scoreboard overlay.

    Returns a list of (x, y, w, h) rectangles in pixels that are
    likely score bar candidates based on brightness and position.

    Parameters
    ----------
    frame_bgr : np.ndarray
        BGR image array (as returned by cv2.imread).

    Returns
    -------
    list[tuple]
        List of (x, y, w, h) bounding boxes.
    """

    h, w = frame_bgr.shape[:2]

    # Only look at top and bottom strips where scoreboards live
    top_strip = frame_bgr[: int(h * SCOREBOARD_ROW_FRACTION), :]
    bottom_strip = frame_bgr[int(h * (1 - SCOREBOARD_ROW_FRACTION)):, :]

    regions = []

    for strip, y_offset in [
        (top_strip, 0),
        (bottom_strip, int(h * (1 - SCOREBOARD_ROW_FRACTION)))
    ]:
        gray = cv2.cvtColor(strip, cv2.COLOR_BGR2GRAY)

        # Threshold on bright pixels (scoreboards are usually light)
        _, thresh = cv2.threshold(
            gray, 200, 255, cv2.THRESH_BINARY
        )

        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for cnt in contours:
            x, y, rw, rh = cv2.boundingRect(cnt)
            # Ignore tiny contours
            if rw > w * 0.1 and rh > 10:
                regions.append((x, y + y_offset, rw, rh))

    return regions


def extract_frame_ocr_info(frame_path):
    """
    Run scoreboard detection on a single frame file.

    Parameters
    ----------
    frame_path : str
        Path to a JPEG / PNG frame extracted from the video.

    Returns
    -------
    dict
        {
          "frame": str,
          "scoreboard_detected": bool,
          "regions": list[dict],   # each has x,y,w,h
          "ocr_text": str          # empty unless pytesseract available
        }
    """

    result = {
        "frame":                frame_path,
        "scoreboard_detected":  False,
        "regions":              [],
        "ocr_text":             ""
    }

    try:

        frame_bgr = cv2.imread(frame_path)

        if frame_bgr is None:
            return result

        regions = detect_scoreboard_regions(frame_bgr)

        if regions:
            result["scoreboard_detected"] = True
            result["regions"] = [
                {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
                for x, y, w, h in regions
            ]

        # Optional: attempt pytesseract if installed
        try:
            import pytesseract  # noqa: F401 — optional dependency

            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray, config="--psm 6")
            result["ocr_text"] = text.strip()

        except ImportError:
            # pytesseract not installed — silently skip
            pass

    except Exception as e:
        print(f"OCR Agent Error on {frame_path}: {e}")

    return result


def analyze_frames_for_scores(frame_paths):
    """
    Run OCR detection across a list of frame paths.

    Parameters
    ----------
    frame_paths : list[str]

    Returns
    -------
    list[dict]
        One result dict per frame (from extract_frame_ocr_info).
    """

    results = []

    for path in frame_paths:
        info = extract_frame_ocr_info(path)
        results.append(info)

    return results
