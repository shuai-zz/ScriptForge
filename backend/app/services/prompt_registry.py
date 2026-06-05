"""PromptTemplate registry for all pipeline stages.

Each stage (0 Bible, 1 Conversion, 2 Assembly) has registered prompts
with variable substitution support.
"""

from dataclasses import dataclass, field
from string import Formatter


@dataclass
class PromptTemplate:
    """A reusable prompt with named variable slots."""

    stage: str
    name: str
    template: str
    required_vars: list[str] = field(default_factory=list)

    def render(self, **variables: str) -> str:
        """Substitute variables into the template.

        Raises KeyError if a required variable is missing.
        """
        # Validate all required vars are present
        for var in self.required_vars:
            if var not in variables:
                raise KeyError(f"Prompt '{self.name}' requires variable '{var}'")
        return self.template.format(**variables)


class PromptRegistry:
    """Central registry for all pipeline prompts."""

    _templates: dict[str, dict[str, PromptTemplate]] = {}

    @classmethod
    def register(cls, template: PromptTemplate) -> None:
        """Register a prompt template."""
        if template.stage not in cls._templates:
            cls._templates[template.stage] = {}
        cls._templates[template.stage][template.name] = template

    @classmethod
    def get(cls, stage: str, name: str) -> PromptTemplate:
        """Retrieve a prompt template by stage and name."""
        if stage not in cls._templates or name not in cls._templates[stage]:
            raise KeyError(f"Prompt not found: stage={stage}, name={name}")
        return cls._templates[stage][name]

    @classmethod
    def list_by_stage(cls, stage: str) -> list[str]:
        """List all prompt names for a given stage."""
        return list(cls._templates.get(stage, {}).keys())

    @classmethod
    def render(cls, stage: str, name: str, **variables: str) -> str:
        """Convenience: get + render in one call."""
        return cls.get(stage, name).render(**variables)


# ── Stage 0: Global Story Bible ──
PromptRegistry.register(
    PromptTemplate(
        stage="stage_0",
        name="bible_generation",
        required_vars=["novel_text"],
        template="""你是一位专业编剧，正在将一部小说改编为剧本。请分析以下小说文本，生成一份结构化的「故事圣经」(Story Bible)。

分析要求：
1. 识别所有有名字的角色（ protagonist / antagonist / supporting / minor 四级分类）
2. 构建角色关系网络（关系类型、强度 1-5、关键节点）
3. 梳理时间线（标注闪回/闪前、时间点、触发事件）
4. 提炼 1-3 个核心主题，每个主题附文本证据和视觉化建议
5. 追踪伏笔（setup/payoff 对）
6. 建立地点索引（首次出现章节、关键道具）
7. 每章摘要（≤5 个关键事件，标注 major/minor/setup/payoff）

请严格按照 story-bible-v1.yaml schema 的 JSON 格式输出。

---

小说全文：
{novel_text}
""",
    )
)

# ── Stage 1: Per-Chapter Conversion ──
PromptRegistry.register(
    PromptTemplate(
        stage="stage_1",
        name="chapter_conversion",
        required_vars=["chapter_text", "story_bible", "previous_script"],
        template="""你是一位专业编剧，正在将小说章节改编为标准剧本格式（YAML）。

输入：
1. 本章原文
2. 故事圣经（全局上下文，含角色档案、关系网络、主题、伏笔状态）
3. 前一章的剧本（保证连续性）

输出要求（严格遵循 script-v1.yaml schema）：
- 每个 scene 必须包含：scene_number, slug（INT./EXT. 地点 - 时间）, summary
- blocks 交替排列：action（视觉动作描述）和 dialogue（角色对白）
- dialogue 必须包含：char_id, char_name, line, parenthetical（可选）
- 每个 block 必须有 source_ref 指向原文章节和段落
- 如果某段内心独白被外化为动作，请添加 annotation（category: inner_to_visual, confidence）
- scene 边界基于：地点变化、时间跳跃、叙事断裂

请只输出 YAML，不要额外解释。

---

故事圣经：
{story_bible}

前一章剧本：
{previous_script}

本章原文：
{chapter_text}
""",
    )
)

# ── Stage 2: Assembly & Validation ──
PromptRegistry.register(
    PromptTemplate(
        stage="stage_2",
        name="assembly",
        required_vars=["chapter_scripts", "story_bible"],
        template="""你是一位剧本统筹，需要将多个章节的场景合并为一部完整的剧本，并进行全局一致性校验。

输入：
1. 所有章节的场景列表（按章节顺序）
2. 故事圣经（角色档案、关系、时间线、伏笔）

任务：
1. 按顺序拼接所有场景，重新分配全局 scene_number（从 1 开始连续递增）
2. 生成 scene_index（每 scene 的 slug, summary, characters, page_estimate）
3. 检查角色一致性：所有 script 中使用的 char_id 必须在角色名册中存在
4. 检查时间线连贯性：相邻 scene 的时间跳跃是否合理（如 night→morning 需要新的一天标记）
5. 检查对白/动作交替：同一 scene 中不允许连续两个同类型 block
6. 生成全局 annotations（ pacing_suggestion, character_consistency 等）

输出严格遵循 script-v1.yaml schema。

---

故事圣经：
{story_bible}

章节场景列表：
{chapter_scripts}
""",
    )
)
