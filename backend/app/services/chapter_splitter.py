"""LLM-based chapter splitting for non-standard novel formats."""

import json
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversion import LLMProvider
from app.services.llm_factory import LLMFactoryError, create_chat_model


class ChapterSplitError(Exception):
    """Raised when LLM chapter splitting fails."""

    pass


_SYSTEM_PROMPT = """You are a novel chapter splitter.

Given the full text of a novel (or a long story), identify natural chapter boundaries and their titles.
The input text uses zero-based line indices: the first line is line 0, the second line is line 1, etc.

Output a single JSON object with this exact shape:
{
  "chapters": [
    {"title": "Prologue", "start_line": 0, "end_line": 42},
    {"title": "The Beginning", "start_line": 43, "end_line": 156},
    ...
  ]
}

Rules:
- The first chapter must start at line 0.
- The last chapter must end at the last line of the text.
- Chapters must be ordered and non-overlapping.
- If the text has no clear chapter boundaries, return a single chapter.
- "title" should be the chapter title as it appears in the text, cleaned up. If there is no title, use "第N章" where N is the chapter index starting at 1.
- Output ONLY valid JSON. Do not wrap it in markdown code fences.
"""


def _extract_json(text: str) -> str:
    """Extract a JSON object from LLM output, tolerating markdown fences."""
    text = text.strip()
    # Strip markdown code fences if present.
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _normalize_title(title: str, idx: int) -> str:
    """Return a clean title or a fallback."""
    title = (title or "").strip()
    if title:
        return title
    return f"第{idx + 1}章"


async def split_text_by_llm(
    db: AsyncSession,
    text: str,
    provider_id: str | None = None,
) -> list[tuple[str, str]]:
    """Split a full novel text into chapters using the configured LLM.

    Args:
        db: Database session for loading the LLM provider.
        text: The full novel text.
        provider_id: Optional specific provider to use. If omitted, the first
            configured provider is used.

    Returns:
        A list of (title, raw_text) tuples, one per detected chapter.

    Raises:
        ChapterSplitError: If no provider is configured or the LLM response
            cannot be parsed into valid chapter boundaries.
    """
    lines = text.splitlines()
    if not lines:
        return []

    query = select(LLMProvider)
    if provider_id:
        query = query.where(LLMProvider.provider_id == provider_id)
    result = await db.execute(query)
    provider = result.scalars().first()

    if provider is None:
        raise ChapterSplitError("请先在首页配置 AI 模型")

    try:
        model = create_chat_model(provider)
    except LLMFactoryError as exc:
        raise ChapterSplitError(str(exc)) from exc

    prompt = f"Total lines: {len(lines)}\n\n{text}"

    try:
        response = await model.ainvoke(
            [
                ("system", _SYSTEM_PROMPT),
                ("human", prompt),
            ]
        )
    except Exception as exc:
        raise ChapterSplitError(f"LLM 调用失败: {exc}") from exc

    raw_content = response.content if hasattr(response, "content") else str(response)
    json_text = _extract_json(raw_content)

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ChapterSplitError(f"LLM 返回内容不是合法 JSON: {exc}") from exc

    chapter_items = parsed.get("chapters") if isinstance(parsed, dict) else None
    if not isinstance(chapter_items, list):
        raise ChapterSplitError("LLM 返回的 JSON 缺少 'chapters' 数组")

    total_lines = len(lines)
    chapters: list[tuple[str, str]] = []
    expected_start = 0

    for idx, item in enumerate(chapter_items):
        if not isinstance(item, dict):
            continue
        start_line = int(item.get("start_line", expected_start))
        end_line = int(item.get("end_line", total_lines))

        # Clamp and sanitize boundaries.
        start_line = max(0, min(start_line, total_lines))
        end_line = max(start_line, min(end_line, total_lines))

        # Fill any gap from the expected position to keep the text complete.
        if start_line > expected_start:
            start_line = expected_start

        title = _normalize_title(item.get("title", ""), idx)
        chapter_text = "\n".join(lines[start_line:end_line]).strip()
        if chapter_text:
            chapters.append((title, chapter_text))
            expected_start = end_line

    # If nothing was produced, fall back to a single chapter.
    if not chapters:
        chapters.append(("全文", text))

    return chapters
