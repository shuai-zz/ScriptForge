"""Integration test for the full AI conversion pipeline.

Mocks LLM responses and verifies that pipeline nodes execute all stages
and that Pydantic validators + semantic validators run at quality gates.

Note: Tests invoke nodes directly (rather than through the full graph)
because LangGraph Send does not propagate full parent state to map tasks
in the current version—this is a known framework limitation.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.pipeline.graph import build_conversion_graph
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


@pytest.fixture
def mock_llm_response():
    """Return a mock ChatModel that returns structured JSON responses."""

    def _make_mock(story_bible_json: str, chapter_scene_json: str):
        mock = MagicMock()

        call_count = [0]

        async def _ainvoke(messages):
            prompt = str(messages[0].content)
            call_count[0] += 1
            # First call is always stage_0 bible generation
            if call_count[0] == 1:
                return AIMessage(content=story_bible_json)
            # Subsequent calls are stage_1 chapter conversions
            return AIMessage(content=chapter_scene_json)

        mock.ainvoke = _ainvoke
        return mock

    return _make_mock


@pytest.fixture
def sample_chapters():
    return [
        {
            "chapter_number": 1,
            "title": "第一章",
            "raw_text": "这是一个测试小说的第一章内容。主角张三登场。",
            "word_count": 100,
        },
        {
            "chapter_number": 2,
            "title": "第二章",
            "raw_text": "第二章，张三遇到了李四。他们开始冒险。",
            "word_count": 100,
        },
        {
            "chapter_number": 3,
            "title": "第三章",
            "raw_text": "第三章，冒险结束。张三和李四成为朋友。",
            "word_count": 100,
        },
    ]


STORY_BIBLE_JSON = """
{
  "schema_version": "1.0",
  "schema_name": "scriptforge-story-bible",
  "overall_synopsis": "测试小说的故事圣经",
  "chapter_synopses": [
    {"chapter_number": 1, "summary": "第一章简介"},
    {"chapter_number": 2, "summary": "第二章简介"},
    {"chapter_number": 3, "summary": "第三章简介"}
  ],
  "character_network": {
    "nodes": [
      {"character_id": "char_1", "name": "张三", "role_type": "protagonist"},
      {"character_id": "char_2", "name": "李四", "role_type": "supporting"}
    ],
    "edges": [
      {"source": "char_1", "target": "char_2", "type": "friend", "intensity": 3}
    ]
  },
  "timeline": [
    {"event_id": "evt_1", "time_label": "now", "description": "张三登场", "time_of_day": "morning", "chapter": 1}
  ],
  "themes": [
    {"theme_id": "theme_1", "name": "友谊", "description": "关于友谊的主题"}
  ],
  "foreshadowing_tracking": [],
  "location_index": [
    {"location_id": "loc_1", "name": "村庄", "description": "故事发生地", "first_chapter": 1}
  ]
}
"""

CHAPTER_SCENE_JSON = """
{
  "scenes": [
    {
      "scene_id": "scene_1",
      "scene_number": 1,
      "slug": {
        "location_type": "EXT.",
        "location_name": "村庄",
        "time": "DAY"
      },
      "blocks": [
        {
          "block_id": "blk_1",
          "order": 0,
          "type": "action",
          "text": "张三走在村庄的小路上。"
        },
        {
          "block_id": "blk_2",
          "order": 1,
          "type": "dialogue",
          "char_id": "char_1",
          "char_name": "张三",
          "line": "今天天气真好。"
        }
      ],
      "characters_present": ["张三"],
      "summary": "张三登场"
    },
    {
      "scene_id": "scene_2",
      "scene_number": 2,
      "slug": {
        "location_type": "INT.",
        "location_name": "屋内",
        "time": "NIGHT"
      },
      "blocks": [
        {
          "block_id": "blk_3",
          "order": 0,
          "type": "action",
          "text": "张三坐在屋里。"
        },
        {
          "block_id": "blk_4",
          "order": 1,
          "type": "dialogue",
          "char_id": "char_1",
          "char_name": "张三",
          "line": "该休息了。"
        }
      ],
      "characters_present": ["张三"],
      "summary": "张三休息"
    }
  ]
}
"""

PROVIDER_CONFIG = {
    "test-provider": {
        "provider_type": "openai_compatible",
        "model_name": "gpt-4",
        "api_key": "sk-test",
        "base_url": "http://localhost:9999",
        "parameters": {"temperature": 0.7},
    }
}


@pytest.mark.asyncio
async def test_pipeline_nodes_execute_all_stages(mock_llm_response, sample_chapters):
    """Invoke nodes sequentially to verify all stages execute correctly."""
    mock_chat = mock_llm_response(STORY_BIBLE_JSON, CHAPTER_SCENE_JSON)

    with patch(
        "app.pipeline.nodes.create_chat_model_from_config",
        return_value=mock_chat,
    ):
        state: ConversionState = {
            "project_id": str(uuid.uuid4()),
            "project_title": "测试项目",
            "chapters": sample_chapters,
            "provider_assignments": {
                "stage_0": "test-provider",
                "stage_1": "test-provider",
                "stage_2": "test-provider",
            },
            "status": "running",
        }
        config = {"configurable": {"providers": PROVIDER_CONFIG}}

        # Stage: validate_input
        result = validate_input(state)
        assert result.get("status") == "running"
        state.update(result)

        # Stage: stage_0_bible
        result = await stage_0_bible(state, config)
        assert "story_bible" in result
        assert result["story_bible"] is not None
        state.update(result)

        # Gate: quality_gate_0
        result = quality_gate_0(state)
        assert result["quality_checks"]["stage_0"]["passed"] is True
        state.update(result)

        # Stage: stage_1_chapter (run once per chapter)
        chapter_scripts: dict = {}
        for ch in sample_chapters:
            ch_state = dict(state)
            ch_state["chapter_number"] = ch["chapter_number"]
            result = await stage_1_chapter(ch_state, config)
            chapter_scripts.update(result.get("chapter_scripts", {}))

        state["chapter_scripts"] = chapter_scripts
        assert len(chapter_scripts) == 3

        # Stage: stage_2_assemble
        result = stage_2_assemble(state)
        assert "assembled_script" in result
        assert result["assembled_script"] is not None
        state.update(result)

        # Gate: quality_gate_2
        result = quality_gate_2(state)
        assert "stage_2" in result["quality_checks"]
        state.update(result)

        # Stage: format_output
        result = await format_output(state, config)
        assert result.get("status") == "completed" or "errors" in result


@pytest.mark.asyncio
async def test_pydantic_validation_runs_at_stage_0(mock_llm_response, sample_chapters):
    """Verify that invalid LLM output triggers Pydantic validation error."""
    bad_json = '{"invalid": true}'  # Missing required fields
    mock_chat = mock_llm_response(bad_json, CHAPTER_SCENE_JSON)

    with patch(
        "app.pipeline.nodes.create_chat_model_from_config",
        return_value=mock_chat,
    ):
        state: ConversionState = {
            "project_id": str(uuid.uuid4()),
            "project_title": "测试项目",
            "chapters": sample_chapters,
            "provider_assignments": {"stage_0": "test-provider"},
            "status": "running",
        }
        config = {"configurable": {"providers": PROVIDER_CONFIG}}

        result = await stage_0_bible(state, config)
        errors = result.get("errors", [])
        assert any(
            "parse" in e.lower()
            or "validation" in e.lower()
            or "pydantic" in e.lower()
            or "story_bible" in e.lower()
            for e in errors
        )


MALFORMED_BIBLE_JSON = """
{
  "metadata": {"title": "三体"},
  "chapter_synopses": [
    {"chapter_number": "第1章", "summary": "汪淼发现倒计时", "key_events": [{"description": "倒计时", "significance": "setup"}]}
  ],
  "timeline": [
    {"sequence": 1, "event": "汪淼发现倒计时", "chapter": "第1章"},
    {"sequence": 2, "event": "丁仪解释物理崩溃", "chapter": "第2章"},
    {"sequence": 3, "event": "史强讲射手假说", "chapter": "第3章"}
  ],
  "themes": [
    {"title": "规律与破缺", "summary": "必然与偶然的对立。"}
  ]
}
"""


@pytest.mark.asyncio
async def test_stage_0_recovers_malformed_bible(mock_llm_response, sample_chapters):
    """Real-world failure shape (wrong field names, '第N章', missing synopsis) is
    repaired by normalization so stage_0 succeeds instead of erroring out."""
    mock_chat = mock_llm_response(MALFORMED_BIBLE_JSON, CHAPTER_SCENE_JSON)

    with patch(
        "app.pipeline.nodes.create_chat_model_from_config",
        return_value=mock_chat,
    ):
        state: ConversionState = {
            "project_id": str(uuid.uuid4()),
            "project_title": "三体",
            "chapters": sample_chapters,
            "provider_assignments": {"stage_0": "test-provider"},
            "status": "running",
        }
        config = {"configurable": {"providers": PROVIDER_CONFIG}}

        result = await stage_0_bible(state, config)

    assert not result.get("errors"), result.get("errors")
    bible = result.get("story_bible")
    assert bible is not None
    assert [e["chapter"] for e in bible["timeline"]] == [1, 2, 3]
    assert bible["themes"][0]["name"] == "规律与破缺"
    assert bible["overall_synopsis"]


@pytest.mark.asyncio
async def test_semantic_validators_run_at_stage_2(mock_llm_response, sample_chapters):
    """Verify that semantic validators run during stage_2_assemble."""
    mock_chat = mock_llm_response(STORY_BIBLE_JSON, CHAPTER_SCENE_JSON)

    with patch(
        "app.pipeline.nodes.create_chat_model_from_config",
        return_value=mock_chat,
    ):
        state: ConversionState = {
            "project_id": str(uuid.uuid4()),
            "project_title": "测试项目",
            "chapters": sample_chapters,
            "provider_assignments": {
                "stage_0": "test-provider",
                "stage_1": "test-provider",
                "stage_2": "test-provider",
            },
            "status": "running",
        }
        config = {"configurable": {"providers": PROVIDER_CONFIG}}

        # Run through stage_0 and stage_1
        result = validate_input(state)
        state.update(result)

        result = await stage_0_bible(state, config)
        state.update(result)

        result = quality_gate_0(state)
        state.update(result)

        chapter_scripts: dict = {}
        for ch in sample_chapters:
            ch_state = dict(state)
            ch_state["chapter_number"] = ch["chapter_number"]
            result = await stage_1_chapter(ch_state, config)
            chapter_scripts.update(result.get("chapter_scripts", {}))
        state["chapter_scripts"] = chapter_scripts

        # Run stage_2_assemble and quality_gate_2
        result = stage_2_assemble(state)
        state.update(result)

        result = quality_gate_2(state)
        qc = result.get("quality_checks", {})
        assert "stage_2" in qc
        assert "issues" in qc["stage_2"]

        # Scene numbers should be sequential
        script = state["assembled_script"]
        scenes = script.get("scenes", [])
        if scenes:
            for i, scene in enumerate(scenes, 1):
                assert scene["scene_number"] == i


def test_graph_has_all_nodes():
    """Verify the compiled StateGraph contains all expected nodes."""
    graph = build_conversion_graph()
    nodes = list(graph.nodes.keys())
    expected = [
        "validate_input",
        "stage_0_bible",
        "quality_gate_0",
        "stage_1_splitter",
        "stage_1_chapter",
        "stage_2_assemble",
        "quality_gate_2",
        "format_output",
    ]
    for node in expected:
        assert node in nodes, f"Node '{node}' not found in graph"


@pytest.mark.asyncio
async def test_astream_node_outputs_are_dicts(mock_llm_response, sample_chapters):
    """Regression: a node returning {} (stage_1_splitter) makes LangGraph stream
    None for that node, which crashed the SSE consumer with
    "'NoneType' object has no attribute 'get'". Every streamed node output must
    be a non-None dict so the consumer's node_output.get(...) is safe."""
    mock_chat = mock_llm_response(STORY_BIBLE_JSON, CHAPTER_SCENE_JSON)
    with patch(
        "app.pipeline.nodes.create_chat_model_from_config",
        return_value=mock_chat,
    ):
        state: ConversionState = {
            "project_id": str(uuid.uuid4()),
            "project_title": "测试项目",
            "run_id": "test-run",
            "chapters": sample_chapters,
            "errors": [],
            "chapter_scripts": {},
            "quality_checks": {},
            "retry_counts": {},
            "provider_assignments": {
                "stage_0": "test-provider",
                "stage_1": "test-provider",
                "stage_2": "test-provider",
            },
            "status": "running",
        }
        config = {
            "configurable": {"thread_id": "test-run", "providers": PROVIDER_CONFIG}
        }
        graph = build_conversion_graph()

        saw_splitter = False
        async for event in graph.astream(state, config=config):
            for node_name, node_output in event.items():
                assert node_output is not None, f"node '{node_name}' streamed None"
                assert isinstance(node_output, dict)
                if node_name == "stage_1_splitter":
                    saw_splitter = True

        assert saw_splitter, "stage_1_splitter path was not exercised"


@pytest.mark.asyncio
async def test_full_pipeline_produces_script(mock_llm_response, sample_chapters):
    """End-to-end: a passing Story Bible + chapter scenes yield an assembled
    script. Guards the Send payload (stage_1_chapter must receive chapters /
    providers via {**state}), scene normalization, and assembly — without the
    Send fix stage_1 fails with "未找到" and no script is produced."""
    mock_chat = mock_llm_response(STORY_BIBLE_JSON, CHAPTER_SCENE_JSON)
    with patch(
        "app.pipeline.nodes.create_chat_model_from_config",
        return_value=mock_chat,
    ):
        state: ConversionState = {
            "project_id": str(uuid.uuid4()),
            "project_title": "测试项目",
            "run_id": "test-run-full",
            "chapters": sample_chapters,
            "errors": [],
            "chapter_scripts": {},
            "quality_checks": {},
            "retry_counts": {},
            "provider_assignments": {
                "stage_0": "test-provider",
                "stage_1": "test-provider",
                "stage_2": "test-provider",
            },
            "status": "running",
        }
        config = {
            "configurable": {
                "thread_id": "test-run-full",
                "providers": PROVIDER_CONFIG,
            }
        }
        graph = build_conversion_graph()

        async for _event in graph.astream(state, config=config):
            pass
        snapshot = await graph.aget_state(config)

    script = (snapshot.values or {}).get("assembled_script")
    assert script is not None, "no assembled_script — stage_1 produced no scenes"
    assert len(script.get("scenes", [])) >= 1
