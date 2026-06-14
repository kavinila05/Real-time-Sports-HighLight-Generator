import cv2
import os
from moviepy import VideoFileClip


def extract_video_metadata(video_path):

    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_count = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    duration = (
        frame_count / fps
        if fps > 0
        else 0
    )

    cap.release()

    return {
        "fps": float(round(fps, 2)),
        "frame_count": int(frame_count),
        "resolution": f"{width}x{height}",
        "duration_seconds": float(
            round(duration, 2)
        )
    }


def extract_sample_frames(
    video_path,
    output_folder="temp_frames",
    num_frames=5
):

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    cap = cv2.VideoCapture(
        video_path
    )

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    frame_indices = [

        int(i * total_frames
        / num_frames)

        for i in range(num_frames)
    ]

    saved_frames = []

    for index in frame_indices:

        cap.set(
            cv2.CAP_PROP_POS_FRAMES,
            index
        )

        success, frame = cap.read()

        if success:

            frame_path = os.path.join(
                output_folder,
                f"frame_{index}.jpg"
            )

            cv2.imwrite(
                frame_path,
                frame
            )

            saved_frames.append(
                frame_path
            )

    cap.release()

    return saved_frames


def extract_audio_from_video(
    video_path,
    output_audio="temp_audio.wav"
):

    clip = VideoFileClip(
        video_path
    )

    if clip.audio is not None:

        clip.audio.write_audiofile(
            output_audio,
            logger=None
        )

        clip.close()

        return output_audio

    return None
