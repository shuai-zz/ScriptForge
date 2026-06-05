"""Unit tests for all 5 YAML Schema Pydantic models (Task 2.8).

Coverage:
- Valid YAML examples pass validation
- Malformed YAML raises ValidationError
- Edge cases: empty lists, missing required fields, out-of-range values
"""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from app.schemas import (
    AnnotationV1,
    CharacterV1,
    ProjectConfigV1,
    ScriptV1,
    StoryBibleV1,
)
from app.schemas.annotation import Severity, AnnotationCategory
from app.schemas.character import RoleType, VocabularyLevel
from app.schemas.project_config import ProviderType, TargetFormat
from app.schemas.script import LocationType, TimeOfDay, BlockType

YAML_DIR = Path(__file__).parent.parent / "app" / "schemas" / "yaml"


def load_yaml(name: str):
    with open(YAML_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ──────────────────────────────────────────────
# 2.8.1  Valid YAML examples pass
# ──────────────────────────────────────────────


class TestValidExamples:
    """All 5 YAML examples should validate cleanly."""

    def test_script_v1(self):
        data = load_yaml("script-v1.yaml")
        model = ScriptV1.model_validate(data)
        assert model.schema_version == "1.0"
        assert model.metadata.title == "长夜将明"
        assert len(model.scenes) == 1
        assert model.scenes[0].slug.location_type == LocationType.INT

    def test_character_v1(self):
        data = load_yaml("character-v1.yaml")
        model = CharacterV1.model_validate(data)
        assert model.character_id == "char-001"
        assert model.story_role.type == RoleType.PROTAGONIST
        assert model.voice.vocabulary_level == VocabularyLevel.CASUAL

    def test_story_bible_v1(self):
        data = load_yaml("story-bible-v1.yaml")
        model = StoryBibleV1.model_validate(data)
        assert model.schema_version == "1.0"
        assert len(model.chapter_synopses) == 2
        assert len(model.character_network.edges) == 2

    def test_project_config_v1(self):
        data = load_yaml("project-config-v1.yaml")
        model = ProjectConfigV1.model_validate(data)
        assert model.schema_version == "1.0"
        assert len(model.llm_providers) == 2
        assert model.conversion_params.target_format == TargetFormat.MOVIE

    def test_annotation_v1(self):
        data = load_yaml("annotation-v1.yaml")
        model = AnnotationV1.model_validate(data)
        assert model.annotation_id == "ann-001"
        assert model.severity == Severity.WARNING
        assert model.category == AnnotationCategory.INNER_TO_VISUAL
        assert model.confidence == 0.85


# ──────────────────────────────────────────────
# 2.8.2  Malformed / invalid data raises ValidationError
# ──────────────────────────────────────────────


class TestInvalidData:
    """Validation should reject bad data with clear errors."""

    def test_script_missing_required_metadata_title(self):
        with pytest.raises(ValidationError) as exc:
            ScriptV1.model_validate({
                "schema_version": "1.0",
                "metadata": {},  # missing title
                "scenes": [],
            })
        assert "title" in str(exc.value)

    def test_character_invalid_role_type(self):
        with pytest.raises(ValidationError) as exc:
            CharacterV1.model_validate({
                "character_id": "c1",
                "name": "Test",
                "story_role": {"type": "hero"},  # invalid enum
            })
        assert "hero" in str(exc.value)

    def test_project_config_invalid_temperature(self):
        with pytest.raises(ValidationError) as exc:
            ProjectConfigV1.model_validate({
                "llm_providers": [{
                    "provider_id": "p1",
                    "label": "Test",
                    "provider_type": "anthropic",
                    "model_name": "test",
                    "encrypted_api_key": "x",
                    "parameters": {"temperature": 3.0},  # > 2.0
                }],
            })
        assert "temperature" in str(exc.value)

    def test_annotation_confidence_out_of_range(self):
        with pytest.raises(ValidationError) as exc:
            AnnotationV1.model_validate({
                "annotation_id": "a1",
                "severity": "info",
                "category": "format_mismatch",
                "target_reference": {"type": "global"},
                "title": "T",
                "description": "D",
                "confidence": 1.5,  # > 1.0
            })
        assert "confidence" in str(exc.value)

    def test_story_bible_invalid_event_significance(self):
        with pytest.raises(ValidationError) as exc:
            StoryBibleV1.model_validate({
                "overall_synopsis": "Test",
                "chapter_synopses": [{
                    "chapter_number": 1,
                    "summary": "S",
                    "key_events": [{"description": "E", "significance": "huge"}],  # invalid
                }],
            })
        assert "huge" in str(exc.value)


# ──────────────────────────────────────────────
# 2.8.3  Edge cases
# ──────────────────────────────────────────────


class TestEdgeCases:
    """Boundary and degenerate cases."""

    def test_script_empty_character_list(self):
        """A script with zero characters should still validate (e.g. early draft)."""
        model = ScriptV1.model_validate({
            "metadata": {"title": "Empty"},
            "characters": [],
            "scenes": [],
        })
        assert model.characters == []
        assert model.scenes == []

    def test_character_empty_relationships(self):
        """A lone-wolf character with no relationships."""
        model = CharacterV1.model_validate({
            "character_id": "loner",
            "name": "独行侠",
            "story_role": {"type": "protagonist"},
            "relationships": [],
        })
        assert model.relationships == []

    def test_project_config_no_providers(self):
        """Project created before any LLM provider is configured."""
        model = ProjectConfigV1.model_validate({
            "conversion_params": {"target_format": "movie"},
        })
        assert model.llm_providers == []

    def test_annotation_zero_confidence(self):
        """Confidence exactly 0.0 is valid (complete guess)."""
        model = AnnotationV1.model_validate({
            "annotation_id": "a0",
            "severity": "suggestion",
            "category": "adaptation_decision",
            "target_reference": {"type": "global"},
            "title": "Guess",
            "description": "Not sure",
            "confidence": 0.0,
        })
        assert model.confidence == 0.0

    def test_annotation_no_alternatives(self):
        """Annotation with no alternatives (AI only saw one viable path)."""
        model = AnnotationV1.model_validate({
            "annotation_id": "a1",
            "severity": "info",
            "category": "pacing_suggestion",
            "target_reference": {"type": "global"},
            "title": "Note",
            "description": "Just a note",
            "confidence": 0.5,
            "alternatives": [],
        })
        assert model.alternatives == []

    def test_story_bible_empty_timeline(self):
        """Story bible for a very short story with no complex timeline."""
        model = StoryBibleV1.model_validate({
            "overall_synopsis": "Short story",
            "timeline": [],
            "themes": [],
        })
        assert model.timeline == []

    def test_script_block_order_zero(self):
        """First block in a scene has order 0."""
        model = ScriptV1.model_validate({
            "metadata": {"title": "T"},
            "scenes": [{
                "scene_id": "s1",
                "scene_number": 1,
                "slug": {"location_type": "INT.", "location_name": "Room", "time": "DAY"},
                "blocks": [{"block_id": "b1", "order": 0, "type": "action", "text": "Test"}],
            }],
        })
        assert model.scenes[0].blocks[0].order == 0

    def test_character_intensity_boundary(self):
        """Relationship intensity at exact boundaries 1 and 5."""
        for intensity in (1, 5):
            model = CharacterV1.model_validate({
                "character_id": "c1",
                "name": "Test",
                "story_role": {"type": "supporting"},
                "relationships": [{
                    "target_char_id": "c2",
                    "type": "friend",
                    "intensity": intensity,
                }],
            })
            assert model.relationships[0].intensity == intensity
