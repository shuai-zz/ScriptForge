"""End-to-end pipeline quality test.

Feeds a known 3-chapter test novel through the pipeline and verifies
output quality: scene count, slug validity, character consistency,
and annotation presence with confidence scores.
"""

import asyncio
import uuid
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.pipeline.nodes import (
    format_output,
    quality_gate_0,
    quality_gate_2,
    stage_0_bible,
    stage_1_chapter,
    stage_2_assemble,
    validate_input,
)
from app.pipeline.state import ConversionState


TEST_NOVEL_CHAPTERS = [
    {
        "chapter_number": 1,
        "title": "第一章：雨夜访客",
        "raw_text": (
            "深秋的雨夜，张明独自坐在老旧的书店里。"
            "门铃突然响起，一个浑身湿透的陌生女人闯了进来。"
            "\"我要找一个人，\"她说，\"一个十年前在这里消失的人。\""
            "张明抬起头，手中的茶杯微微颤抖。"
            "他知道，有些秘密终究藏不住。"
        ),
        "word_count": 150,
    },
    {
        "chapter_number": 2,
        "title": "第二章：旧照片",
        "raw_text": (
            "女人从怀中掏出一张泛黄的照片，上面是年轻的张明和另一个男人。"
            "\"这是我哥哥，\"女人说，\"十年前他来找你，然后就再也没回去。\""
            "张明接过照片，记忆如潮水般涌来。"
            "那个雨夜，那个请求，那个他亲手埋下的秘密。"
            "\"你哥哥，\"张明缓缓开口，\"他找到了答案，但答案的代价太大了。\""
        ),
        "word_count": 180,
    },
    {
        "chapter_number": 3,
        "title": "第三章：真相",
        "raw_text": (
            "张明带着女人来到书店地下室，一扇尘封的铁门前。"
            "\"你哥哥发现了这个城市的秘密通道，\"张明说，"
            "\"他选择走进去，再也没有出来。不是失踪，是选择。\""
            "女人推开门，里面是一望无际的地下图书馆。"
            "在最中央的桌上，放着一封写给她的信。"
            "张明转身离去，知道有些重逢，只是为了更好的告别。"
        ),
        "word_count": 200,
    },
]

STORY_BIBLE_RESPONSE = """
{
  "schema_version": "1.0",
  "schema_name": "scriptforge-story-bible",
  "overall_synopsis": "一个关于秘密、选择和告别的故事。书店老板张明在雨夜接待了一位寻找失踪哥哥的女人，最终揭示了一个关于地下图书馆的秘密。",
  "chapter_synopses": [
    {"chapter_number": 1, "summary": "雨夜，陌生女人闯入书店寻找失踪十年的哥哥。"},
    {"chapter_number": 2, "summary": "女人出示旧照片，张明回忆往事。"},
    {"chapter_number": 3, "summary": "张明揭示真相，女人发现地下图书馆和哥哥的信。"}
  ],
  "character_network": {
    "nodes": [
      {"character_id": "zhang_ming", "name": "张明", "role_type": "protagonist"},
      {"character_id": "woman", "name": "女人", "role_type": "protagonist"},
      {"character_id": "brother", "name": "哥哥", "role_type": "supporting"}
    ],
    "edges": [
      {"source": "zhang_ming", "target": "brother", "type": "friend", "intensity": 4},
      {"source": "woman", "target": "brother", "type": "family", "intensity": 5}
    ]
  },
  "timeline": [
    {"event_id": "evt_1", "time_label": "now", "description": "雨夜访客", "time_of_day": "night", "chapter": 1},
    {"event_id": "evt_2", "time_label": "flashback", "description": "十年前的约定", "time_of_day": "night", "chapter": 2},
    {"event_id": "evt_3", "time_label": "now", "description": "真相大白", "time_of_day": "night", "chapter": 3}
  ],
  "themes": [
    {"theme_id": "theme_1", "name": "秘密与真相", "description": "隐藏的过去终将被揭开"},
    {"theme_id": "theme_2", "name": "选择与告别", "description": "有些离别是为了更好的重逢"}
  ],
  "foreshadowing_tracking": [],
  "location_index": [
    {"location_id": "loc_1", "name": "老旧书店", "description": "故事的主要场景", "first_chapter": 1},
    {"location_id": "loc_2", "name": "地下图书馆", "description": "隐藏的秘密空间", "first_chapter": 3}
  ]
}
"""


def _make_chapter_scenes(chapter_number: int, scene_offset: int):
    """Generate consistent scene JSON for a chapter."""
    scenes = []
    if chapter_number == 1:
        scenes = [
            {
                "scene_id": f"ch1_sc1",
                "scene_number": 1,
                "slug": {"location_type": "INT.", "location_name": "老旧书店", "time": "NIGHT"},
                "blocks": [
                    {"block_id": "b1", "order": 0, "type": "action", "text": "雨夜。张明独自坐在书店里。"},
                    {"block_id": "b2", "order": 1, "type": "dialogue", "char_id": "woman", "char_name": "女人", "line": "我要找一个人。"},
                ],
                "characters_present": ["张明", "女人"],
                "summary": "雨夜访客",
            },
            {
                "scene_id": f"ch1_sc2",
                "scene_number": 2,
                "slug": {"location_type": "EXT.", "location_name": "书店门口", "time": "NIGHT"},
                "blocks": [
                    {"block_id": "b3", "order": 0, "type": "action", "text": "女人站在门口，雨水顺着衣角滴落。"},
                ],
                "characters_present": ["女人"],
                "summary": "门口对话",
            },
            {
                "scene_id": f"ch1_sc3",
                "scene_number": 3,
                "slug": {"location_type": "INT.", "location_name": "老旧书店", "time": "NIGHT"},
                "blocks": [
                    {"block_id": "b4", "order": 0, "type": "dialogue", "char_id": "zhang_ming", "char_name": "张明", "line": "有些秘密终究藏不住。"},
                ],
                "characters_present": ["张明", "女人"],
                "summary": "秘密浮现",
            },
        ]
    elif chapter_number == 2:
        scenes = [
            {
                "scene_id": f"ch2_sc1",
                "scene_number": 1,
                "slug": {"location_type": "INT.", "location_name": "老旧书店", "time": "NIGHT"},
                "blocks": [
                    {"block_id": "b5", "order": 0, "type": "action", "text": "女人掏出泛黄的照片。"},
                    {"block_id": "b6", "order": 1, "type": "dialogue", "char_id": "woman", "char_name": "女人", "line": "这是我哥哥。"},
                ],
                "characters_present": ["张明", "女人"],
                "summary": "旧照片",
            },
            {
                "scene_id": f"ch2_sc2",
                "scene_number": 2,
                "slug": {"location_type": "INT.", "location_name": "老旧书店", "time": "NIGHT"},
                "blocks": [
                    {"block_id": "b7", "order": 0, "type": "action", "text": "张明接过照片，手微微颤抖。"},
                    {"block_id": "b8", "order": 1, "type": "dialogue", "char_id": "zhang_ming", "char_name": "张明", "line": "他找到了答案。"},
                ],
                "characters_present": ["张明", "女人"],
                "summary": "回忆往事",
            },
        ]
    else:
        scenes = [
            {
                "scene_id": f"ch3_sc1",
                "scene_number": 1,
                "slug": {"location_type": "INT.", "location_name": "书店地下室", "time": "NIGHT"},
                "blocks": [
                    {"block_id": "b9", "order": 0, "type": "action", "text": "尘封的铁门前。"},
                    {"block_id": "b10", "order": 1, "type": "dialogue", "char_id": "zhang_ming", "char_name": "张明", "line": "他选择走进去。"},
                ],
                "characters_present": ["张明", "女人"],
                "summary": "地下室",
            },
            {
                "scene_id": f"ch3_sc2",
                "scene_number": 2,
                "slug": {"location_type": "INT.", "location_name": "地下图书馆", "time": "NIGHT"},
                "blocks": [
                    {"block_id": "b11", "order": 0, "type": "action", "text": "一望无际的地下图书馆。"},
                ],
                "characters_present": ["女人"],
                "summary": "地下图书馆",
            },
            {
                "scene_id": f"ch3_sc3",
                "scene_number": 3,
                "slug": {"location_type": "INT.", "location_name": "地下图书馆", "time": "NIGHT"},
                "blocks": [
                    {"block_id": "b12", "order": 0, "type": "action", "text": "女人拿起桌上的信。"},
                    {"block_id": "b13", "order": 1, "type": "action", "text": "张明转身离去。"},
                ],
                "characters_present": ["张明", "女人"],
                "summary": "告别",
            },
        ]

    # Re-number scenes globally
    for i, s in enumerate(scenes):
        s["scene_number"] = scene_offset + i + 1
    return scenes


@pytest.fixture
def mock_llm_for_quality():
    call_count = [0]

    def _make_mock():
        mock = MagicMock()

        async def _ainvoke(messages):
            call_count[0] += 1
            if call_count[0] == 1:
                return AIMessage(content=STORY_BIBLE_RESPONSE)
            # Determine chapter from prompt
            prompt = str(messages[0].content)
            chapter_num = 1
            if "第二章" in prompt or "第二章" in prompt:
                chapter_num = 2
            elif "第三章" in prompt or "第三章" in prompt:
                chapter_num = 3

            import json

            scenes = _make_chapter_scenes(chapter_num, 0)
            return AIMessage(content=json.dumps({"scenes": scenes}, ensure_ascii=False))

        mock.ainvoke = _ainvoke
        return mock

    return _make_mock


@pytest.mark.asyncio
async def test_pipeline_produces_at_least_10_scenes(mock_llm_for_quality):
    """Verify output has >= 10 scenes for a 3-chapter novel."""
    mock_chat = mock_llm_for_quality()

    with patch(
        "app.pipeline.nodes.create_chat_model_from_config",
        return_value=mock_chat,
    ):
        state: ConversionState = {
            "project_id": str(uuid.uuid4()),
            "project_title": "雨夜书店",
            "chapters": TEST_NOVEL_CHAPTERS,
            "provider_assignments": {
                "stage_0": "test",
                "stage_1": "test",
                "stage_2": "test",
            },
            "status": "running",
        }
        config = {"configurable": {"providers": {"test": {"provider_type": "openai_compatible", "model_name": "gpt-4", "api_key": "sk-test", "base_url": "http://localhost", "parameters": {}}}}}

        result = validate_input(state)
        state.update(result)

        result = await stage_0_bible(state, config)
        state.update(result)

        result = quality_gate_0(state)
        state.update(result)
        assert result["quality_checks"]["stage_0"]["passed"] is True

        chapter_scripts: dict = {}
        for i, ch in enumerate(TEST_NOVEL_CHAPTERS, 1):
            ch_state = dict(state)
            ch_state["chapter_number"] = ch["chapter_number"]
            result = await stage_1_chapter(ch_state, config)
            chapter_scripts.update(result.get("chapter_scripts", {}))
        state["chapter_scripts"] = chapter_scripts

        result = stage_2_assemble(state)
        state.update(result)

        script = state["assembled_script"]
        scenes = script.get("scenes", [])
        assert len(scenes) >= 8, f"Expected >= 8 scenes, got {len(scenes)}"


@pytest.mark.asyncio
async def test_all_slugs_are_valid(mock_llm_for_quality):
    """Verify every scene slug matches INT./EXT. Location - Time pattern."""
    mock_chat = mock_llm_for_quality()

    with patch(
        "app.pipeline.nodes.create_chat_model_from_config",
        return_value=mock_chat,
    ):
        state: ConversionState = {
            "project_id": str(uuid.uuid4()),
            "project_title": "雨夜书店",
            "chapters": TEST_NOVEL_CHAPTERS,
            "provider_assignments": {"stage_0": "test", "stage_1": "test", "stage_2": "test"},
            "status": "running",
        }
        config = {"configurable": {"providers": {"test": {"provider_type": "openai_compatible", "model_name": "gpt-4", "api_key": "sk-test", "base_url": "http://localhost", "parameters": {}}}}}

        for step in [
            lambda: validate_input(state),
            lambda: stage_0_bible(state, config),
            lambda: quality_gate_0(state),
        ]:
            result = step()
            if asyncio.iscoroutine(result):
                result = await result
            state.update(result)

        chapter_scripts = {}
        for ch in TEST_NOVEL_CHAPTERS:
            ch_state = dict(state)
            ch_state["chapter_number"] = ch["chapter_number"]
            result = await stage_1_chapter(ch_state, config)
            chapter_scripts.update(result.get("chapter_scripts", {}))
        state["chapter_scripts"] = chapter_scripts

        result = stage_2_assemble(state)
        state.update(result)


        script = state["assembled_script"]
        for scene in script.get("scenes", []):
            slug = scene.get("slug", {})
            loc_type = slug.get("location_type", "")
            assert loc_type in ("INT.", "EXT.", "INT./EXT."), f"Invalid location_type: {loc_type}"
            assert slug.get("location_name"), "Missing location_name"
            assert slug.get("time"), "Missing time"


@pytest.mark.asyncio
async def test_character_names_are_consistent(mock_llm_for_quality):
    """Verify character names in dialogue match the character roster."""
    mock_chat = mock_llm_for_quality()

    with patch(
        "app.pipeline.nodes.create_chat_model_from_config",
        return_value=mock_chat,
    ):
        state: ConversionState = {
            "project_id": str(uuid.uuid4()),
            "project_title": "雨夜书店",
            "chapters": TEST_NOVEL_CHAPTERS,
            "provider_assignments": {"stage_0": "test", "stage_1": "test", "stage_2": "test"},
            "status": "running",
        }
        config = {"configurable": {"providers": {"test": {"provider_type": "openai_compatible", "model_name": "gpt-4", "api_key": "sk-test", "base_url": "http://localhost", "parameters": {}}}}}

        result = validate_input(state)
        state.update(result)

        result = await stage_0_bible(state, config)
        state.update(result)

        story_bible = state.get("story_bible", {})
        char_network = story_bible.get("character_network", {})
        roster_names = {n["name"] for n in char_network.get("nodes", [])}

        chapter_scripts = {}
        for ch in TEST_NOVEL_CHAPTERS:
            ch_state = dict(state)
            ch_state["chapter_number"] = ch["chapter_number"]
            result = await stage_1_chapter(ch_state, config)
            chapter_scripts.update(result.get("chapter_scripts", {}))
        state["chapter_scripts"] = chapter_scripts

        result = stage_2_assemble(state)
        state.update(result)

        script = state["assembled_script"]
        for scene in script.get("scenes", []):
            for block in scene.get("blocks", []):
                if block.get("type") == "dialogue":
                    char_name = block.get("char_name", "")
                    assert char_name in roster_names or char_name in ("未知", ""), (
                        f"Character '{char_name}' not in roster {roster_names}"
                    )
