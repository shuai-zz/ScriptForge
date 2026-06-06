"""Unit tests for semantic validators (Phase 11.1–11.8)."""

import pytest

from app.schemas.script import (
    BlockType,
    LocationType,
    RoleType,
    ScriptBlock,
    ScriptCharacter,
    ScriptMetadata,
    ScriptV1,
    Slug,
    TimeOfDay,
)
from app.services.validators import (
    CharacterAppearanceValidator,
    CharacterConsistencyValidator,
    DialogueActionAlternationValidator,
    SceneNumberContinuityValidator,
    SlugLineValidator,
    TimelineCoherenceValidator,
    ValidationSeverity,
    ValidatorRunner,
)


# ── Helpers ──


def _make_script(**kwargs) -> ScriptV1:
    """Build a minimal valid script for testing."""
    defaults = {
        "schema_version": "1.0",
        "schema_name": "scriptforge-script",
        "metadata": ScriptMetadata(title="Test", total_scenes=0, estimated_runtime=0),
        "characters": [],
        "scenes": [],
        "scene_index": [],
        "global_annotations": [],
    }
    defaults.update(kwargs)
    return ScriptV1(**defaults)


def _make_scene(number: int, **kwargs) -> dict:
    defaults = {
        "scene_id": f"s{number}",
        "scene_number": number,
        "slug": Slug(location_type=LocationType.INT, location_name="Room", time=TimeOfDay.DAY),
        "summary": "",
        "characters_present": [],
        "props": [],
        "blocks": [],
        "annotations": [],
    }
    defaults.update(kwargs)
    return defaults


def _make_block(block_type: BlockType, **kwargs) -> dict:
    defaults = {
        "block_id": f"b{kwargs.get('order', 0)}",
        "order": kwargs.get("order", 0),
        "type": block_type,
        "annotation_refs": [],
    }
    if block_type == BlockType.ACTION:
        defaults["text"] = kwargs.get("text", "Action text.")
    else:
        defaults["char_id"] = kwargs.get("char_id", "c1")
        defaults["char_name"] = kwargs.get("char_name", "Alice")
        defaults["line"] = kwargs.get("line", "Hello.")
        defaults["parenthetical"] = kwargs.get("parenthetical", None)
    defaults.update(kwargs)
    return defaults


# ── 11.1 CharacterConsistencyValidator ──


class TestCharacterConsistencyValidator:
    def test_valid_passes(self):
        script = _make_script(
            characters=[
                ScriptCharacter(character_id="c1", name="Alice", role_type=RoleType.PROTAGONIST),
            ],
            scenes=[
                _make_scene(1, characters_present=["c1"], blocks=[_make_block(BlockType.DIALOGUE, char_id="c1")]),
            ],
        )
        v = CharacterConsistencyValidator()
        findings = v.validate(script)
        assert len(findings) == 0

    def test_orphan_char_id_in_dialogue(self):
        script = _make_script(
            characters=[
                ScriptCharacter(character_id="c1", name="Alice", role_type=RoleType.PROTAGONIST),
            ],
            scenes=[
                _make_scene(1, blocks=[_make_block(BlockType.DIALOGUE, char_id="c99")]),
            ],
        )
        v = CharacterConsistencyValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.ERROR
        assert "c99" in findings[0].message

    def test_orphan_in_characters_present(self):
        script = _make_script(
            characters=[],
            scenes=[
                _make_scene(1, characters_present=["ghost"]),
            ],
        )
        v = CharacterConsistencyValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.ERROR
        assert "ghost" in findings[0].message

    def test_empty_script_passes(self):
        script = _make_script()
        v = CharacterConsistencyValidator()
        findings = v.validate(script)
        assert len(findings) == 0


# ── 11.2 DialogueActionAlternationValidator ──


class TestDialogueActionAlternationValidator:
    def test_alternating_passes(self):
        script = _make_script(
            scenes=[
                _make_scene(
                    1,
                    blocks=[
                        _make_block(BlockType.ACTION, order=0),
                        _make_block(BlockType.DIALOGUE, order=1),
                        _make_block(BlockType.ACTION, order=2),
                    ],
                ),
            ],
        )
        v = DialogueActionAlternationValidator()
        findings = v.validate(script)
        assert len(findings) == 0

    def test_back_to_back_action(self):
        script = _make_script(
            scenes=[
                _make_scene(
                    1,
                    blocks=[
                        _make_block(BlockType.ACTION, order=0),
                        _make_block(BlockType.ACTION, order=1),
                    ],
                ),
            ],
        )
        v = DialogueActionAlternationValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.WARNING
        assert "action" in findings[0].message

    def test_back_to_back_dialogue(self):
        script = _make_script(
            scenes=[
                _make_scene(
                    1,
                    blocks=[
                        _make_block(BlockType.DIALOGUE, order=0),
                        _make_block(BlockType.DIALOGUE, order=1),
                    ],
                ),
            ],
        )
        v = DialogueActionAlternationValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.WARNING
        assert "dialogue" in findings[0].message

    def test_single_block_passes(self):
        script = _make_script(
            scenes=[_make_scene(1, blocks=[_make_block(BlockType.ACTION, order=0)])],
        )
        v = DialogueActionAlternationValidator()
        findings = v.validate(script)
        assert len(findings) == 0

    def test_empty_scene_passes(self):
        script = _make_script(scenes=[_make_scene(1, blocks=[])])
        v = DialogueActionAlternationValidator()
        findings = v.validate(script)
        assert len(findings) == 0


# ── 11.3 SlugLineValidator ──


class TestSlugLineValidator:
    def test_valid_slug_passes(self):
        script = _make_script(
            scenes=[
                _make_scene(1, slug=Slug(location_type=LocationType.INT, location_name="Room", time=TimeOfDay.DAY)),
                _make_scene(2, slug=Slug(location_type=LocationType.EXT, location_name="Street", time=TimeOfDay.NIGHT)),
            ],
        )
        v = SlugLineValidator()
        findings = v.validate(script)
        assert len(findings) == 0

    def test_invalid_location_type(self):
        # Bypass Pydantic enum validation to test the validator itself
        bad_slug = Slug.model_construct(location_type="INVALID", location_name="Room", time=TimeOfDay.DAY)
        script = _make_script(
            scenes=[
                _make_scene(1, slug=bad_slug),
            ],
        )
        v = SlugLineValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.ERROR
        assert "地点前缀" in findings[0].message

    def test_empty_location_name(self):
        script = _make_script(
            scenes=[
                _make_scene(1, slug=Slug(location_type=LocationType.INT, location_name="", time=TimeOfDay.DAY)),
            ],
        )
        v = SlugLineValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.ERROR
        assert "名称为空" in findings[0].message

    def test_invalid_time(self):
        bad_slug = Slug.model_construct(location_type=LocationType.INT, location_name="Room", time="NOON")
        script = _make_script(
            scenes=[
                _make_scene(1, slug=bad_slug),
            ],
        )
        v = SlugLineValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.ERROR
        assert "时间标记" in findings[0].message


# ── 11.4 SceneNumberContinuityValidator ──


class TestSceneNumberContinuityValidator:
    def test_consecutive_passes(self):
        script = _make_script(
            scenes=[
                _make_scene(1),
                _make_scene(2),
                _make_scene(3),
            ],
        )
        v = SceneNumberContinuityValidator()
        findings = v.validate(script)
        assert len(findings) == 0

    def test_starts_at_2(self):
        script = _make_script(
            scenes=[
                _make_scene(2),
                _make_scene(3),
            ],
        )
        v = SceneNumberContinuityValidator()
        findings = v.validate(script)
        assert any("未从 1 开始" in f.message for f in findings)

    def test_gap(self):
        script = _make_script(
            scenes=[
                _make_scene(1),
                _make_scene(3),
            ],
        )
        v = SceneNumberContinuityValidator()
        findings = v.validate(script)
        assert any("不连续" in f.message for f in findings)

    def test_duplicate(self):
        script = _make_script(
            scenes=[
                _make_scene(1),
                _make_scene(1),
            ],
        )
        v = SceneNumberContinuityValidator()
        findings = v.validate(script)
        assert any("重复" in f.message for f in findings)

    def test_single_scene_passes(self):
        script = _make_script(scenes=[_make_scene(1)])
        v = SceneNumberContinuityValidator()
        findings = v.validate(script)
        assert len(findings) == 0

    def test_empty_script_passes(self):
        script = _make_script()
        v = SceneNumberContinuityValidator()
        findings = v.validate(script)
        assert len(findings) == 0


# ── 11.5 TimelineCoherenceValidator ──


class TestTimelineCoherenceValidator:
    def test_reasonable_transition_passes(self):
        script = _make_script(
            scenes=[
                _make_scene(1, slug=Slug(location_type=LocationType.INT, location_name="Room", time=TimeOfDay.DAY)),
                _make_scene(2, slug=Slug(location_type=LocationType.INT, location_name="Room", time=TimeOfDay.EVENING)),
            ],
        )
        v = TimelineCoherenceValidator()
        findings = v.validate(script)
        assert len(findings) == 0

    def test_night_to_day_same_location(self):
        script = _make_script(
            scenes=[
                _make_scene(1, slug=Slug(location_type=LocationType.INT, location_name="Room", time=TimeOfDay.NIGHT)),
                _make_scene(2, slug=Slug(location_type=LocationType.INT, location_name="Room", time=TimeOfDay.DAY)),
            ],
        )
        v = TimelineCoherenceValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.WARNING
        assert "同一地点" in findings[0].message

    def test_night_to_day_different_location(self):
        script = _make_script(
            scenes=[
                _make_scene(1, slug=Slug(location_type=LocationType.INT, location_name="Room A", time=TimeOfDay.NIGHT)),
                _make_scene(2, slug=Slug(location_type=LocationType.EXT, location_name="Street", time=TimeOfDay.DAY)),
            ],
        )
        v = TimelineCoherenceValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.INFO
        assert "不同地点" in findings[0].message

    def test_single_scene_passes(self):
        script = _make_script(scenes=[_make_scene(1)])
        v = TimelineCoherenceValidator()
        findings = v.validate(script)
        assert len(findings) == 0


# ── 11.6 CharacterAppearanceValidator ──


class TestCharacterAppearanceValidator:
    def test_protagonist_above_threshold_passes(self):
        script = _make_script(
            characters=[
                ScriptCharacter(character_id="c1", name="Alice", role_type=RoleType.PROTAGONIST),
            ],
            scenes=[
                _make_scene(1, characters_present=["c1"]),
                _make_scene(2, characters_present=["c1"]),
                _make_scene(3, characters_present=["c1"]),
                _make_scene(4, characters_present=["c1"]),
                _make_scene(5, characters_present=["c1"]),
            ],
        )
        v = CharacterAppearanceValidator()
        findings = v.validate(script)
        assert len(findings) == 0

    def test_protagonist_below_threshold(self):
        script = _make_script(
            characters=[
                ScriptCharacter(character_id="c1", name="Alice", role_type=RoleType.PROTAGONIST),
            ],
            scenes=[
                _make_scene(1),
                _make_scene(2),
                _make_scene(3),
                _make_scene(4),
                _make_scene(5),
            ],
        )
        v = CharacterAppearanceValidator()
        findings = v.validate(script)
        assert len(findings) == 1
        assert findings[0].severity == ValidationSeverity.WARNING
        assert "出场率过低" in findings[0].message

    def test_non_protagonist_ignored(self):
        script = _make_script(
            characters=[
                ScriptCharacter(character_id="c1", name="Bob", role_type=RoleType.SUPPORTING),
            ],
            scenes=[_make_scene(1)],
        )
        v = CharacterAppearanceValidator()
        findings = v.validate(script)
        assert len(findings) == 0

    def test_empty_script_passes(self):
        script = _make_script()
        v = CharacterAppearanceValidator()
        findings = v.validate(script)
        assert len(findings) == 0


# ── 11.7 ValidatorRunner ──


class TestValidatorRunner:
    def test_valid_script_passes(self):
        script = _make_script(
            characters=[
                ScriptCharacter(character_id="c1", name="Alice", role_type=RoleType.PROTAGONIST),
            ],
            scenes=[
                _make_scene(
                    1,
                    characters_present=["c1"],
                    blocks=[
                        _make_block(BlockType.ACTION, order=0),
                        _make_block(BlockType.DIALOGUE, order=1, char_id="c1"),
                    ],
                ),
            ],
        )
        runner = ValidatorRunner()
        report = runner.run(script)
        assert report.passed
        assert len(report.errors) == 0
        assert len(report.warnings) == 0

    def test_mixed_issues(self):
        script = _make_script(
            characters=[
                ScriptCharacter(character_id="c1", name="Alice", role_type=RoleType.PROTAGONIST),
            ],
            scenes=[
                _make_scene(
                    1,
                    blocks=[
                        _make_block(BlockType.ACTION, order=0),
                        _make_block(BlockType.ACTION, order=1),  # warning: back-to-back action
                        _make_block(BlockType.DIALOGUE, order=2, char_id="ghost"),  # error: orphan char
                    ],
                ),
            ],
        )
        runner = ValidatorRunner()
        report = runner.run(script)
        assert not report.passed
        assert len(report.errors) >= 1
        assert len(report.warnings) >= 1
        assert any("ghost" in f.message for f in report.errors)
        assert any("action" in f.message for f in report.warnings)

    def test_custom_validators(self):
        script = _make_script()
        runner = ValidatorRunner(validators=[])
        report = runner.run(script)
        assert report.passed
