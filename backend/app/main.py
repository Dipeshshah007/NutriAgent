from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, SessionLocal, engine
from .routers import admin, auth, cart, catalog, chat, orders, planner, profile, tracker
from .seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title=f"{settings.app_name} API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for r in (auth, catalog, cart, orders, profile, tracker, planner, chat, admin):
    app.include_router(r.router)


@app.get("/api/config", tags=["meta"])
def public_config():
    """White-label settings consumed by the frontend."""
    return {"app_name": settings.app_name, "tagline": settings.app_tagline, "currency": settings.currency_symbol,
            "free_shipping_over": settings.free_shipping_over, "ai_provider": "gemini" if settings.gemini_api_key else "offline-coach"}


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok"}


# Optional single-server deployment: serve the built React app (frontend/dist) from FastAPI
_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.exists():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        f = _dist / full_path
        return FileResponse(f if f.is_file() else _dist / "index.html")
