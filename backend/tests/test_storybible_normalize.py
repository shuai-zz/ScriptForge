"""Tests for Story Bible normalization (stage_0 LLM-output repair).

Reproduces the malformed shape that broke a real 三体 conversion (wrong field
names, '第N章' chapter strings, missing overall_synopsis/ids) and asserts the
normalizer maps it back to a valid StoryBibleV1.
"""

from app.pipeline.nodes import _coerce_chapter_int, _normalize_story_bible
from app.schemas.story_bible import StoryBibleV1


def test_coerce_chapter_int():
    assert _coerce_chapter_int("第1章") == 1
    assert _coerce_chapter_int("第12章") == 12
    assert _coerce_chapter_int(3) == 3
    assert _coerce_chapter_int("5") == 5
    assert _coerce_chapter_int("") == 1  # default
    assert _coerce_chapter_int(None) == 1
    assert _coerce_chapter_int(0) == 1  # below ge=1 → default


def test_normalize_repairs_real_failure_shape():
    """The exact deviation pattern from the reported error."""
    bad = {
        "metadata": {"title": "三体"},
        "chapter_synopses": [
            {
                "chapter_number": "第1章",
                "summary": "汪淼发现照片上的倒计时",
                "key_events": [{"description": "倒计时出现", "significance": "setup"}],
            }
        ],
        "timeline": [
            {"sequence": 1, "event": "汪淼发现倒计时", "chapter": "第1章"},
            {"sequence": 2, "event": "丁仪用台球解释物理崩溃", "chapter": "第2章"},
            {"sequence": 3, "event": "史强讲射手假说", "chapter": "第3章"},
        ],
        "themes": [
            {"title": "规律与破缺", "summary": "必然与偶然的对立。"},
        ],
        # overall_synopsis intentionally missing
    }

    normalized = _normalize_story_bible(bad)
    # Must now validate without raising.
    sb = StoryBibleV1.model_validate(normalized)

    # chapter strings coerced to ints
    assert [e.chapter for e in sb.timeline] == [1, 2, 3]
    assert sb.chapter_synopses[0].chapter_number == 1
    # timeline required fields filled / aliased
    assert sb.timeline[0].description == "汪淼发现倒计时"
    assert sb.timeline[0].event_id
    assert sb.timeline[0].time_label.value == "now"
    assert sb.timeline[0].time_of_day.value == "afternoon"
    # theme title -> name, ids/description filled
    assert sb.themes[0].name == "规律与破缺"
    assert sb.themes[0].theme_id
    assert sb.themes[0].description
    # overall_synopsis synthesized from chapter summaries
    assert sb.overall_synopsis


def test_normalize_leaves_valid_data_intact():
    good = {
        "overall_synopsis": "完整概要",
        "timeline": [
            {
                "event_id": "evt-9",
                "time_label": "flashback",
                "description": "原本就对的事件",
                "time_of_day": "night",
                "chapter": 2,
            }
        ],
        "themes": [
            {"theme_id": "t-9", "name": "原本的主题", "description": "原本的描述"}
        ],
    }
    sb = StoryBibleV1.model_validate(_normalize_story_bible(good))
    assert sb.overall_synopsis == "完整概要"
    ev = sb.timeline[0]
    assert ev.event_id == "evt-9"
    assert ev.time_label.value == "flashback"
    assert ev.time_of_day.value == "night"
    assert ev.chapter == 2
    assert sb.themes[0].theme_id == "t-9"
    assert sb.themes[0].name == "原本的主题"


def test_normalize_handles_invalid_enum_values():
    """An out-of-vocabulary time_of_day/time_label is coerced to a safe default."""
    data = {
        "overall_synopsis": "x",
        "timeline": [
            {
                "event_id": "e1",
                "time_label": "现在",
                "description": "d",
                "time_of_day": "noon",
                "chapter": 1,
            }
        ],
    }
    sb = StoryBibleV1.model_validate(_normalize_story_bible(data))
    assert sb.timeline[0].time_label.value == "now"
    assert sb.timeline[0].time_of_day.value == "afternoon"


def test_normalize_coerces_object_lists_to_strings():
    """Second real failure: model emitted full objects where list[str] was expected
    (new_characters / new_locations / foreshadowing_setups / textual_instances)."""
    data = {
        "overall_synopsis": "x",
        "chapter_synopses": [
            {
                "chapter_number": 1,
                "summary": "s1",
                "new_characters": [
                    {"character_id": "c1", "name": "汪淼", "role_type": "protagonist"}
                ],
            },
            {
                "chapter_number": 2,
                "summary": "s2",
                "new_characters": [
                    {"character_id": "c2", "name": "丁仪", "role_type": "supporting"}
                ],
                "new_locations": [
                    {"location_id": "loc-1", "name": "台球厅", "first_chapter": 2, "scenes": []}
                ],
            },
            {
                "chapter_number": 3,
                "summary": "s3",
                "foreshadowing_setups": [
                    {"item_id": "fs-1", "description": "倒计时", "setup_chapter": 1, "payoff_chapter": None}
                ],
            },
        ],
        "themes": [
            {"theme_id": "t1", "name": "n", "description": "d", "textual_instances": [{"quote": "原文片段"}]}
        ],
    }
    sb = StoryBibleV1.model_validate(_normalize_story_bible(data))
    assert sb.chapter_synopses[0].new_characters == ["汪淼"]
    assert sb.chapter_synopses[1].new_characters == ["丁仪"]
    assert sb.chapter_synopses[1].new_locations == ["台球厅"]
    assert sb.chapter_synopses[2].foreshadowing_setups == ["倒计时"]
    assert sb.themes[0].textual_instances == ["原文片段"]  # fallback to first string value
