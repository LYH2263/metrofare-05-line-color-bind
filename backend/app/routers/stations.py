from fastapi import APIRouter, HTTPException
from app.repositories.lines import ValidationError
from app.schemas.lines import StationLinesUpdate
from app.services.metro_service import MetroService

router = APIRouter(tags=["stations"])

@router.get("/stations")
def list_stations():
    with MetroService() as s:
        return {"items": s.stations()}

@router.get("/stations/{code}")
def get_station(code: str):
    with MetroService() as s:
        row = s.station(code)
        if not row:
            raise HTTPException(404)
        return row

@router.put("/stations/{code}/lines")
def put_station_lines(code: str, body: StationLinesUpdate):
    with MetroService() as s:
        try:
            row = s.update_station_lines(code, body.line_codes)
        except ValidationError as e:
            raise HTTPException(400, str(e))
        if row is None:
            raise HTTPException(404, f"站点不存在: {code}")
        return row
