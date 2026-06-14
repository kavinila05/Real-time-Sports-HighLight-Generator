from services.progress_service import (
    update_progress
)

from services.video_service import (
    extract_sample_frames,
    extract_audio_from_video
)

from services.storage_service import (
    save_analysis_result
)

from services.clip_service import (
    generate_highlight_clip
)

from services.thumbnail_service import (
    generate_thumbnail
)

from services.event_service import (
    process_events
)

from agents.vision_agent import (
    analyze_frames
)

from agents.audio_agent import (
    detect_audio_spikes
)

from agents.commentary_agent import (
    detect_commentary_events
)

from agents.fusion_agent import (
    fuse_multimodal_events
)

from agents.ranking_agent import (
    rank_highlights
)

from agents.highlight_agent import (
    select_highlights,
    build_highlight_manifest
)

from agents.summary_agent import (
    generate_match_summary
)

from agents.ocr_agent import (
    analyze_frames_for_scores
)


def run_pipeline(
    video_id,
    video_path,
    sport,
    metadata
):

    try:

        # ==================================
        # Stage 1 — Extract Frames
        # ==================================

        update_progress(
            video_id,
            "Extracting video frames",
            10
        )

        fps = float(metadata.get("fps", 30.0))

        frames = (
            extract_sample_frames(
                video_path,
                num_frames=10
            )
        )

        print(
            f"Frames extracted: "
            f"{len(frames)}"
        )

        # ==================================
        # Stage 1b — OCR Scoreboard Detection
        # ==================================

        ocr_results = (
            analyze_frames_for_scores(frames)
        )

        scoreboard_frames = [
            r for r in ocr_results
            if r.get("scoreboard_detected", False)
        ]

        print(
            f"Scoreboard frames detected: "
            f"{len(scoreboard_frames)}"
        )

        # ==================================
        # Stage 2 — Audio Analysis
        # ==================================

        update_progress(
            video_id,
            "Analyzing crowd audio",
            25
        )

        audio_path = (
            extract_audio_from_video(
                video_path
            )
        )

        audio_spikes = (
            detect_audio_spikes(
                audio_path
            )
        )

        print(
            f"Audio spikes: "
            f"{len(audio_spikes)}"
        )

        # ==================================
        # Stage 3 — Commentary Analysis
        # ==================================

        update_progress(
            video_id,
            "Analyzing commentary",
            40
        )

        commentary_events = (
            detect_commentary_events(
                audio_path,
                sport
            )
        )

        print(
            f"Commentary events: "
            f"{len(commentary_events)}"
        )

        # ==================================
        # Stage 4 — Vision Analysis
        # ==================================

        update_progress(
            video_id,
            "Running vision analysis",
            55
        )

        detections = (
            analyze_frames(
                frames,
                sport
            )
        )

        print(
            f"Vision detections: "
            f"{len(detections)}"
        )

        # ==================================
        # Stage 5 — Event Processing
        # ==================================

        update_progress(
            video_id,
            "Detecting match events",
            70
        )

        candidate_events = (
            process_events(
                sport,
                detections,
                fps=fps
            )
        )

        print(
            f"Candidate events: "
            f"{len(candidate_events)}"
        )

        # ==================================
        # Stage 6 — Multimodal Fusion
        # ==================================

        update_progress(
            video_id,
            "Running multimodal fusion",
            80
        )

        events = (
            fuse_multimodal_events(
                candidate_events,
                audio_spikes,
                commentary_events,
                fps,
                sport
            )
        )

        print(
            f"Fused events: "
            f"{len(events)}"
        )

        # ==================================
        # Stage 7 — Highlight Ranking
        # ==================================

        update_progress(
            video_id,
            "Ranking highlights",
            85
        )

        ranked_events = (
            rank_highlights(events)
        )

        # ==================================
        # Stage 7b — Highlight Selection
        # (smart filter via highlight_agent)
        # ==================================

        selected_highlights = (
            select_highlights(
                ranked_events,
                sport
            )
        )

        highlight_manifest = (
            build_highlight_manifest(
                selected_highlights,
                video_id,
                sport
            )
        )

        print(
            f"Selected highlights: "
            f"{len(selected_highlights)}"
        )

        # ==================================
        # Stage 8 — Highlight Generation
        # ==================================

        update_progress(
            video_id,
            "Generating highlight clips",
            90
        )

        generated_clips = []

        for clip_index, event in enumerate(
            selected_highlights, start=1
        ):
            timestamp = event.get("timestamp", 0)

            # Generate clip
            clip_path = (
                generate_highlight_clip(
                    video_path,
                    timestamp,
                    f"highlight_{clip_index}.mp4"
                )
            )

            # Generate thumbnail — pass full context so the
            # Pillow overlay includes rank, confidence, label + sport
            thumbnail_path = (
                generate_thumbnail(
                    video_path,
                    timestamp,
                    f"thumb_{clip_index}.jpg",
                    event_label=event.get("event", ""),
                    sport=sport,
                    rank=clip_index,
                    confidence=float(event.get("confidence", 0.0)),
                )
            )

            # Get caption from manifest if available
            manifest_clips = highlight_manifest.get("clips", [])
            caption = ""
            if clip_index - 1 < len(manifest_clips):
                caption = manifest_clips[clip_index - 1].get("caption", "")

            generated_clips.append({
                "event":      event.get("event", "unknown"),
                "timestamp":  timestamp,
                "confidence": event.get("confidence", 0),
                "rank":       event.get("rank", 0),
                "importance": event.get("importance", "secondary"),
                "caption":    caption,
                "clip":       clip_path,
                "thumbnail":  thumbnail_path
            })

        print(
            f"Generated clips: "
            f"{len(generated_clips)}"
        )

        # ==================================
        # Stage 9 — Top Moment
        # ==================================

        top_moment = None

        if selected_highlights:
            top_moment = selected_highlights[0]
        elif ranked_events:
            top_moment = max(
                ranked_events,
                key=lambda x: x.get("confidence", 0)
            )

        # ==================================
        # Stage 9b — Match Summary
        # ==================================

        match_summary = generate_match_summary(
            sport,
            ranked_events,
            commentary_events,
            audio_spikes,
            metadata
        )

        # ==================================
        # Stage 10 — Build Report
        # ==================================

        update_progress(
            video_id,
            "Building report",
            95
        )

        result = {
            "video_id":         str(video_id),
            "sport":            sport,
            "metadata":         metadata,
            "match_summary":    match_summary,
            "top_moment":       top_moment,
            "events":           ranked_events,
            "audio_spikes":     audio_spikes,
            "commentary_events": commentary_events,
            "highlight_clips":  generated_clips,
            "highlight_manifest": highlight_manifest,
            "ocr_results":      ocr_results,
            "event_count":      len(ranked_events)
        }

        save_analysis_result(video_id, result)

        # ==================================
        # Completed
        # ==================================

        update_progress(
            video_id,
            "Completed",
            100
        )

        print("Analysis completed successfully")

    except Exception as e:

        import traceback
        traceback.print_exc()

        print(
            "Pipeline Error:",
            str(e)
        )

        update_progress(
            video_id,
            f"Error: {str(e)}",
            0
        )
