"""Conversion pipeline endpoints: SSE streaming progress."""

import json
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
from app.pipeline.graph import build_conversion_graph
from app.pipeline.state import ConversionState

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
            # Load project
            project = await db.get(Project, project_id)
            if not project:
                yield _sse_event(
                    {
                        "current_stage": "error",
                        "percent": 0,
                        "message": "项目不存在",
                        "type": "error",
                    }
                )
                return

            # Load chapters
            result = await db.execute(
                select(Chapter)
                .where(Chapter.project_id == project_id)
                .order_by(Chapter.number)
            )
            chapters = result.scalars().all()

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

            # Load providers
            result = await db.execute(
                select(LLMProvider).where(LLMProvider.project_id == project_id)
            )
            providers_orm = result.scalars().all()

            if not providers_orm:
                yield _sse_event(
                    {
                        "current_stage": "error",
                        "percent": 0,
                        "message": "请先配置 LLM 模型",
                        "type": "error",
                    }
                )
                return

            # Decrypt and build provider configs
            providers: dict[str, dict] = {}
            for p in providers_orm:
                try:
                    api_key = decrypt(p.encrypted_api_key)
                except Exception:
                    yield _sse_event(
                        {
                            "current_stage": "error",
                            "percent": 0,
                            "message": f"无法解密 provider {p.provider_id} 的 API 密钥",
                            "type": "error",
                        }
                    )
                    return

                providers[p.provider_id] = {
                    "provider_type": p.provider_type,
                    "model_name": p.model_name,
                    "api_key": api_key,
                    "base_url": p.base_url,
                    "parameters": p.parameters or {},
                }

            # Provider assignments per stage
            provider_assignments: dict[str, str] = {}
            for p in providers_orm:
                for stage in p.assigned_stages or []:
                    provider_assignments[stage] = p.provider_id

            # Fallback: use first provider for all unassigned stages
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

        yield _sse_event(
            {"current_stage": "done", "percent": 100, "message": "转换完成"}
        )
        yield "event: close\ndata: \n\n"

    return StreamingResponse(
        event_generator(), media_type="text/event-stream"
    )


def _sse_event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
