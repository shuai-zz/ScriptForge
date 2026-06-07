"""Tests for stage_1 scene normalization (repairing LLM script output).

The model often returns slug as a string ('INT. 地点 - 夜') and omits
scene_id / block_id / order, which made every scene fail Scene validation and
left the run with no script. These tests pin the coercion that fixes it.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage

from app.pipeline.nodes import (
    _coerce_slug,
    _coerce_time_of_day,
    _normalize_scene,
    stage_1_chapter,
)
from app.schemas.script import Scene


def test_coerce_time_of_day():
    assert _coerce_time_of_day("夜") == "NIGHT"
    assert _coerce_time_of_day("下午") == "AFTERNOON"
    assert _coerce_time_of_day("黄昏") == "DUSK"
    assert _coerce_time_of_day("NIGHT") == "NIGHT"
    assert _coerce_time_of_day("night") == "NIGHT"
    assert _coerce_time_of_day("不知道") == "DAY"  # fallback
    assert _coerce_time_of_day(None) == "DAY"


def test_coerce_slug_from_string():
    assert _coerce_slug("INT. 汪淼家客厅 - 夜") == {
        "location_type": "INT.",
        "location_name": "汪淼家客厅",
        "time": "NIGHT",
    }
    s = _coerce_slug("EXT. 台球厅 - 下午")
    assert s["location_type"] == "EXT."
    assert s["location_name"] == "台球厅"
    assert s["time"] == "AFTERNOON"


def test_coerce_slug_from_dict_and_fallback():
    assert _coerce_slug(
        {"location_type": "EXT.", "location_name": "街道", "time": "DAY"}
    ) == {"location_type": "EXT.", "location_name": "街道", "time": "DAY"}
    # missing/invalid pieces → safe defaults
    assert _coerce_slug(None) == {
        "location_type": "INT.",
        "location_name": "未知地点",
        "time": "DAY",
    }


def test_normalize_scene_fills_required_fields():
    scene = {
        "slug": "INT. 房间 - 夜",
        "blocks": [
            {"type": "action", "text": "动作"},
            {"char_name": "甲", "line": "台词"},  # no type/block_id/order
        ],
    }
    out = _normalize_scene(scene, chapter_number=1, index=0)
    Scene.model_validate(out)  # must not raise
    assert out["scene_id"] == "sc-1-1"
    assert out["scene_number"] == 1
    assert out["slug"]["time"] == "NIGHT"
    assert out["blocks"][0]["block_id"] and out["blocks"][0]["order"] == 0
    assert out["blocks"][1]["order"] == 1
    assert out["blocks"][1]["type"] == "dialogue"  # inferred from line/char_name


def test_normalize_scene_coerces_annotation_strings():
    """The model often drops a description string into scene.annotations
    (list[SceneAnnotationRef]) and objects into block.annotation_refs (list[str])."""
    scene = {
        "slug": {"location_type": "INT.", "location_name": "x", "time": "DAY"},
        "blocks": [
            {
                "block_id": "b1",
                "order": 0,
                "type": "action",
                "text": "t",
                "annotation_refs": [{"id": "a"}],
            }
        ],
        "annotations": ["本场景对应小说第二章的物理学崩溃揭示。"],
    }
    out = _normalize_scene(scene, 2, 0)
    Scene.model_validate(out)  # must not raise
    assert out["annotations"][0] == {
        "annotation_id": "本场景对应小说第二章的物理学崩溃揭示。"
    }
    assert out["blocks"][0]["annotation_refs"] == ["a"]


async def test_stage_1_recovers_natural_llm_output():
    yaml_out = """```yaml
scenes:
  - scene_number: 1
    slug: "INT. 汪淼家客厅 - 夜"
    characters_present: [c1]
    blocks:
      - {type: action, text: 汪淼坐在沙发上。}
      - {type: dialogue, char_name: 汪淼, line: 这不可能……}
```"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=AIMessage(content=yaml_out))
    state = {
        "chapter_number": 1,
        "chapters": [{"chapter_number": 1, "title": "t", "raw_text": "x", "word_count": 1}],
        "story_bible": {},
        "chapter_scripts": {},
        "provider_assignments": {"stage_1": "p"},
    }
    config = {
        "configurable": {
            "providers": {
                "p": {
                    "provider_type": "anthropic",
                    "model_name": "m",
                    "api_key": "k",
                    "base_url": None,
                    "parameters": {},
                }
            }
        }
    }
    with patch("app.pipeline.nodes.create_chat_model_from_config", return_value=mock):
        result = await stage_1_chapter(state, config)

    assert not result.get("errors"), result.get("errors")
    scenes = result["chapter_scripts"]["1"]
    assert len(scenes) == 1
    assert scenes[0]["slug"]["time"] == "NIGHT"
    assert all(b.get("block_id") for b in scenes[0]["blocks"])
