import os


def cluster_audio_spikes(
    spikes,
    threshold=2
):
    """
    Group nearby audio spikes (within `threshold` seconds) into
    single excitement bursts and return their average timestamp.
    """

    if not spikes:
        return []

    clustered = []
    current_group = [spikes[0]]

    for i in range(1, len(spikes)):

        current_time = spikes[i]["timestamp"]
        previous_time = current_group[-1]["timestamp"]

        if current_time - previous_time <= threshold:
            current_group.append(spikes[i])
        else:
            avg_time = round(
                sum(s["timestamp"] for s in current_group)
                / len(current_group),
                2
            )
            clustered.append({
                "timestamp": float(avg_time),
                "strength": int(len(current_group))
            })
            current_group = [spikes[i]]

    # flush last group
    avg_time = round(
        sum(s["timestamp"] for s in current_group)
        / len(current_group),
        2
    )
    clustered.append({
        "timestamp": float(avg_time),
        "strength": int(len(current_group))
    })

    return clustered


# ----------------------------------
# Multimodal Fusion
# ----------------------------------

def fuse_multimodal_events(

    candidate_events,
    audio_spikes,
    commentary_events,
    fps,
    sport

):
    """
    Fuse vision events with audio spikes and commentary signals.

    Fixes applied vs original:
    - Frame timestamp is derived from the frame filename + fps
      (using os.path.basename for cross-platform safety).
    - Commentary matching no longer blindly assigns commentary_events[0]
      to every event. Instead we keep the vision-detected label and add a
      confidence boost when ANY commentary keyword was found. If a single
      commentary event exists it is only substituted for the FIRST (most
      prominent) candidate so the label isn't duplicated across all events.
    """

    clustered_audio = cluster_audio_spikes(audio_spikes)

    fused_events = []

    for idx, event in enumerate(candidate_events):

        # -----------------------------------------------
        # Timestamp from frame filename (platform-safe)
        # -----------------------------------------------

        frame_path = event.get("frame", "")

        try:
            basename = os.path.basename(frame_path)
            frame_number = int(
                os.path.splitext(basename)[0].split("_")[-1]
            )
            timestamp = round(frame_number / fps, 2)
        except (ValueError, IndexError):
            timestamp = event.get("timestamp", 0.0)

        # -----------------------------------------------
        # Base confidence from vision agent
        # -----------------------------------------------

        confidence = event.get("confidence", 0.5)
        matched_audio = False

        # -----------------------------------------------
        # Audio Matching — boost if crowd spike nearby
        # -----------------------------------------------

        for audio in clustered_audio:
            if abs(audio["timestamp"] - timestamp) <= 3:
                matched_audio = True
                confidence += 0.2
                break

        # -----------------------------------------------
        # Commentary Matching — boost if keywords found.
        # Only substitute the event label for the first
        # candidate (top-ranked by vision confidence) so
        # we don't stamp every event with the same label.
        # -----------------------------------------------

        predicted_event = event["event"]

        if commentary_events:
            confidence += 0.25
            # Only relabel the first/top candidate event
            if idx == 0:
                predicted_event = str(commentary_events[0])

        confidence = round(min(confidence, 1.0), 2)

        # -----------------------------------------------
        # Sport-specific confidence threshold
        # -----------------------------------------------

        thresholds = {
            "basketball": 0.65,
            "football":   0.75,
            "cricket":    0.85,
            "badminton":  0.70,
        }

        threshold = 0.8  # default
        for key, val in thresholds.items():
            if key in sport.lower():
                threshold = val
                break

        # -----------------------------------------------
        # Sport-aware minor event label
        # (replaces the generic "minor_play" string so
        #  the UI can display a sport-correct term)
        # -----------------------------------------------

        sport_lower = sport.lower()
        if "basketball" in sport_lower:
            minor_label = "possession"
        elif "football" in sport_lower:
            minor_label = "open_play"
        elif "badminton" in sport_lower:
            minor_label = "rally"
        else:
            # cricket default
            minor_label = "minor_play"

        # -----------------------------------------------
        # Highlight Decision
        # -----------------------------------------------

        if confidence >= threshold:
            fused_events.append({
                "event":       str(predicted_event),
                "timestamp":   float(timestamp),
                "confidence":  confidence,
                "audio_match": bool(matched_audio),
                "highlight":   True
            })
        else:
            fused_events.append({
                "event":       minor_label,
                "timestamp":   float(timestamp),
                "confidence":  confidence,
                "audio_match": bool(matched_audio),
                "highlight":   False
            })

    # -----------------------------------------------
    # De-duplicate events that share the same second
    # -----------------------------------------------

    final_events = []
    seen_times = set()

    for event in fused_events:
        rounded_time = round(event["timestamp"])
        if rounded_time not in seen_times:
            final_events.append(event)
            seen_times.add(rounded_time)

    return final_events
