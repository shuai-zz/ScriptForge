"""Semantic validators for screenplay content quality (Phase 11).

Each validator inspects a ScriptV1 object and returns structured findings.
ValidatorRunner orchestrates all validators and produces a ValidationReport.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from app.schemas.script import BlockType, LocationType, ScriptV1, TimeOfDay


class ValidationSeverity(str, Enum):
    """Severity level of a validation finding."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationFinding:
    """A single issue discovered by a validator."""

    validator: str
    severity: ValidationSeverity
    message: str
    scene_id: str | None = None
    scene_number: int | None = None
    block_id: str | None = None
    char_id: str | None = None


@dataclass
class ValidationReport:
    """Aggregated results from running all validators."""

    errors: list[ValidationFinding] = field(default_factory=list)
    warnings: list[ValidationFinding] = field(default_factory=list)
    infos: list[ValidationFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Report passes when there are no errors."""
        return len(self.errors) == 0

    @property
    def all_findings(self) -> list[ValidationFinding]:
        return self.errors + self.warnings + self.infos


class Validator(Protocol):
    """Protocol for screenplay validators."""

    def validate(self, script: ScriptV1) -> list[ValidationFinding]: ...


# ── 11.1 CharacterConsistencyValidator ──


class CharacterConsistencyValidator:
    """Ensure every char_id used in scenes exists in the script character roster."""

    def validate(self, script: ScriptV1) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        known_ids = {c.character_id for c in script.characters}

        for scene in script.scenes:
            # Check characters_present list
            for char_id in scene.characters_present:
                if char_id not in known_ids:
                    findings.append(
                        ValidationFinding(
                            validator=self.__class__.__name__,
                            severity=ValidationSeverity.ERROR,
                            message=f"角色 '{char_id}' 出现在场景中但未在角色名册中注册。",
                            scene_id=scene.scene_id,
                            scene_number=scene.scene_number,
                            char_id=char_id,
                        )
                    )

            # Check dialogue block char_ids
            for block in scene.blocks:
                if block.type == BlockType.DIALOGUE and block.char_id:
                    if block.char_id not in known_ids:
                        findings.append(
                            ValidationFinding(
                                validator=self.__class__.__name__,
                                severity=ValidationSeverity.ERROR,
                                message=f"对白引用了未注册的角色 '{block.char_id}'。",
                                scene_id=scene.scene_id,
                                scene_number=scene.scene_number,
                                block_id=block.block_id,
                                char_id=block.char_id,
                            )
                        )

        return findings


# ── 11.2 DialogueActionAlternationValidator ──


class DialogueActionAlternationValidator:
    """Within a scene, no two consecutive blocks should have the same type."""

    def validate(self, script: ScriptV1) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []

        for scene in script.scenes:
            for i in range(1, len(scene.blocks)):
                prev = scene.blocks[i - 1]
                curr = scene.blocks[i]
                if prev.type == curr.type:
                    findings.append(
                        ValidationFinding(
                            validator=self.__class__.__name__,
                            severity=ValidationSeverity.WARNING,
                            message=f"场景内出现连续的 {curr.type.value} 块（第 {i} 和第 {i + 1} 个）。建议插入不同类型的块以保持节奏。",
                            scene_id=scene.scene_id,
                            scene_number=scene.scene_number,
                            block_id=curr.block_id,
                        )
                    )

        return findings


# ── 11.3 SlugLineValidator ──


class SlugLineValidator:
    """Every scene slug must have a valid location_type, non-empty location_name, and valid time."""

    VALID_LOCATION_TYPES = {lt.value for lt in LocationType}
    VALID_TIMES = {t.value for t in TimeOfDay}

    def validate(self, script: ScriptV1) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []

        for scene in script.scenes:
            slug = scene.slug
            if slug.location_type not in self.VALID_LOCATION_TYPES:
                findings.append(
                    ValidationFinding(
                        validator=self.__class__.__name__,
                        severity=ValidationSeverity.ERROR,
                        message=f"无效的场景地点前缀: '{slug.location_type}'。应为 INT./EXT./INT./EXT.。",
                        scene_id=scene.scene_id,
                        scene_number=scene.scene_number,
                    )
                )

            if not slug.location_name or not str(slug.location_name).strip():
                findings.append(
                    ValidationFinding(
                        validator=self.__class__.__name__,
                        severity=ValidationSeverity.ERROR,
                        message="场景地点名称为空。",
                        scene_id=scene.scene_id,
                        scene_number=scene.scene_number,
                    )
                )

            if slug.time not in self.VALID_TIMES:
                findings.append(
                    ValidationFinding(
                        validator=self.__class__.__name__,
                        severity=ValidationSeverity.ERROR,
                        message=f"无效的时间标记: '{slug.time}'。",
                        scene_id=scene.scene_id,
                        scene_number=scene.scene_number,
                    )
                )

        return findings


# ── 11.4 SceneNumberContinuityValidator ──


class SceneNumberContinuityValidator:
    """Scene numbers must start at 1 and increment consecutively without gaps or duplicates."""

    def validate(self, script: ScriptV1) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        scenes = script.scenes
        if not scenes:
            return findings

        numbers = [s.scene_number for s in scenes]
        sorted_numbers = sorted(numbers)

        # Check starts at 1
        if sorted_numbers[0] != 1:
            findings.append(
                ValidationFinding(
                    validator=self.__class__.__name__,
                    severity=ValidationSeverity.ERROR,
                    message=f"场景编号未从 1 开始（首个编号为 {sorted_numbers[0]}）。",
                )
            )

        # Check consecutiveness
        for i in range(1, len(sorted_numbers)):
            if sorted_numbers[i] != sorted_numbers[i - 1] + 1:
                findings.append(
                    ValidationFinding(
                        validator=self.__class__.__name__,
                        severity=ValidationSeverity.ERROR,
                        message=f"场景编号不连续：{sorted_numbers[i - 1]} 之后直接跳到 {sorted_numbers[i]}。",
                    )
                )

        # Check duplicates
        seen = set()
        for s in scenes:
            if s.scene_number in seen:
                findings.append(
                    ValidationFinding(
                        validator=self.__class__.__name__,
                        severity=ValidationSeverity.ERROR,
                        message=f"场景编号重复: #{s.scene_number}。",
                        scene_id=s.scene_id,
                        scene_number=s.scene_number,
                    )
                )
            seen.add(s.scene_number)

        return findings


# ── 11.5 TimelineCoherenceValidator ──


class TimelineCoherenceValidator:
    """Flag implausible time jumps between adjacent scenes, especially at the same location."""

    # Time progression that typically implies a new day / large gap
    IMPLAUSIBLE_SAME_LOCATION_JUMPS: set[tuple[str, str]] = {
        ("NIGHT", "MORNING"),
        ("NIGHT", "DAY"),
        ("NIGHT", "AFTERNOON"),
        ("EVENING", "MORNING"),
        ("EVENING", "DAY"),
        ("MORNING", "NIGHT"),
        ("DAY", "NIGHT"),
        ("AFTERNOON", "NIGHT"),
        ("DAWN", "NIGHT"),
        ("DUSK", "MORNING"),
        ("DUSK", "DAY"),
    }

    def validate(self, script: ScriptV1) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        scenes = script.scenes

        for i in range(1, len(scenes)):
            prev = scenes[i - 1]
            curr = scenes[i]
            prev_slug = prev.slug
            curr_slug = curr.slug

            same_location = (
                prev_slug.location_type == curr_slug.location_type
                and prev_slug.location_name == curr_slug.location_name
            )

            time_pair = (prev_slug.time, curr_slug.time)
            if time_pair in self.IMPLAUSIBLE_SAME_LOCATION_JUMPS:
                severity = (
                    ValidationSeverity.WARNING
                    if same_location
                    else ValidationSeverity.INFO
                )
                location_note = "同一地点" if same_location else "不同地点"
                findings.append(
                    ValidationFinding(
                        validator=self.__class__.__name__,
                        severity=severity,
                        message=(
                            f"时间跳跃可能不合理（{location_note}）："
                            f"场景 {prev.scene_number} ({prev_slug.time}) → "
                            f"场景 {curr.scene_number} ({curr_slug.time})。"
                            f"建议添加过渡场景或时间标记。"
                        ),
                        scene_id=curr.scene_id,
                        scene_number=curr.scene_number,
                    )
                )

        return findings


# ── 11.6 CharacterAppearanceValidator ──


class CharacterAppearanceValidator:
    """Protagonist-type characters must appear in at least 20% of scenes."""

    MIN_PROTAGONIST_RATIO = 0.20

    def validate(self, script: ScriptV1) -> list[ValidationFinding]:
        findings: list[ValidationFinding] = []
        total_scenes = len(script.scenes)
        if total_scenes == 0:
            return findings

        # Count appearances per character
        appearance_counts: dict[str, int] = {}
        for scene in script.scenes:
            seen_in_scene: set[str] = set(scene.characters_present)
            for block in scene.blocks:
                if block.type == BlockType.DIALOGUE and block.char_id:
                    seen_in_scene.add(block.char_id)
            for char_id in seen_in_scene:
                appearance_counts[char_id] = appearance_counts.get(char_id, 0) + 1

        # Check protagonists
        for char in script.characters:
            if char.role_type.value == "protagonist":
                count = appearance_counts.get(char.character_id, 0)
                ratio = count / total_scenes
                if ratio < self.MIN_PROTAGONIST_RATIO:
                    findings.append(
                        ValidationFinding(
                            validator=self.__class__.__name__,
                            severity=ValidationSeverity.WARNING,
                            message=(
                                f"主角 '{char.name}' 出场率过低："
                                f"{count}/{total_scenes} 场景（{ratio:.0%}），"
                                f"建议至少 {self.MIN_PROTAGONIST_RATIO:.0%}。"
                            ),
                            char_id=char.character_id,
                        )
                    )

        return findings


# ── 11.7 ValidatorRunner ──


DEFAULT_VALIDATORS: list[Validator] = [
    CharacterConsistencyValidator(),
    DialogueActionAlternationValidator(),
    SlugLineValidator(),
    SceneNumberContinuityValidator(),
    TimelineCoherenceValidator(),
    CharacterAppearanceValidator(),
]


class ValidatorRunner:
    """Orchestrate all validators and aggregate findings into a ValidationReport."""

    def __init__(self, validators: list[Validator] | None = None) -> None:
        self.validators = validators or DEFAULT_VALIDATORS

    def run(self, script: ScriptV1) -> ValidationReport:
        """Run all validators against the given script."""
        report = ValidationReport()
        for validator in self.validators:
            for finding in validator.validate(script):
                if finding.severity == ValidationSeverity.ERROR:
                    report.errors.append(finding)
                elif finding.severity == ValidationSeverity.WARNING:
                    report.warnings.append(finding)
                else:
                    report.infos.append(finding)
        return report
