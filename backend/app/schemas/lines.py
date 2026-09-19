from pydantic import BaseModel, Field


class LineBandUpdate(BaseModel):
    color: str | None = None
    name: str | None = Field(default=None, max_length=32)


class StationLinesUpdate(BaseModel):
    line_codes: list[str]
