"""LangGraph pipeline nodes — Stage 0, Stage 1, Stage 2, and utilities."""

import json

import yaml
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Send

from app.pipeline.state import ConversionState
from app.schemas.script import Scene, ScriptMetadata, ScriptV1
from app.schemas.story_bible import StoryBibleV1
from app.services.llm_factory import LLMFactoryError, create_chat_model_from_config
from app.services.prompt_registry import PromptRegistry


# ── Stage 0 ──


def validate_input(state: ConversionState) -> dict:
    """Validate pipeline inputs before starting conversion.

    Checks:
      - At least 3 chapters are provided
      - Each chapter has required fields (chapter_number, title, raw_text)
      - Chapter raw_text is non-empty
    """
    errors: list[str] = []
    chapters = state.get("chapters", [])

    if not chapters:
        errors.append("没有提供任何章节。")
    elif len(chapters) < 3:
        errors.append(
            f"章节数量不足：提供了 {len(chapters)} 章，至少需要 3 章。"
        )

    required_fields = {"chapter_number", "title", "raw_text"}
    for idx, ch in enumerate(chapters):
        missing = required_fields - set(ch.keys())
        if missing:
            errors.append(
                f"第 {idx + 1} 个章节缺少必需字段：{', '.join(sorted(missing))}"
            )
            continue

        if not ch.get("raw_text") or not str(ch["raw_text"]).strip():
            errors.append(
                f"第 {ch.get('chapter_number', idx + 1)} 章内容为空。"
            )

    if errors:
        return {
            "errors": errors,
            "status": "failed",
            "progress": {
                "current_stage": "validate_input",
                "percent": 0,
                "message": "输入验证失败",
                "details": {"error_count": len(errors)},
            },
        }

    return {
        "status": "running",
        "progress": {
            "current_stage": "validate_input",
            "percent": 5,
            "message": "输入验证通过",
            "details": {"chapter_count": len(chapters)},
        },
    }


async def stage_0_bible(state: ConversionState, config: RunnableConfig) -> dict:
    """Stage 0: Generate Story Bible from all chapters via LLM.

    Expects provider configs under config["configurable"]["providers"].
    The stage_0 provider is selected via state["provider_assignments"]["stage_0"].
    """
    chapters = state.get("chapters", [])
    provider_id = state.get("provider_assignments", {}).get("stage_0")
    providers = config.get("configurable", {}).get("providers", {})

    provider_cfg = providers.get(provider_id)
    if not provider_cfg:
        return {
            "errors": [f"Stage 0 provider '{provider_id}' not found in config"],
            "status": "failed",
            "progress": {
                "current_stage": "stage_0_bible",
                "percent": 5,
                "message": "Stage 0 启动失败：模型配置缺失",
            },
        }

    # Build novel text
    novel_text = "\n\n".join(
        f"## 第{ch['chapter_number']}章 {ch.get('title', '')}\n\n{ch.get('raw_text', '')}"
        for ch in chapters
    )

    # Render prompt
    try:
        prompt_text = PromptRegistry.render(
            "stage_0", "bible_generation", novel_text=novel_text
        )
    except KeyError as exc:
        return {
            "errors": [f"Prompt error: {exc}"],
            "status": "failed",
            "progress": {
                "current_stage": "stage_0_bible",
                "percent": 5,
                "message": "Prompt 模板错误",
            },
        }

    # Call LLM
    try:
        llm = create_chat_model_from_config(provider_cfg)
        response = await llm.ainvoke([HumanMessage(content=prompt_text)])
        content = str(response.content)
    except LLMFactoryError as exc:
        return {
            "errors": [f"LLM factory error: {exc}"],
            "status": "failed",
            "progress": {
                "current_stage": "stage_0_bible",
                "percent": 5,
                "message": "LLM 初始化失败",
            },
        }
    except Exception as exc:
        return {
            "errors": [f"LLM invocation error: {exc}"],
            "status": "failed",
            "progress": {
                "current_stage": "stage_0_bible",
                "percent": 5,
                "message": "LLM 调用失败",
            },
        }

    # Parse JSON response
    try:
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()

        data = json.loads(json_str)
        story_bible = StoryBibleV1.model_validate(data)
    except Exception as exc:
        return {
            "errors": [f"Failed to parse StoryBible response: {exc}"],
            "status": "failed",
            "progress": {
                "current_stage": "stage_0_bible",
                "percent": 5,
                "message": "故事圣经解析失败",
                "details": {"raw_preview": content[:500]},
            },
        }

    return {
        "story_bible": story_bible.model_dump(),
        "status": "running",
        "progress": {
            "current_stage": "stage_0_bible",
            "percent": 20,
            "message": "故事圣经生成完成",
            "details": {
                "character_count": len(story_bible.character_network.nodes),
                "theme_count": len(story_bible.themes),
            },
        },
    }


def quality_gate_0(state: ConversionState) -> dict:
    """Stage 0 quality gate: verify Story Bible has at least 1 key character.

    Updates quality_checks and retry_counts in state.
    Conditional edges (wired in 5.9) read quality_checks["stage_0"].passed
    to route to retry, human_intervention, or stage_1.
    """
    story_bible = state.get("story_bible")
    retry_counts = state.get("retry_counts", {})
    current_retry = retry_counts.get("stage_0", 0)

    issues: list[str] = []
    passed = False

    if not story_bible:
        issues.append("Story Bible 未生成。")
    else:
        char_network = story_bible.get("character_network", {})
        nodes = char_network.get("nodes", [])
        if len(nodes) < 1:
            issues.append("未识别到任何关键角色（至少需要 1 个）。")
        else:
            passed = True

    new_retry_count = current_retry
    if not passed:
        new_retry_count = current_retry + 1

    next_status = state.get("status", "running")
    if not passed and new_retry_count >= 3:
        next_status = "paused"
        issues.append("Stage 0 质量检查连续 3 次未通过，需要人工干预。")

    return {
        "quality_checks": {
            "stage_0": {
                "passed": passed,
                "issues": issues,
                "retry_count": new_retry_count,
            }
        },
        "retry_counts": {"stage_0": new_retry_count},
        "status": next_status,
        "progress": {
            "current_stage": "quality_gate_0",
            "percent": 22 if passed else 20,
            "message": "Stage 0 质量检查通过" if passed else "Stage 0 质量检查未通过",
            "details": {
                "passed": passed,
                "retry_count": new_retry_count,
                "issues": issues,
            },
        },
    }


# ── Stage 1 ──


def stage_1_splitter(state: ConversionState) -> list[Send]:
    """Split chapters into parallel conversion tasks.

    Returns a Send for each chapter; LangGraph executes them in parallel.
    Each Send injects 'chapter_number' into the sub-node's state.
    """
    return [
        Send("stage_1_chapter", {"chapter_number": ch["chapter_number"]})
        for ch in state.get("chapters", [])
    ]


async def stage_1_chapter(
    state: ConversionState, config: RunnableConfig
) -> dict:
    """Convert a single chapter into script scenes.

    Receives the global state merged with the Send payload (chapter_number).
    Uses Story Bible as shared context and the preceding chapter's script
    for continuity.

    Validates every scene with Pydantic before accepting.
    """
    chapter_number = state.get("chapter_number")
    if chapter_number is None:
        return {
            "errors": ["stage_1_chapter 缺少 chapter_number"],
            "chapter_scripts": {},
        }

    chapters = state.get("chapters", [])
    story_bible = state.get("story_bible", {})
    chapter_scripts = state.get("chapter_scripts", {})

    current_ch = next(
        (c for c in chapters if c["chapter_number"] == chapter_number), None
    )
    if not current_ch:
        return {
            "errors": [f"第 {chapter_number} 章未找到"],
            "chapter_scripts": {},
        }

    # Preceding chapter script as YAML context
    prev_scenes = chapter_scripts.get(str(chapter_number - 1), [])
    previous_script = yaml.safe_dump(prev_scenes, allow_unicode=True) if prev_scenes else ""

    story_bible_yaml = (
        yaml.safe_dump(story_bible, allow_unicode=True) if story_bible else ""
    )
    chapter_text = current_ch.get("raw_text", "")

    # Render prompt
    try:
        prompt_text = PromptRegistry.render(
            "stage_1",
            "chapter_conversion",
            chapter_text=chapter_text,
            story_bible=story_bible_yaml,
            previous_script=previous_script,
        )
    except KeyError as exc:
        return {
            "errors": [f"Prompt error: {exc}"],
            "chapter_scripts": {},
        }

    # Call LLM
    provider_id = state.get("provider_assignments", {}).get("stage_1")
    providers = config.get("configurable", {}).get("providers", {})
    provider_cfg = providers.get(provider_id)

    if not provider_cfg:
        return {
            "errors": [f"Stage 1 provider '{provider_id}' not found"],
            "chapter_scripts": {},
        }

    try:
        llm = create_chat_model_from_config(provider_cfg)
        response = await llm.ainvoke([HumanMessage(content=prompt_text)])
        content = str(response.content)
    except LLMFactoryError as exc:
        return {
            "errors": [f"LLM factory error: {exc}"],
            "chapter_scripts": {},
        }
    except Exception as exc:
        return {
            "errors": [f"LLM invocation error: {exc}"],
            "chapter_scripts": {},
        }

    # Parse YAML response into Scene list
    try:
        yaml_str = content
        if "```yaml" in content:
            yaml_str = content.split("```yaml")[1].split("```")[0].strip()
        elif "```" in content:
            yaml_str = content.split("```")[1].split("```")[0].strip()

        data = yaml.safe_load(yaml_str)
        if isinstance(data, dict) and "scenes" in data:
            scenes_data = data["scenes"]
        elif isinstance(data, list):
            scenes_data = data
        else:
            scenes_data = [data] if data else []

        scenes = [Scene.model_validate(s).model_dump() for s in scenes_data]
    except Exception as exc:
        return {
            "errors": [f"第 {chapter_number} 章场景解析失败: {exc}"],
            "chapter_scripts": {},
        }

    return {
        "chapter_scripts": {str(chapter_number): scenes},
    }


# ── Stage 2 ──


def stage_2_assemble(state: ConversionState) -> dict:
    """Assemble all chapter scenes into a complete screenplay.

    - Concatenates scenes in chapter order
    - Assigns sequential scene_numbers (1, 2, 3...)
    - Generates scene_index entries
    - Builds a ScriptV1 Pydantic model

    Semantic validators (Group 11) are stubbed here; full integration
    will be wired once validators are implemented.
    """
    chapters = state.get("chapters", [])
    chapter_scripts = state.get("chapter_scripts", {})
    story_bible = state.get("story_bible", {})
    project_title = state.get("project_title", "未命名剧本")

    # Collect scenes in chapter order
    all_scenes: list[dict] = []
    for ch in chapters:
        ch_num = str(ch["chapter_number"])
        scenes = chapter_scripts.get(ch_num, [])
        all_scenes.extend(scenes)

    if not all_scenes:
        return {
            "errors": ["组装失败：没有可用的场景。"],
            "status": "failed",
            "progress": {
                "current_stage": "stage_2_assemble",
                "percent": 60,
                "message": "剧本组装失败：无场景数据",
            },
        }

    # Assign sequential scene numbers
    for i, scene in enumerate(all_scenes, start=1):
        scene["scene_number"] = i

    # Build scene_index
    scene_index = []
    for scene in all_scenes:
        slug = scene.get("slug", {})
        slug_line = (
            f"{slug.get('location_type', '')} {slug.get('location_name', '')} - "
            f"{slug.get('time', '')}"
        ).strip()
        scene_index.append(
            {
                "scene_id": scene.get("scene_id", f"scene-{scene['scene_number']}"),
                "scene_number": scene["scene_number"],
                "slug_line": slug_line,
                "summary": scene.get("summary", ""),
                "characters": scene.get("characters_present", []),
            }
        )

    # Build ScriptV1
    try:
        script = ScriptV1(
            metadata=ScriptMetadata(
                title=project_title,
                total_scenes=len(all_scenes),
            ),
            scenes=all_scenes,
            scene_index=scene_index,
        )
    except Exception as exc:
        return {
            "errors": [f"剧本模型验证失败: {exc}"],
            "status": "failed",
            "progress": {
                "current_stage": "stage_2_assemble",
                "percent": 60,
                "message": "剧本组装失败：模型验证错误",
            },
        }

    return {
        "assembled_script": script.model_dump(),
        "status": "running",
        "progress": {
            "current_stage": "stage_2_assemble",
            "percent": 75,
            "message": f"剧本组装完成，共 {len(all_scenes)} 个场景",
            "details": {"scene_count": len(all_scenes)},
        },
    }
