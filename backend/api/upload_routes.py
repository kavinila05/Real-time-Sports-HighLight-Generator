from fastapi import (
    APIRouter,
    UploadFile,
    File
)

from agents.intake_agent import (
    process_uploaded_video
)

from services.storage_service import (
    save_analysis_result
)

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)


@router.post("/")
async def upload_video(

    file: UploadFile = File(...)

):

    result = (
        process_uploaded_video(file)
    )

    save_analysis_result(

        result["video_id"],

        result
    )

    return {

        "status":
            "uploaded",

        "video_id":
            result["video_id"],

        "sport":
            result["sport"],

        "metadata":
            result["metadata"]
    }
