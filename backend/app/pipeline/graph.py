"""LangGraph StateGraph builder for the AI conversion pipeline.

Topology:
  validate_input -> stage_0_bible -> quality_gate_0
  quality_gate_0 --(pass)-> stage_1_splitter --[Send]-> stage_1_chapter (parallel)
  stage_1_chapter -> stage_2_assemble -> quality_gate_2 -> format_output -> END
  quality_gate_0 --(fail/retry)-> stage_0_bible
  quality_gate_0 --(fail/max retry)-> END
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Send

from app.pipeline.nodes import (
    format_output,
    quality_gate_0,
    quality_gate_2,
    stage_0_bible,
    stage_1_chapter,
    stage_1_splitter,
    stage_2_assemble,
    validate_input,
)
from app.pipeline.state import ConversionState


# ── Conditional edge routers ──


def _route_stage_0(state: ConversionState) -> str:
    """Route from quality_gate_0 based on check result and retry count."""
    qc = state.get("quality_checks", {}).get("stage_0", {})
    if qc.get("passed"):
        return "stage_1_splitter"

    retry = state.get("retry_counts", {}).get("stage_0", 0)
    if retry < 3:
        return "stage_0_bible"
    return END


def _route_stage_1(state: ConversionState) -> list[Send]:
    """Map chapters into parallel stage_1_chapter tasks."""
    return [
        Send("stage_1_chapter", {"chapter_number": ch["chapter_number"]})
        for ch in state.get("chapters", [])
    ]


def _route_stage_2(state: ConversionState) -> str:
    """Route from quality_gate_2.

    Even when issues are flagged, we proceed to format_output so the
    user receives the script plus annotations. The issues are stored
    in state['quality_checks']['stage_2']['issues'].
    """
    return "format_output"


# ── Graph builder ──


def build_conversion_graph(checkpointer: MemorySaver | None = None) -> StateGraph:
    """Build and compile the conversion StateGraph.

    Args:
        checkpointer: LangGraph checkpointer for checkpoint persistence.
                      Defaults to MemorySaver (in-memory; suitable for
                      dev/testing). For production use AsyncPostgresSaver.

    Returns:
        Compiled StateGraph ready for ``ainvoke()`` or ``astream()``.
    """
    builder = StateGraph(ConversionState)

    # Nodes
    builder.add_node("validate_input", validate_input)
    builder.add_node("stage_0_bible", stage_0_bible)
    builder.add_node("quality_gate_0", quality_gate_0)
    builder.add_node("stage_1_splitter", stage_1_splitter)
    builder.add_node("stage_1_chapter", stage_1_chapter)
    builder.add_node("stage_2_assemble", stage_2_assemble)
    builder.add_node("quality_gate_2", quality_gate_2)
    builder.add_node("format_output", format_output)

    # Entry
    builder.set_entry_point("validate_input")

    # Linear edges
    builder.add_edge("validate_input", "stage_0_bible")
    builder.add_edge("stage_0_bible", "quality_gate_0")

    # Stage 0 conditional routing
    builder.add_conditional_edges("quality_gate_0", _route_stage_0)

    # Stage 1 map-reduce
    builder.add_conditional_edges("stage_1_splitter", _route_stage_1)
    builder.add_edge("stage_1_chapter", "stage_2_assemble")

    # Stage 2
    builder.add_edge("stage_2_assemble", "quality_gate_2")
    builder.add_conditional_edges("quality_gate_2", _route_stage_2)

    # Output
    builder.add_edge("format_output", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)
