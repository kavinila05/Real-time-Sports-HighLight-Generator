import os
import uuid


UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


analysis_results = {}


def save_uploaded_video(file):

    video_id = str(
        uuid.uuid4()
    )

    extension = (
        file.filename
        .split(".")[-1]
    )

    filename = (
        f"{video_id}.{extension}"
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    with open(
        file_path,
        "wb"
    ) as f:

        f.write(
            file.file.read()
        )

    return (
        video_id,
        file_path
    )


def save_analysis_result(
    video_id,
    result
):

    analysis_results[
        video_id
    ] = result


def get_analysis_result(
    video_id
):

    return analysis_results.get(
        video_id,
        {}
    )
