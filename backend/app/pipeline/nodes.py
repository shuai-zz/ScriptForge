"""LangGraph pipeline nodes — Stage 0, Stage 1, Stage 2, and utilities."""

from app.pipeline.state import ConversionState


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
