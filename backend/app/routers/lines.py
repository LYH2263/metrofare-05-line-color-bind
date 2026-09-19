from fastapi import APIRouter, HTTPException

from app.repositories.lines import ValidationError
from app.schemas.lines import LineBandUpdate
from app.services.metro_service import MetroService

router = APIRouter(tags=["lines"])


@router.get("/lines")
def list_lines():
    with MetroService() as s:
        return {"items": s.lines()}


@router.patch("/lines/{code}")
def update_line(code: str, body: LineBandUpdate):
    if body.color is None and body.name is None:
        raise HTTPException(400, "需提供 color 或 name")
    with MetroService() as s:
        try:
            row = s.update_line_band(code, color=body.color, name=body.name)
        except ValidationError as e:
            raise HTTPException(400, str(e))
        if row is None:
            raise HTTPException(404, f"线路不存在: {code}")
        return row
