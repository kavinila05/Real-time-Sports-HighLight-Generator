from fastapi import APIRouter
from services.progress_service import get_progress

router = APIRouter(
    prefix="/progress",
    tags=["Progress"]
)


@router.get("/{video_id}")
def fetch_progress(video_id: str):

    return get_progress(video_id)
