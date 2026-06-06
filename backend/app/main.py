"""ScriptForge Backend Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import annotations, chapters, characters, conversion, export, projects, providers, story_bibles, versions

app = FastAPI(
    title="ScriptForge API",
    description="AI-powered novel-to-script conversion",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(providers.router)
app.include_router(projects.router)
app.include_router(chapters.router)
app.include_router(characters.router)
app.include_router(annotations.router)
app.include_router(versions.router)
app.include_router(export.router)
app.include_router(conversion.router)
app.include_router(story_bibles.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
