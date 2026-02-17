from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db
from backend.models.user import User
from backend.schemas.export import ExportFormat, ExportRequest
from backend.services.export_service import (
    export_leaderboard_csv,
    export_leaderboard_pdf,
    export_leaderboard_xlsx,
)

router = APIRouter(prefix="/api/v1/export", tags=["export"])

MIME_TYPES = {
    ExportFormat.csv: "text/csv",
    ExportFormat.xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ExportFormat.pdf: "application/pdf",
}

EXTENSIONS = {
    ExportFormat.csv: "csv",
    ExportFormat.xlsx: "xlsx",
    ExportFormat.pdf: "pdf",
}


@router.post("/leaderboard/{jd_id}")
def export_leaderboard(
    jd_id: UUID,
    body: ExportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exporters = {
        ExportFormat.csv: export_leaderboard_csv,
        ExportFormat.xlsx: export_leaderboard_xlsx,
        ExportFormat.pdf: export_leaderboard_pdf,
    }

    exporter = exporters.get(body.format)
    if not exporter:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {body.format}")

    try:
        content = exporter(db, jd_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

    filename = f"leaderboard.{EXTENSIONS[body.format]}"
    return Response(
        content=content,
        media_type=MIME_TYPES[body.format],
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
