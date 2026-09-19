from pydantic import BaseModel


class LineColorUpdate(BaseModel):
    color: str


class StationLinesUpdate(BaseModel):
    lines: list[str]
