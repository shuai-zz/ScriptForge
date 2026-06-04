## Context

ScriptForge is a greenfield project. No existing codebase constraints. Target users are novel authors who want to adapt their work into screenplays but lack professional screenwriting training. The tool uses AI (LLM) to automate the heavy lifting of adaptation while keeping the author in creative control.

**Technical context:**
- Frontend: React 19 + TypeScript + TailwindCSS 4 + shadcn/ui (Radix primitives)
- Backend: Python 3.12 + FastAPI + LangGraph + LangChain + SQLAlchemy 2.0 + PostgreSQL
- AI: Multi-provider LLM integration (Anthropic, OpenAI-compatible)
- Versioning: Git wrapper on backend, zero-Git-knowledge UX on frontend
- The core AI pipeline is a 3-stage LangGraph StateGraph: Story Bible → Per-Chapter Conversion → Assembly & Validation

## Goals / Non-Goals

**Goals:**
- Full-stack web app: users upload novel chapters → AI converts → edit in block editor → export
- 5 YAML Schemas (Script, Character, StoryBible, ProjectConfig, Annotation) with design rationale docs
- Multi-model pluggable architecture: users bring their own API keys, assign models per pipeline stage
- Built-in version management via backend Git wrapper with intuitive UI
- Block-based script editor with annotation sidebar, scene timeline, and character visualization
- Streaming AI progress via SSE with live script preview during generation
- Dark visual theme ("暗房 The Darkroom") optimized for writing focus

**Non-Goals:**
- Real-time collaboration (single-user tool)
- Video/audio generation from script
- Full production scheduling / budgeting features
- Mobile app (responsive web for tablet/desktop only)
- Offline-first / PWA
- Multi-language novel support (Chinese-first; architecture allows extension)

## Decisions

### 1. Python + FastAPI over Spring Boot

**Decision:** Use Python 3.12 + FastAPI instead of Spring Boot.

**Rationale:**
- LangChain/LangGraph are Python-native; using them from JVM would require REST bridging, adding latency and complexity
- FastAPI's native async + SSE support is ideal for streaming AI progress
- Pydantic models map directly to YAML Schema validation
- Automatic OpenAPI docs → TypeScript type generation for frontend
- Python's dominance in AI/LLM tooling means faster iteration on prompt engineering

**Alternatives considered:** Spring Boot (original requirement) — rejected because LangChain Java port is immature and the overhead of bridging JVM ↔ Python for LLM calls would dominate development complexity.

### 2. LangGraph for Pipeline Orchestration

**Decision:** Use LangGraph StateGraph to orchestrate the 3-stage conversion pipeline.

**Rationale:**
- DAG-native: Stage 1 chapters can run in parallel; state flows through graph nodes
- Built-in checkpointing: save/resume intermediate states (critical for long-running conversions)
- Streaming: each node's output can be streamed to frontend via SSE
- Conditional edges: quality gates can branch to retry or human intervention
- LangChain integration: unified ChatModel interface for multi-provider LLM

```
StateGraph topology:
  validate_input → stage_0_bible → quality_gate_0 ──(pass)──→ stage_1_map ──→ stage_2_assemble ──→ quality_gate_1 → format_output
                                   │                    (parallel chapters)                         │
                                   └──(fail)──→ retry/human_intervention                            └──(fail)──→ flag_issues
```

**Alternatives considered:**
- Custom Celery workflow — more infrastructure, no streaming, harder to debug
- Prefect/Airflow — overkill for single-user pipeline, heavy deployment
- Manual async orchestration — reinventing DAG logic, no checkpointing

### 3. Block-Based Editor (Self-Built) over Rich Text Library

**Decision:** Build a custom block-based editor rather than adapting TipTap/Slate.js.

**Rationale:**
- Screenplay structure is uniquely rigid: action/dialogue blocks alternate, each with specific sub-fields (character name, parenthetical, etc.)
- Generic rich text editors require extensive schema customization that approaches the cost of a custom solution
- Block model maps 1:1 to YAML Schema, simplifying serialization
- Drag-and-drop reordering is native to a block model; generic editors resist structural drag-and-drop
- ContentEditable blocks with controlled React state are well-understood and debuggable

**Data model:**
```typescript
type ScriptBlock = ActionBlock | DialogueBlock

interface ActionBlock {
  type: "action"
  id: string
  order: number
  text: string
  annotationRefs: string[]
  sourceRef?: { chapter: number; paragraph: number; quote: string }
}

interface DialogueBlock {
  type: "dialogue"
  id: string
  order: number
  charId: string
  charName: string
  line: string
  parenthetical: string | null
  annotationRefs: string[]
  sourceRef?: { chapter: number; paragraph: number; quote: string }
}
```

### 4. Backend Git Wrapper for Version Management

**Decision:** Use GitPython on backend to manage version history; expose simplified concepts to frontend.

**Rationale:**
- Real Git is battle-tested for text versioning (YAML files are text)
- No browser-based Git library needed (isomorphic-git has IndexedDB limitations)
- Frontend only sees: "timeline", "checkpoint", "compare", "restore" — zero Git concepts

**Implementation:**
- Each project gets a Git repo at `/data/projects/{project_id}/`
- Auto-commit every 2 minutes (debounced, only if changes exist)
- User "checkpoint" → `git commit -m "<user message>"` with tag
- AI generation complete → auto-commit with `ai-generated` tag
- Version diff → `git diff <a> <b> -- outputs/` returned as structured diff

**Alternatives considered:**
- Event sourcing with immutable YAML snapshots — simpler to implement but no diff/merge tooling, storage grows linearly
- isomorphic-git in browser — IndexedDB limits, no remote push, complex conflict resolution
- Full Git UI (GitHub-style) — too complex for target users

### 5. YAML as Canonical Format

**Decision:** Store scripts as YAML files; edit through UI that maps YAML ↔ UI state.

**Rationale:**
- YAML is human-readable and editable in any text editor
- Git-diff friendly (line-oriented text format)
- Easy to serialize/deserialize in both Python (PyYAML) and TypeScript (js-yaml)
- Industry scripts use Fountain (markdown-like) or FDX (XML); YAML is structurally richer and easier to program against
- Multi-format export from YAML as single source of truth

### 6. Visual Design: "暗房 The Darkroom"

**Decision:** Dark theme with amber gold (#d4a853) as primary accent, Courier Prime for script content.

**Rationale:**
- Dark backgrounds reduce eye strain during long editing sessions (common for writers)
- Amber gold evokes a desk lamp — warmth, focus, creativity
- Courier Prime is the industry-standard screenplay font, signaling professionalism
- Differentiates from generic SaaS tools

**Color system:**
| Role | Hex | Usage |
|------|-----|-------|
| Page BG | #0b0b12 | Full page background |
| Surface | #13141f | Cards, panels |
| Card | #1a1b2e | Elevated surfaces |
| Primary (Amber) | #d4a853 | Key actions, selected state, AI progress |
| Secondary (Sage) | #5b8c85 | Links, secondary actions |
| Tertiary (Lavender) | #8b7fa8 | Annotations, metadata |
| Text Primary | #e8e6e3 | Body text (warm white) |
| Text Secondary | #9895a0 | Labels, captions |

### 7. API Key Encryption

**Decision:** AES-256-GCM encryption for stored API keys; encryption key from environment variable.

**Rationale:**
- Users bring their own API keys — compromise would be catastrophic
- AES-256-GCM provides authenticated encryption (confidentiality + integrity)
- Key material never logged, never returned in API responses (masked: `sk-ant-***...***aBcD`)
- Encryption key injected via `SCRIPTFORGE_ENCRYPTION_KEY` env var, never in code or DB

### 8. SSE over WebSocket for AI Progress

**Decision:** Use Server-Sent Events (SSE) for streaming AI progress to frontend.

**Rationale:**
- One-way server→client streaming is exactly what AI progress needs
- SSE is simpler than WebSocket: no handshake upgrade, no bidirectional complexity
- Native browser EventSource API (with automatic reconnection)
- FastAPI has first-class SSE support via StreamingResponse
- LangGraph can emit events per node execution

## Risks / Trade-offs

- **[Risk] LLM API latency & cost** → Pipeline uses cheaper models for Stage 0 (analysis) and reserves premium models for Stage 1 (creative conversion). Users control model assignment per stage. Streaming reduces perceived latency.
- **[Risk] AI hallucination in script content** → Annotation system captures AI's reasoning with confidence scores. Low-confidence annotations flagged for review. Source text traceability lets authors verify against original.
- **[Risk] 3+ chapters exceed context window** → Stage 0 compresses full text into structured Story Bible (~3K words). Stage 1 processes one chapter at a time with Bible as shared context. For very long chapters, recursive summarization.
- **[Risk] YAML deeply nested, hard to read raw** → UI is the primary editing surface; raw YAML is for storage and git diff. Schema versioning (v1.0) allows future format evolution.
- **[Trade-off] Custom block editor vs. mature library** → Faster to build for our specific domain, but we forgo rich text features (annotations, collaborative cursors) that mature libraries provide out of box. Acceptable for single-user v1.
- **[Trade-off] Git on backend vs. database versioning** → Adds GitPython dependency and filesystem coupling, but gains battle-tested diff/merge and potential future GitHub integration.

## Open Questions

1. **PDF export engine**: WeasyPrint (Python, free) vs. ReportLab (Python, more control but complex) vs. client-side PDF generation? WeasyPrint is preferred for CSS-based layout but font support for Chinese needs verification.
2. **Chapter upload UX**: Simple textarea paste vs. file upload (txt/md/docx) vs. URL import? Start with textarea + file upload; docx import via markitdown as stretch.
3. **Authentication**: Required for v1? Multi-tenant with user accounts or single-user local deployment? Lean toward optional auth — single-user mode with localStorage project references, optional password-protected multi-project mode.
