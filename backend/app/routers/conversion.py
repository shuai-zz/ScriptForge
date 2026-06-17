"""Conversion pipeline endpoints: SSE streaming progress."""

import json
import logging
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig
from sqlalchemy import select

from app.core.encryption import decrypt
from app.database import async_session_factory
from app.models.chapter import Chapter
from app.models.conversion import ConversionRun, LLMProvider
from app.models.project import Project
from app.models.story_bible import StoryBible
from app.pipeline.graph import build_conversion_graph
from app.pipeline.state import ConversionState
from app.schemas.script import ScriptV1
from app.services.character_service import (
    CharacterRelationshipService,
    CharacterService,
)
from app.services.script_persistence_service import ScriptPersistenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/convert", tags=["conversion"])


@router.get("/stream")
async def convert_stream(project_id: uuid.UUID) -> StreamingResponse:
    """Start a conversion run and stream progress via SSE.

    Each event is a JSON object:
    ```json
    {"current_stage": "...", "percent": 0-100, "message": "...", "details": {}}
    ```
    """

    async def event_generator():
        async with async_session_factory() as db:
            try:
                project, chapters, providers, provider_assignments = (
                    await _load_project_providers(db, project_id)
                )
            except HTTPException as exc:
                yield _sse_event(
                    {
                        "current_stage": "error",
                        "percent": 0,
                        "message": exc.detail,
                        "type": "error",
                    }
                )
                return

            if len(chapters) < 3:
                yield _sse_event(
                    {
                        "current_stage": "error",
                        "percent": 0,
                        "message": "至少需要 3 章才能开始转换",
                        "type": "error",
                    }
                )
                return

            # Create ConversionRun
            run = ConversionRun(
                project_id=project_id,
                status="running",
                stage="validate_input",
            )
            db.add(run)
            await db.commit()
            await db.refresh(run)
            run_id = run.id

        # Build pipeline state
        state = ConversionState(
            project_id=str(project_id),
            project_title=project.name,
            run_id=str(run_id),
            chapters=[
                {
                    "chapter_number": c.number,
                    "title": c.title,
                    "raw_text": c.raw_text,
                    "word_count": c.word_count,
                }
                for c in chapters
            ],
            errors=[],
            chapter_scripts={},
            quality_checks={},
            retry_counts={},
            provider_assignments=provider_assignments,
        )

        graph = build_conversion_graph()
        config = RunnableConfig(
            configurable={
                "thread_id": str(run_id),
                "providers": providers,
            }
        )

        final_status = "running"
        final_stage = "validate_input"
        final_error: str | None = None

        try:
            async for event in graph.astream(state, config=config):
                for node_name, node_output in event.items():
                    # LangGraph yields None for nodes that produce no state
                    # update (e.g. the stage_1_splitter no-op) — guard against it.
                    node_output = node_output or {}
                    progress = node_output.get("progress", {})
                    if progress:
                        final_stage = progress.get("current_stage", final_stage)
                        yield _sse_event(progress)

                    errors = node_output.get("errors", [])
                    for err in errors:
                        final_error = err
                        yield _sse_event(
                            {
                                "current_stage": node_name,
                                "percent": progress.get("percent", 0),
                                "message": err,
                                "type": "error",
                            }
                        )

                    status = node_output.get("status")
                    if status:
                        final_status = status

        except Exception as exc:
            final_status = "failed"
            final_error = str(exc)
            yield _sse_event(
                {
                    "current_stage": "error",
                    "percent": 0,
                    "message": str(exc),
                    "type": "error",
                }
            )

        # Update ConversionRun in DB
        async with async_session_factory() as db:
            run = await db.get(ConversionRun, run_id)
            if run:
                run.status = final_status
                run.stage = final_stage
                run.error_message = final_error
                await db.commit()

        # Persist the assembled script once the run has completed
        if final_status == "completed":
            await _persist_script(project_id, graph, config)
            await _persist_bible_and_characters(project_id, graph, config)

        yield _sse_event(
            {"current_stage": "done", "percent": 100, "message": "转换完成"}
        )
        yield "event: close\ndata: \n\n"

    return StreamingResponse(
        event_generator(), media_type="text/event-stream"
    )


# ── ConversionRun CRUD ──


@router.get("/runs", response_model=list[dict])
async def list_conversion_runs(project_id: uuid.UUID) -> list[dict]:
    """List all conversion runs for a project."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(ConversionRun)
            .where(ConversionRun.project_id == project_id)
            .order_by(ConversionRun.started_at.desc())
        )
        runs = result.scalars().all()
        return [
            {
                "id": str(r.id),
                "status": r.status,
                "stage": r.stage,
                "error_message": r.error_message,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_seconds": r.duration_seconds,
            }
            for r in runs
        ]


@router.get("/runs/{run_id}", response_model=dict)
async def get_conversion_run(
    project_id: uuid.UUID, run_id: uuid.UUID
) -> dict:
    """Get a single conversion run."""
    async with async_session_factory() as db:
        run = await db.get(ConversionRun, run_id)
        if not run or run.project_id != project_id:
            raise HTTPException(status_code=404, detail="Conversion run not found")
        return {
            "id": str(run.id),
            "status": run.status,
            "stage": run.stage,
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "duration_seconds": run.duration_seconds,
            "checkpoint_state": run.checkpoint_state,
        }


# ── Helpers ──


def _sse_event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/runs/{run_id}/resume")
async def resume_conversion(
    project_id: uuid.UUID, run_id: uuid.UUID
) -> StreamingResponse:
    """Resume a paused or failed conversion run via SSE.

    Uses the LangGraph checkpointer (MemorySaver for dev) to resume
    from the last checkpoint. Requires the same ``thread_id`` as the
    original run (which is the run_id).
    """

    async def event_generator():
        async with async_session_factory() as db:
            run = await db.get(ConversionRun, run_id)
            if not run or run.project_id != project_id:
                yield _sse_event(
                    {
                        "current_stage": "error",
                        "percent": 0,
                        "message": "Conversion run 不存在",
                        "type": "error",
                    }
                )
                return

            if run.status not in ("paused", "failed", "running"):
                yield _sse_event(
                    {
                        "current_stage": "error",
                        "percent": 0,
                        "message": f"当前状态 '{run.status}' 不支持恢复",
                        "type": "error",
                    }
                )
                return

            try:
                _project, _chapters, providers, _pa = await _load_project_providers(
                    db, project_id
                )
            except HTTPException as exc:
                yield _sse_event(
                    {
                        "current_stage": "error",
                        "percent": 0,
                        "message": exc.detail,
                        "type": "error",
                    }
                )
                return

            # Reset status to running
            run.status = "running"
            run.error_message = None
            await db.commit()

        graph = build_conversion_graph()
        config = RunnableConfig(
            configurable={
                "thread_id": str(run_id),
                "providers": providers,
            }
        )

        final_status = "running"
        final_stage = run.stage or "validate_input"
        final_error: str | None = None

        try:
            # Resume from checkpoint by passing None as input
            async for event in graph.astream(None, config=config):
                for node_name, node_output in event.items():
                    # LangGraph yields None for nodes that produce no state
                    # update (e.g. the stage_1_splitter no-op) — guard against it.
                    node_output = node_output or {}
                    progress = node_output.get("progress", {})
                    if progress:
                        final_stage = progress.get("current_stage", final_stage)
                        yield _sse_event(progress)

                    errors = node_output.get("errors", [])
                    for err in errors:
                        final_error = err
                        yield _sse_event(
                            {
                                "current_stage": node_name,
                                "percent": progress.get("percent", 0),
                                "message": err,
                                "type": "error",
                            }
                        )

                    status = node_output.get("status")
                    if status:
                        final_status = status

        except Exception as exc:
            final_status = "failed"
            final_error = str(exc)
            yield _sse_event(
                {
                    "current_stage": "error",
                    "percent": 0,
                    "message": str(exc),
                    "type": "error",
                }
            )

        # Update ConversionRun
        async with async_session_factory() as db:
            run = await db.get(ConversionRun, run_id)
            if run:
                run.status = final_status
                run.stage = final_stage
                run.error_message = final_error
                await db.commit()

        # Persist the assembled script once the run has completed
        if final_status == "completed":
            await _persist_script(project_id, graph, config)
            await _persist_bible_and_characters(project_id, graph, config)

        yield _sse_event(
            {"current_stage": "done", "percent": 100, "message": "转换完成"}
        )
        yield "event: close\ndata: \n\n"

    return StreamingResponse(
        event_generator(), media_type="text/event-stream"
    )


# ── Helpers ──


async def _load_project_providers(
    db, project_id: uuid.UUID
) -> tuple[Project, list[Chapter], dict[str, dict], dict[str, str]]:
    """Load project, chapters, and decrypted providers.

    Returns (project, chapters, providers, provider_assignments).
    Raises HTTPException on missing data.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    result = await db.execute(
        select(Chapter)
        .where(Chapter.project_id == project_id)
        .order_by(Chapter.number)
    )
    chapters = result.scalars().all()

    result = await db.execute(select(LLMProvider))
    providers_orm = result.scalars().all()
    if not providers_orm:
        raise HTTPException(
            status_code=400, detail="请先在首页配置 AI 模型"
        )

    providers: dict[str, dict] = {}
    for p in providers_orm:
        api_key = decrypt(p.encrypted_api_key)
        providers[p.provider_id] = {
            "provider_type": p.provider_type,
            "model_name": p.model_name,
            "api_key": api_key,
            "base_url": p.base_url,
            "parameters": p.parameters or {},
        }

    provider_assignments: dict[str, str] = {}
    for p in providers_orm:
        for stage in p.assigned_stages or []:
            provider_assignments[stage] = p.provider_id

    if not provider_assignments:
        first_id = providers_orm[0].provider_id
        provider_assignments = {
            "stage_0": first_id,
            "stage_1": first_id,
            "stage_2": first_id,
        }
    else:
        first_id = providers_orm[0].provider_id
        for stage in ("stage_0", "stage_1", "stage_2"):
            if stage not in provider_assignments:
                provider_assignments[stage] = first_id

    return project, chapters, providers, provider_assignments


async def _persist_script(
    project_id: uuid.UUID, graph, config: RunnableConfig
) -> None:
    """Persist the assembled ScriptV1 to DB rows and YAML (upsert by project).

    Best-effort: reads the final pipeline state from the graph checkpointer and
    writes both normalized DB rows (scenes/blocks/characters) and the legacy YAML
    string. Any failure is logged but never propagated — persistence must not
    break a finished conversion.
    """
    try:
        snapshot = await graph.aget_state(config)
        assembled = (snapshot.values or {}).get("assembled_script")
        if not assembled:
            return
        script = ScriptV1.model_validate(assembled)
        async with async_session_factory() as db:
            await ScriptPersistenceService.persist_script(
                db,
                project_id,
                script,
                delete_missing_characters=True,
                replace_annotations=True,
            )
    except Exception:
        logger.exception("Failed to persist script for project %s", project_id)


async def _persist_bible_and_characters(
    project_id: uuid.UUID, graph, config: RunnableConfig
) -> None:
    """Persist the Story Bible and its characters/relationships after a run.

    Upserts the bible into ``story_bibles`` and creates Character /
    CharacterRelationship rows from the bible's ``character_network`` (skipping
    any that already exist by name, so user-added characters are preserved).
    Best-effort: any failure is logged, never propagated.
    """
    try:
        snapshot = await graph.aget_state(config)
        bible = (snapshot.values or {}).get("story_bible")
        if not bible:
            return

        async with async_session_factory() as db:
            # 1) Upsert the Story Bible content.
            result = await db.execute(
                select(StoryBible).where(StoryBible.project_id == project_id)
            )
            row = result.scalar_one_or_none()
            if row:
                row.content = bible
            else:
                db.add(StoryBible(project_id=project_id, content=bible))
            await db.commit()

            # 2) Characters from character_network.nodes (dedupe by name).
            network = bible.get("character_network") or {}
            existing = await CharacterService.list_by_project(db, project_id)
            by_name = {c.name: c for c in existing}
            id_map: dict[str, object] = {}
            for node in network.get("nodes") or []:
                name = node.get("name")
                if not name:
                    continue
                char = by_name.get(name)
                if char is None:
                    char = await CharacterService.create(
                        db,
                        project_id=project_id,
                        name=name,
                        role_type=node.get("role_type", "supporting"),
                        aliases=[],
                        traits=[],
                    )
                    by_name[name] = char
                if node.get("character_id"):
                    id_map[node["character_id"]] = char

            # 3) Relationships from character_network.edges (skip duplicates).
            existing_rels = await CharacterRelationshipService.list_by_project(
                db, project_id
            )
            seen = {(r.source_character_id, r.target_character_id) for r in existing_rels}
            for edge in network.get("edges") or []:
                src = id_map.get(edge.get("source"))
                tgt = id_map.get(edge.get("target"))
                if not src or not tgt or (src.id, tgt.id) in seen:
                    continue
                intensity = max(1, min(5, int(edge.get("intensity", 3) or 3)))
                await CharacterRelationshipService.create(
                    db,
                    project_id=project_id,
                    source_character_id=src.id,
                    target_character_id=tgt.id,
                    type=str(edge.get("type", "other")),
                    intensity=intensity,
                )
                seen.add((src.id, tgt.id))
    except Exception:
        logger.exception(
            "Failed to persist story bible / characters for project %s", project_id
        )
