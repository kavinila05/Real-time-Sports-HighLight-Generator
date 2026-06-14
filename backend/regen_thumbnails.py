"""
Utility script: regen_thumbnails.py
------------------------------------
Re-generates all thumbnails for the most recent analysis
result using the new Pillow-powered thumbnail_service.

Run from the backend/ folder (with venv active):
    python regen_thumbnails.py

This lets you preview the new thumbnail quality without
having to re-run the full analysis pipeline.
"""

import sys
import os

# Make sure we're in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from services.storage_service import analysis_results
from services.thumbnail_service import generate_thumbnail


def regen(report: dict):
    clips = report.get("highlight_clips", [])
    sport = report.get("sport", "Unknown")
    video_path = report.get("file_path") or report.get("metadata", {}).get("file_path")

    if not clips:
        print("No highlight clips in report.")
        return

    if not video_path or not os.path.exists(video_path):
        print(f"Video path not found: {video_path}")
        print("Clips stored:", [c.get("clip") for c in clips])
        return

    print(f"\nRegenerating {len(clips)} thumbnail(s) for sport='{sport}'\n")

    for i, clip in enumerate(clips, start=1):
        ts   = float(clip.get("timestamp", 0))
        ev   = clip.get("event", "")
        conf = float(clip.get("confidence", 0))
        rank = clip.get("rank") or i
        fname = f"thumb_{i}.jpg"

        print(f"  [{i}] timestamp={ts}s  event='{ev}'  conf={round(conf*100)}%  rank={rank}")

        path = generate_thumbnail(
            video_path=video_path,
            timestamp=ts,
            filename=fname,
            event_label=ev,
            sport=sport,
            rank=rank,
            confidence=conf,
        )

        if path:
            size_kb = round(os.path.getsize(path) / 1024)
            print(f"       ✓ Saved: {path}  ({size_kb} KB)")
        else:
            print(f"       ✗ Failed to generate thumbnail")

    print("\nDone. Refresh http://localhost:8000/dashboard to see updated thumbnails.")


if __name__ == "__main__":
    if not analysis_results:
        print("No analysis results in memory.")
        print("Run a full analysis first, then call this script in the same process.")
        print()
        print("Alternatively, pass a video file directly:")
        print("  python regen_thumbnails.py <video_path> <timestamp1,timestamp2,...>")
        print()

        # If called with args: regen_thumbnails.py video.mp4 5.2,12.4,30.1
        if len(sys.argv) >= 3:
            vpath      = sys.argv[1]
            timestamps = [float(t) for t in sys.argv[2].split(",")]
            sport      = sys.argv[3] if len(sys.argv) > 3 else "Unknown"
            events     = sys.argv[4].split(",") if len(sys.argv) > 4 else [""] * len(timestamps)

            print(f"Manual mode: video={vpath}  sport={sport}")
            for i, (ts, ev) in enumerate(zip(timestamps, events), start=1):
                path = generate_thumbnail(
                    video_path=vpath,
                    timestamp=ts,
                    filename=f"thumb_manual_{i}.jpg",
                    event_label=ev,
                    sport=sport,
                    rank=i,
                    confidence=0.85,
                )
                print(f"  [{i}] {path}")
        sys.exit(0)

    latest_id = list(analysis_results.keys())[-1]
    regen(analysis_results[latest_id])
