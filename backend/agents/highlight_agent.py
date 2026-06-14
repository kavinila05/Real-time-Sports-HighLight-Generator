"""
Highlight Agent
---------------
Selects the best highlight clips from ranked events and
produces a structured highlight reel manifest.

This agent is called after ranking_agent to apply
additional filtering rules — e.g. maximum highlights cap,
minimum gap between consecutive highlights, and a
sport-specific importance filter.
"""


def select_highlights(
    ranked_events,
    sport,
    max_highlights=5,
    min_gap_seconds=10
):
    """
    Filter ranked events down to the best highlights for the reel.

    Parameters
    ----------
    ranked_events : list[dict]
        Output from ranking_agent.rank_highlights — sorted by score.
    sport : str
        Detected sport name (used for sport-specific cap).
    max_highlights : int
        Hard cap on total number of highlight clips to generate.
    min_gap_seconds : float
        Minimum time gap between two selected highlights so they
        don't overlap after the ±5–8 s clip window is applied.

    Returns
    -------
    list[dict]
        Filtered list of highlight events ready for clip generation.
    """

    sport = sport.lower()

    # Sport-specific caps
    sport_caps = {
        "cricket":    6,
        "football":   5,
        "basketball": 7,
        "badminton":  5,
    }

    cap = sport_caps.get(
        next((k for k in sport_caps if k in sport), None),
        max_highlights
    )

    selected = []
    last_timestamp = -999.0

    for event in ranked_events:

        if not event.get("highlight", False):
            continue

        timestamp = float(event.get("timestamp", 0))
        confidence = float(event.get("confidence", 0))

        # Skip if too close to the previous selected clip
        if timestamp - last_timestamp < min_gap_seconds:
            continue

        # Skip very low confidence events even if flagged as highlight
        if confidence < 0.5:
            continue

        selected.append(event)
        last_timestamp = timestamp

        if len(selected) >= cap:
            break

    return selected


def build_highlight_manifest(
    selected_events,
    video_id,
    sport
):
    """
    Build the highlight reel manifest — a structured list of clip
    descriptors including captions and clip ordering.

    Parameters
    ----------
    selected_events : list[dict]
        Output from select_highlights.
    video_id : str
        Unique video identifier.
    sport : str
        Detected sport.

    Returns
    -------
    dict
        Manifest with reel metadata and ordered clip list.
    """

    clips = []

    for i, event in enumerate(selected_events, start=1):

        event_name = str(event.get("event", "key moment"))
        timestamp = float(event.get("timestamp", 0))
        confidence = float(event.get("confidence", 0))
        importance = str(event.get("importance", "secondary"))

        # Human-readable caption
        caption = _build_caption(
            event_name,
            timestamp,
            sport,
            i
        )

        clips.append({
            "index":      i,
            "event":      event_name,
            "timestamp":  timestamp,
            "confidence": confidence,
            "importance": importance,
            "caption":    caption,
            "clip_name":  f"highlight_{i}.mp4",
            "thumb_name": f"thumb_{i}.jpg"
        })

    manifest = {
        "video_id":       str(video_id),
        "sport":          str(sport),
        "total_clips":    len(clips),
        "reel_title":     f"{sport.title()} Highlight Reel",
        "clips":          clips
    }

    return manifest


# --------------------------------------------------
# Internal helpers
# --------------------------------------------------

def _build_caption(
    event_name,
    timestamp,
    sport,
    index
):
    """Generate a short human-readable caption for a highlight clip."""

    minutes = int(timestamp // 60)
    seconds = int(timestamp % 60)
    time_str = f"{minutes:02d}:{seconds:02d}"

    sport_emojis = {
        "cricket":    "🏏",
        "football":   "⚽",
        "basketball": "🏀",
        "badminton":  "🏸",
    }

    emoji = sport_emojis.get(
        next((k for k in sport_emojis if k in sport.lower()), None),
        "🏆"
    )

    clean_event = (
        event_name
        .replace("a ", "")
        .replace("an ", "")
        .title()
    )

    return f"{emoji} #{index} — {clean_event} @ {time_str}"
