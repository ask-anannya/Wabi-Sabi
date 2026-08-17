from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import JSONResponse

from models.llm_response import ScanResponse
from models.user import User
from services import scan_store
from services.llm_datadog_metrics import llm_metrics
from services.llm_service import analyse_and_advise
from utils.exception_handler import ExceptionBase

router = APIRouter()


@router.post("/scan")
async def scan(
    image: UploadFile,
    user_id: str = Form(...),
    age: int | None = Form(None),
    skin_type: str | None = Form(None),
    concerns: str | None = Form(None),
) -> ScanResponse:
    profile = User(
        age=age,
        skin_type=skin_type,
        concerns=[c.strip() for c in concerns.split(",") if c.strip()] if concerns else None,
    )
    image_bytes = await image.read()
    try:
        return await analyse_and_advise(image_bytes, profile, user_id)
    except ValueError as e:
        # Bad/under-spec image — user-fixable, not a server error.
        print(f"[scan] 400: {e}")
        raise ExceptionBase(status_code=400, message=str(e))
    except (TimeoutError, RuntimeError) as e:
        print(f"[scan] 502: {e}")
        llm_metrics.log_scan_event("youcam.task.failures")
        raise ExceptionBase(
            status_code=502,
            message="I couldn't get a reading this time — please try again in a moment.",
        ) from e


@router.get("/scan/history")
async def scan_history(user_id: str, limit: int = 10):
    records = scan_store.get_scan_history(user_id, limit)
    return {
        "result": [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "metrics": r.metrics_json,
                "trust_score": r.trust_score,
                "advice": r.advice_json,
            }
            for r in records
        ]
    }


@router.delete("/scan/history/{scan_id}")
async def delete_scan(scan_id: int, user_id: str):
    deleted = scan_store.delete_scan(scan_id, user_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"message": "Scan not found."})
    return {"result": "deleted"}
