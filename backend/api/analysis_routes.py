from fastapi import (
    APIRouter
)

from threading import Thread

from agents.pipeline_orchestrator import (
    run_pipeline
)

from services.storage_service import (
    get_analysis_result
)

router = APIRouter(
    prefix="/analyze",
    tags=["Analyze"]
)


@router.post("/{video_id}")
def analyze_video(
    video_id: str
):

    video_data = (
        get_analysis_result(
            video_id
        )
    )

    if not video_data:

        return {
            "error":
            "Video not found"
        }

    thread = Thread(

        target=run_pipeline,

        args=(

            video_id,

            video_data[
                "file_path"
            ],

            video_data[
                "sport"
            ],

            video_data[
                "metadata"
            ]
        )
    )

    thread.start()

    return {

        "status":
            "analysis_started",

        "video_id":
            video_id
    }
