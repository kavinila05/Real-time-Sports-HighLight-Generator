from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.storage_service import get_analysis_result

router = APIRouter(
    prefix="/report",
    tags=["Report"]
)


@router.get("/latest")
def get_latest_report():
    """
    Return the most recently stored report.
    Useful when the dashboard loads without a video_id.
    """
    from services.storage_service import analysis_results

    if not analysis_results:
        raise HTTPException(status_code=404, detail="No reports available yet.")

    # Return the last stored result
    latest_id = list(analysis_results.keys())[-1]
    return analysis_results[latest_id]


@router.get("/{video_id}")
def get_report(video_id: str):
    report = get_analysis_result(video_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report not found for video_id: {video_id}")
    return JSONResponse(content=report)
