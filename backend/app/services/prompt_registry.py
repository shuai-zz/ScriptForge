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

请**只输出一个 JSON 对象**（不要 markdown 代码块、不要任何解释文字），严格使用下列字段名与结构：

{{
  "overall_synopsis": "<整部作品的整体剧情概要，一段话>",
  "chapter_synopses": [
    {{"chapter_number": 1, "summary": "<本章摘要>", "key_events": [{{"description": "<关键事件>", "significance": "major"}}], "new_characters": [], "new_locations": [], "foreshadowing_setups": [], "foreshadowing_payoffs": []}}
  ],
  "character_network": {{
    "nodes": [{{"character_id": "c1", "name": "<角色名>", "role_type": "protagonist"}}],
    "edges": [{{"source": "c1", "target": "c2", "type": "friend", "intensity": 3, "key_moments": []}}]
  }},
  "timeline": [
    {{"event_id": "evt-1", "time_label": "now", "description": "<事件描述>", "time_of_day": "afternoon", "duration": null, "trigger_events": [], "chapter": 1}}
  ],
  "themes": [
    {{"theme_id": "theme-1", "name": "<主题名>", "description": "<主题阐述>", "textual_instances": [], "visual_motifs": []}}
  ],
  "foreshadowing_tracking": [
    {{"item_id": "fs-1", "setup_chapter": 1, "description": "<伏笔描述>", "status": "unresolved", "payoff_chapter": null}}
  ],
  "location_index": [
    {{"location_id": "loc-1", "name": "<地点名>", "description": "<描述>", "key_props": [], "first_chapter": 1, "scenes": []}}
  ]
}}

字段取值约束（务必遵守，否则解析会失败）：
- overall_synopsis：必填，不可省略。
- role_type ∈ protagonist | antagonist | supporting | minor
- edges.type ∈ lover | family | friend | rival | mentor | enemy | colleague | other；intensity 为 1-5 的整数
- time_label ∈ now | flashback | flashforward
- time_of_day ∈ dawn | morning | afternoon | dusk | evening | night | midnight
- significance ∈ major | minor | setup | payoff
- status ∈ unresolved | resolved
- 所有 chapter / chapter_number / setup_chapter / payoff_chapter / first_chapter 必须是**整数**（例如 1、2、3），不要写「第1章」之类的字符串。
- 每个 timeline 事件必须含 event_id、time_label、description、time_of_day、chapter；每个 theme 必须含 theme_id、name、description。
- 以下列表的元素都是**字符串**（名称或简短描述），不要放对象/字典：new_characters、new_locations、foreshadowing_setups、foreshadowing_payoffs、textual_instances、visual_motifs、trigger_events、key_moments、key_props、scenes。

分析要求：
1. 识别所有有名字的角色并分级（protagonist/antagonist/supporting/minor），构建角色关系网络。
2. 梳理时间线（标注闪回/闪前、时间点、触发事件）。
3. 提炼 1-3 个核心主题，每个附文本证据和视觉化建议。
4. 追踪伏笔（setup/payoff 对）、建立地点索引、每章摘要（≤5 个关键事件）。

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
        template="""你是一位专业编剧，正在将小说章节改编为标准剧本格式。

输入：本章原文、故事圣经（全局上下文，含角色档案/关系/主题/伏笔）、前一章剧本（保证连续性）。

**只输出 YAML**（不要额外解释），严格使用下列结构与字段名：

scenes:
  - scene_id: "sc-1"            # 必填，唯一字符串
    scene_number: 1             # 必填，整数
    slug:                       # 必填，必须是对象（不是字符串！）
      location_type: "INT."     # 取值：INT. | EXT. | INT./EXT.
      location_name: "汪淼家客厅"
      time: "NIGHT"             # 取值：DAY|NIGHT|DAWN|DUSK|MORNING|AFTERNOON|EVENING|LATER|CONTINUOUS|SAME TIME
    summary: "场景简述"
    characters_present: ["c1"]  # 角色 id 列表（来自故事圣经名册）
    props: []
    blocks:                     # 必填，action 与 dialogue 交替
      - block_id: "b-1"         # 每个 block 必填，唯一
        order: 0                # 每个 block 必填，从 0 起的整数
        type: "action"          # 取值：action | dialogue
        text: "视觉动作描述"
        source_ref: {{chapter: 1, paragraph: 3, quote: "原文引用"}}
      - block_id: "b-2"
        order: 1
        type: "dialogue"
        char_id: "c1"
        char_name: "汪淼"
        line: "对白内容"
        parenthetical: "（颤抖）"   # 可选
    annotations: []

硬性要求：
- slug 必须是对象（含 location_type / location_name / time 三个字段），**严禁写成 "INT. 地点 - 时间" 这样的字符串**。
- 每个 scene 必须有 scene_id；每个 block 必须有 block_id 和 order（从 0 递增的整数）。
- location_type 与 time 必须使用上面列出的英文枚举值（不要用中文）。
- char_id 必须来自故事圣经的角色名册；scene 边界基于地点变化 / 时间跳跃 / 叙事断裂。
- **完整性约束（务必遵守）：**
  1. 你必须覆盖本章原文中的**所有关键情节**和**所有地点变化**，不能遗漏或跳过任何一段重要叙事。
  2. 如果本章原文涉及多个不同地点，你必须为**每个地点变化**生成独立的 scene，严禁合并到同一个 scene 中。
  3. 每个 block 必须包含 `source_ref`，其中 `chapter` 必须等于本章编号，`paragraph` 尽量标注对应的原文段落序号，`quote` 摘录对应的原文句子（不少于 10 字）。这用于后续校验章节内容是否丢失。

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
