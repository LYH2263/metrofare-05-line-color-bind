from fastapi import APIRouter

from app.routers import dashboard, edges, fares, history, lines, quote, settings, stations

api = APIRouter(prefix="/api")
for r in (dashboard, stations, edges, fares, lines, quote, history, settings):
    api.include_router(r.router)
