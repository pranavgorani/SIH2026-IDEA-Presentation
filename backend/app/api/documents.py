from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.models.database import get_db, Case, Document
from backend.app.core.config import settings

router = APIRouter(prefix="/documents", tags=["Document Media Storage"])

@router.get("/{case_id}/front", summary="Retrieve primary document front scan")
def get_front_document(case_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.case_id == case_id, Document.side == "FRONT").first()
    if not doc or not Path(doc.file_path).exists():
        raise HTTPException(status_code=404, detail="Document image not found.")
    return FileResponse(doc.file_path, media_type=doc.mime_type)

@router.get("/{case_id}/live", summary="Retrieve presented individual selfie portrait")
def get_live_document(case_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.case_id == case_id, Document.side == "LIVE_PERSON").first()
    if not doc or not Path(doc.file_path).exists():
        raise HTTPException(status_code=404, detail="Live portrait image not found.")
    return FileResponse(doc.file_path, media_type=doc.mime_type)

@router.get("/{case_id}/heatmap", summary="Retrieve forensic Error Level Analysis (ELA) heatmap")
def get_forensic_heatmap(case_id: str):
    heatmap_path = settings.STORAGE_DIR / case_id / "forensic_heatmap.png"
    if not heatmap_path.exists():
        raise HTTPException(status_code=404, detail="Forensic heatmap not yet rendered for this case.")
    return FileResponse(str(heatmap_path), media_type="image/png")
