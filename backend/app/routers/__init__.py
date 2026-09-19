from fastapi import APIRouter

from app.routers import dashboard, edges, fares, history, lines, quote, settings, stations

api = APIRouter(prefix="/api")
for r in (dashboard, stations, edges, lines, fares, quote, history, settings):
    api.include_router(r.router)
