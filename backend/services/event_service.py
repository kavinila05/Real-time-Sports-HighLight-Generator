import os


def process_events(
    sport,
    detections,
    fps=30.0
):
    """
    Convert CLIP vision detections into structured events.

    Uses actual frame numbers extracted from frame filenames
    and the video FPS to compute accurate timestamps — instead
    of the old hardcoded i*6.2 multiplier.
    """

    events = []

    sport = sport.lower()

    for detection in detections:

        event = detection.get(
            "event",
            "unknown"
        )

        confidence = detection.get(
            "confidence",
            0.5
        )

        frame_path = detection.get(
            "frame",
            ""
        )

        # -----------------------------------------------
        # Derive timestamp from frame filename
        # e.g.  "temp_frames/frame_450.jpg"  → 450 / fps
        # Falls back to 0 if parsing fails.
        # -----------------------------------------------

        try:

            basename = os.path.basename(
                frame_path
            )

            # strip extension, split on "_", take last part

            frame_number = int(
                os.path.splitext(basename)[0]
                .split("_")[-1]
            )

            timestamp = round(
                frame_number / fps,
                2
            )

        except (ValueError, IndexError):

            timestamp = 0.0

        # -----------------------------------------------
        # Filter out normal play frames — not highlights
        # -----------------------------------------------

        if "normal" in event.lower():
            continue

        # -----------------------------------------------
        # Importance scoring
        # -----------------------------------------------

        importance = 0.5

        high_importance_keywords = [
            "goal",
            "slam dunk",
            "wicket",
            "six",
            "smash",
            "winning point",
            "boundary",
            "celebrating",
            "celebration",
            "maximum",
            "six"
        ]

        medium_importance_keywords = [
            "save",
            "rally",
            "penalty",
            "3 pointer",
            "scoring",
            "free throw",
            "match point"
        ]

        if any(
            kw in event.lower()
            for kw in high_importance_keywords
        ):
            importance = 0.9

        elif any(
            kw in event.lower()
            for kw in medium_importance_keywords
        ):
            importance = 0.75

        events.append({
            "event": event,
            "timestamp": float(timestamp),
            "confidence": float(confidence),
            "importance": float(importance),
            "frame": frame_path
        })

    return events
