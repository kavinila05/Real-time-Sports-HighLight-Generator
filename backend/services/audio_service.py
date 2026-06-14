"""
Audio Service
-------------
Thin service layer around audio_agent.detect_audio_spikes.

Provides helper utilities for:
- Computing overall crowd excitement score from a spike list.
- Formatting audio spike data for report serialisation.
- Extracting audio from video (delegates to video_service).
"""

from agents.audio_agent import detect_audio_spikes
from services.video_service import extract_audio_from_video


def get_audio_analysis(video_path):
    """
    Full audio analysis pipeline for a video file.

    Extracts the audio track, detects energy spikes and
    returns structured analysis results.

    Parameters
    ----------
    video_path : str
        Absolute path to the video file.

    Returns
    -------
    dict
        {
          "audio_path":        str | None,
          "spikes":            list[dict],
          "spike_count":       int,
          "excitement_score":  float   (0-1 normalised)
        }
    """

    audio_path = extract_audio_from_video(video_path)

    spikes = detect_audio_spikes(audio_path)

    excitement_score = compute_excitement_score(spikes)

    return {
        "audio_path":       audio_path,
        "spikes":           spikes,
        "spike_count":      len(spikes),
        "excitement_score": excitement_score
    }


def compute_excitement_score(spikes):
    """
    Derive a 0–1 excitement score from the list of audio spikes.

    A video with >= 10 spikes scores 1.0; 0 spikes scores 0.0.

    Parameters
    ----------
    spikes : list[dict]
        Audio spikes as returned by detect_audio_spikes.

    Returns
    -------
    float
    """

    if not spikes:
        return 0.0

    # Normalise against a reference of 10 spikes = full excitement
    score = min(len(spikes) / 10.0, 1.0)

    return round(score, 2)


def format_spikes_for_report(spikes):
    """
    Convert raw spike dicts to a clean report-friendly format.

    Parameters
    ----------
    spikes : list[dict]
        Raw spikes: [{"timestamp": float, "energy": float}, ...]

    Returns
    -------
    list[dict]
        Cleaned list with float-safe values.
    """

    formatted = []

    for spike in spikes:
        formatted.append({
            "timestamp": float(round(spike.get("timestamp", 0), 2)),
            "energy":    float(round(spike.get("energy", 0), 4))
        })

    return formatted
