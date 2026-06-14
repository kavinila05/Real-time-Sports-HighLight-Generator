from services.storage_service import (
    save_uploaded_video
)

from services.video_service import (
    extract_video_metadata,
    extract_sample_frames
)

from agents.sport_detection_agent import (
    detect_sport
)


def process_uploaded_video(file):

    video_id, path = (
        save_uploaded_video(file)
    )

    metadata = (
        extract_video_metadata(path)
    )

    frames = (
        extract_sample_frames(path)
    )

    sport = (
        detect_sport(frames)
    )

    return {

        "video_id":
            video_id,

        "file_path":
            path,

        "metadata":
            metadata,

        "sport":
            sport
    }
