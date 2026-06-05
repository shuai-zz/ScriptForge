"""LangGraph state definition for the AI conversion pipeline."""

import operator
from typing import Annotated, TypedDict


class ChapterInput(TypedDict, total=False):
    """A single novel chapter as pipeline input."""

    chapter_number: int
    title: str
    raw_text: str
    word_count: int


class PipelineProgress(TypedDict, total=False):
    """Current pipeline execution progress."""

    current_stage: str
    percent: int
    message: str
    details: dict


class QualityCheckResult(TypedDict, total=False):
    """Result of a single quality gate check."""

    passed: bool
    issues: list[str]
    retry_count: int


def _merge_dicts(left: dict, right: dict) -> dict:
    """Merge two dictionaries (right overrides left for overlapping keys)."""
    merged = left.copy()
    merged.update(right)
    return merged


class ConversionState(TypedDict, total=False):
    """Complete state for the LangGraph conversion pipeline.

    Each stage node reads from and writes to specific fields.
    Annotated fields use reducers so that parallel/map nodes
    can contribute partial updates without overwriting each other.
    """

    # ── Identity ──
    project_id: str
    run_id: str | None

    # ── Inputs ──
    chapters: list[ChapterInput]

    # ── Stage 0 outputs ──
    story_bible: dict | None

    # ── Stage 1 outputs (key = chapter_number as string) ──
    chapter_scripts: Annotated[dict[str, list[dict]], _merge_dicts]

    # ── Stage 2 outputs ──
    assembled_script: dict | None

    # ── Tracking & quality ──
    errors: Annotated[list[str], operator.add]
    progress: PipelineProgress
    quality_checks: Annotated[dict[str, QualityCheckResult], _merge_dicts]
    retry_counts: Annotated[dict[str, int], _merge_dicts]

    # ── Configuration ──
    provider_assignments: dict[str, str]  # stage -> provider_id
    status: str  # running | completed | failed | paused | retrying
