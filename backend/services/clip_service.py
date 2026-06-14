import os
from moviepy import VideoFileClip


HIGHLIGHT_FOLDER = (
    "highlights"
)

os.makedirs(
    HIGHLIGHT_FOLDER,
    exist_ok=True
)


def generate_highlight_clip(

    video_path,
    timestamp,
    clip_name

):

    try:

        clip = VideoFileClip(
            video_path
        )

        start_time = max(
            0,
            timestamp - 5
        )

        end_time = min(

            clip.duration,

            timestamp + 8
        )

        output_path = os.path.join(

            HIGHLIGHT_FOLDER,

            clip_name
        )

        highlight = (
            clip.subclipped(
                start_time,
                end_time
            )
        )

        highlight.write_videofile(

            output_path,

            codec="libx264",

            audio_codec="aac",

            logger=None
        )

        clip.close()

        return output_path

    except Exception as e:

        print(
            "Clip Error:",
            str(e)
        )

        return None
