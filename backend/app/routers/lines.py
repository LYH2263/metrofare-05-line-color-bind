from fastapi import APIRouter, HTTPException
from app.schemas.lines import LineColorUpdate
from app.services.metro_service import MetroService, ValidationError

router = APIRouter(tags=["lines"])


@router.get("/lines")
def list_lines():
    with MetroService() as s:
        return {"items": s.lines()}


@router.put("/lines/{code}/color")
def update_line_color(code: str, body: LineColorUpdate):
    with MetroService() as s:
        try:
            row = s.update_line_color(code, body.color)
        except ValidationError as exc:
            raise HTTPException(422, str(exc))
        if not row:
            raise HTTPException(404, f"线路不存在: {code}")
        return row
