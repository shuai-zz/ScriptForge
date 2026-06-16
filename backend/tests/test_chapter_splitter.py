"""Tests for LLM-based chapter splitting."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.chapter_splitter import (
    ChapterSplitError,
    _extract_json,
    split_text_by_llm,
)


def test_extract_json_strips_markdown_fences():
    assert _extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _extract_json('```\n{"a": 1}\n```') == '{"a": 1}'
    assert _extract_json('{"a": 1}') == '{"a": 1}'


@pytest.mark.asyncio
async def test_split_text_by_llm_creates_chapters_from_model_response():
    text = "序章\n开始。\n\n第一章 风起\n正文。\n\n第二章 云涌\n更多。\n\n尾声\n结束。"
    expected_response = {
        "chapters": [
            {"title": "序章", "start_line": 0, "end_line": 2},
            {"title": "第一章 风起", "start_line": 2, "end_line": 4},
            {"title": "第二章 云涌", "start_line": 4, "end_line": 6},
            {"title": "尾声", "start_line": 6, "end_line": 7},
        ]
    }

    fake_model = MagicMock()
    fake_model.ainvoke = AsyncMock(
        return_value=MagicMock(content=json.dumps(expected_response))
    )

    fake_provider = MagicMock()
    fake_db = MagicMock()
    fake_db.execute = AsyncMock(
        return_value=MagicMock(scalars=MagicMock(first=MagicMock(return_value=fake_provider)))
    )

    with patch(
        "app.services.chapter_splitter.create_chat_model",
        return_value=fake_model,
    ):
        chapters = await split_text_by_llm(fake_db, text)

    assert len(chapters) == 4
    titles = [t for t, _ in chapters]
    assert titles == ["序章", "第一章 风起", "第二章 云涌", "尾声"]
    # Verify text slicing: the first chapter should not include later content.
    assert "开始" in chapters[0][1]
    assert "风起" not in chapters[0][1]


@pytest.mark.asyncio
async def test_split_text_by_llm_raises_when_no_provider():
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=result)

    with pytest.raises(ChapterSplitError, match="请先在首页配置 AI 模型"):
        await split_text_by_llm(fake_db, "any text")


@pytest.mark.asyncio
async def test_split_text_by_llm_raises_on_invalid_json():
    fake_model = MagicMock()
    fake_model.ainvoke = AsyncMock(return_value=MagicMock(content="not json"))

    fake_provider = MagicMock()
    fake_db = MagicMock()
    fake_db.execute = AsyncMock(
        return_value=MagicMock(scalars=MagicMock(first=MagicMock(return_value=fake_provider)))
    )

    with patch(
        "app.services.chapter_splitter.create_chat_model",
        return_value=fake_model,
    ):
        with pytest.raises(ChapterSplitError):
            await split_text_by_llm(fake_db, "any text")
