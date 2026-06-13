"""
Audio Agent — extracts and analyzes audio from the sports video.
Detects crowd excitement spikes and commentary cues to reinforce
event detection from the vision agent.

Dependencies (add to requirements.txt):
    librosa==0.10.2
    soundfile==0.13.1
"""

import os
import json
import numpy as np


def extract_audio(video_path: str, audio_output: str = "outputs/audio/audio.wav") -> str | None:
    """Extract audio track from video using moviepy."""
    try:
        from moviepy import VideoFileClip
        os.makedirs(os.path.dirname(audio_output), exist_ok=True)
        clip = VideoFileClip(video_path)
        if clip.audio is None:
            print("[AudioAgent] No audio track found in video.")
            return None
        clip.audio.write_audiofile(audio_output, logger=None)
        clip.close()
        print(f"[AudioAgent] Audio extracted to {audio_output}")
        return audio_output
    except Exception as e:
        print(f"[AudioAgent] Audio extraction failed: {e}")
        return None


def analyze_audio(
    audio_path: str,
    duration_sec: float,
    events_folder: str = "outputs/events"
) -> list:
    """
    Analyze audio for:
    - RMS energy spikes (crowd roar / high excitement moments)
    - Spectral centroid changes (pitch of commentary)
    Returns a list of audio events with timestamps.
    """
    try:
        import librosa
    except ImportError:
        print("[AudioAgent] librosa not installed. Skipping audio analysis.")
        print("[AudioAgent] Install with: pip install librosa soundfile")
        return []

    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
    except Exception as e:
        print(f"[AudioAgent] Could not load audio: {e}")
        return []

    # Compute RMS energy in 1-second windows
    hop_length = sr  # 1 second
    rms = librosa.feature.rms(y=y, frame_length=sr, hop_length=hop_length)[0]

    # Compute spectral centroid (brightness / pitch indicator)
    spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]

    # Normalize
    rms_norm = rms / (rms.max() + 1e-9)
    centroid_norm = spec_centroid / (spec_centroid.max() + 1e-9)

    # Excitement score = weighted combo of energy + brightness
    excitement = 0.7 * rms_norm + 0.3 * centroid_norm

    # Find excitement spikes (top 20% moments)
    threshold = np.percentile(excitement, 80)

    audio_events = []
    in_spike = False
    spike_start = 0

    for i, score in enumerate(excitement):
        t = i  # 1 second per frame
        if score >= threshold and not in_spike:
            in_spike = True
            spike_start = t
        elif score < threshold and in_spike:
            in_spike = False
            # Merge very short spikes
            if t - spike_start >= 1:
                audio_events.append({
                    "start_sec": spike_start,
                    "end_sec": t,
                    "peak_excitement": round(float(excitement[spike_start:t].max()), 4),
                    "avg_excitement": round(float(excitement[spike_start:t].mean()), 4),
                    "type": _classify_audio_excitement(
                        float(excitement[spike_start:t].max()),
                        float(centroid_norm[spike_start:t].mean())
                    )
                })

    # Handle ongoing spike at end
    if in_spike:
        t = len(excitement)
        audio_events.append({
            "start_sec": spike_start,
            "end_sec": min(t, int(duration_sec)),
            "peak_excitement": round(float(excitement[spike_start:].max()), 4),
            "avg_excitement": round(float(excitement[spike_start:].mean()), 4),
            "type": "crowd_noise"
        })

    os.makedirs(events_folder, exist_ok=True)
    with open(os.path.join(events_folder, "audio_events.json"), "w") as f:
        json.dump(audio_events, f, indent=2)

    print(f"[AudioAgent] Found {len(audio_events)} audio excitement spikes")
    return audio_events


def _classify_audio_excitement(peak: float, centroid: float) -> str:
    """Roughly classify the type of audio spike."""
    if peak > 0.85 and centroid > 0.6:
        return "crowd_roar"  # Very loud + high pitch = big moment
    elif peak > 0.7:
        return "crowd_cheer"
    elif centroid > 0.7:
        return "commentary_excitement"
    else:
        return "crowd_noise"


def merge_audio_with_visual_events(
    visual_events: list,
    audio_events: list,
    window_sec: float = 3.0
) -> list:
    """
    Boost confidence of visual events that coincide with audio excitement spikes.
    Returns enriched visual_events list.
    """
    for ve in visual_events:
        ts = ve["timestamp_sec"]
        audio_boost = False
        audio_type = None
        peak_excitement = 0.0

        for ae in audio_events:
            # Check if visual event timestamp falls within audio spike window
            if ae["start_sec"] - window_sec <= ts <= ae["end_sec"] + window_sec:
                audio_boost = True
                audio_type = ae["type"]
                peak_excitement = max(peak_excitement, ae["peak_excitement"])
                break

        ve["audio_boost"] = audio_boost
        ve["audio_type"] = audio_type
        ve["audio_excitement"] = round(peak_excitement, 4)

        # If audio says something exciting happened but vision didn't flag it,
        # upgrade the event to a potential highlight
        if audio_boost and not ve["is_highlight"] and peak_excitement > 0.75:
            ve["is_highlight"] = True
            if ve["event"] == "Normal Play":
                ve["event"] = "Crowd Reaction"

    return visual_events
