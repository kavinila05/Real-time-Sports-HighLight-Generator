"""
Summary Agent
-------------
Generates a natural-language match summary from the
pipeline output (ranked events, commentary, audio spikes
and video metadata) without requiring an external LLM.

The summary is built by template-filling based on detected
sport, event types and statistics — keeping the backend
fully self-contained.
"""


def generate_match_summary(
    sport,
    ranked_events,
    commentary_events,
    audio_spikes,
    metadata
):
    """
    Build a structured match summary from pipeline outputs.

    Parameters
    ----------
    sport : str
        Detected sport label.
    ranked_events : list[dict]
        Events after ranking (may be empty).
    commentary_events : list[str]
        Commentary keyword matches (e.g. ["wicket", "six"]).
    audio_spikes : list[dict]
        Crowd energy spikes from audio analysis.
    metadata : dict
        Video metadata: fps, frame_count, resolution,
        duration_seconds.

    Returns
    -------
    dict
        Summary containing headline, body, key_stats, and
        event_breakdown.
    """

    sport_clean = sport.lower().replace("a ", "").replace("an ", "").strip()

    duration_sec = float(
        metadata.get("duration_seconds", 0)
    )
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration_str = f"{minutes}m {seconds}s"

    total_events = len(ranked_events)
    highlight_events = [
        e for e in ranked_events
        if e.get("highlight", False)
    ]
    total_highlights = len(highlight_events)
    total_spikes = len(audio_spikes)
    commentary_count = len(commentary_events)

    # -----------------------------------------------
    # Top event
    # -----------------------------------------------

    top_event = None
    if highlight_events:
        top_event = max(
            highlight_events,
            key=lambda x: x.get("confidence", 0)
        )

    # -----------------------------------------------
    # Headline
    # -----------------------------------------------

    if total_highlights == 0:
        headline = (
            f"Analysis complete — "
            f"no highlight-level events detected in this "
            f"{sport_clean} video."
        )
    elif total_highlights == 1:
        headline = (
            f"1 key highlight found in "
            f"{duration_str} of {sport_clean} action."
        )
    else:
        headline = (
            f"{total_highlights} key highlights detected "
            f"across {duration_str} of {sport_clean} action."
        )

    # -----------------------------------------------
    # Body paragraph
    # -----------------------------------------------

    body_parts = []

    body_parts.append(
        f"The multi-modal pipeline analyzed the video "
        f"({duration_str}) using vision, audio and commentary agents."
    )

    if commentary_count > 0:
        events_str = ", ".join(commentary_events)
        body_parts.append(
            f"The commentary agent transcribed and matched "
            f"{commentary_count} event keyword(s): {events_str}."
        )

    if total_spikes > 0:
        body_parts.append(
            f"The audio agent detected {total_spikes} crowd "
            f"energy spike(s) suggesting exciting moments."
        )

    if top_event:
        top_label = str(top_event.get("event", "key play"))
        top_conf = float(top_event.get("confidence", 0))
        top_ts = float(top_event.get("timestamp", 0))
        ts_min = int(top_ts // 60)
        ts_sec = int(top_ts % 60)
        body_parts.append(
            f"The top-ranked highlight is '{top_label}' "
            f"at {ts_min:02d}:{ts_sec:02d} "
            f"with {round(top_conf * 100)}% confidence."
        )

    body = " ".join(body_parts)

    # -----------------------------------------------
    # Event breakdown by type
    # (normalize sport-aware minor labels so the
    #  dashboard overview tiles are readable)
    # -----------------------------------------------

    MINOR_LABELS = {"minor_play", "possession", "open_play", "rally"}

    event_breakdown = {}
    for event in ranked_events:
        raw_label = str(event.get("event", "unknown"))
        # Group all minor/non-highlight plays under one bucket
        if raw_label in MINOR_LABELS:
            label = raw_label.replace("_", " ").title()
        else:
            # Clean CLIP-style labels: "a cricket wicket" → "Wicket"
            label = (
                raw_label
                .replace("_", " ")
                .replace("a cricket ", "")
                .replace("a football ", "")
                .replace("a basketball ", "")
                .replace("a badminton ", "")
                .replace("a ", "")
                .replace("an ", "")
                .strip()
                .title()
            )
        event_breakdown[label] = (
            event_breakdown.get(label, 0) + 1
        )

    # -----------------------------------------------
    # Key stats
    # -----------------------------------------------

    key_stats = {
        "duration":          duration_str,
        "total_events":      total_events,
        "highlights":        total_highlights,
        "audio_spikes":      total_spikes,
        "commentary_events": commentary_count,
        "resolution":        metadata.get("resolution", "N/A"),
        "fps":               metadata.get("fps", "N/A")
    }

    return {
        "headline":        headline,
        "body":            body,
        "key_stats":       key_stats,
        "event_breakdown": event_breakdown,
        "top_event":       top_event
    }
