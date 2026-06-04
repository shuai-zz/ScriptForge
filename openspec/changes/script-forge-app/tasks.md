## 1. Project Scaffolding

- [ ] 1.1 Initialize monorepo structure: `backend/` (Python/FastAPI) and `frontend/` (React/Vite/TypeScript)
- [ ] 1.2 Backend: Set up FastAPI app skeleton with health check, CORS middleware, and project directory layout (routers/, services/, models/, schemas/, pipeline/)
- [ ] 1.3 Backend: Configure SQLAlchemy 2.0 async engine + Alembic for PostgreSQL with base models
- [ ] 1.4 Frontend: Initialize Vite + React 19 + TypeScript project with TailwindCSS 4, shadcn/ui, and React Router 7
- [ ] 1.5 Frontend: Implement "暗房 The Darkroom" design system (colors, typography, spacing, shadows) as Tailwind theme + CSS variables
- [ ] 1.6 Frontend: Build base layout shell (sidebar nav + main content area + toast notifications)

## 2. YAML Schema Definitions & Documentation

- [ ] 2.1 Define `script-v1.yaml` — complete screenplay schema with metadata, characters, scenes (action/dialogue blocks), scene_index, and global_annotations
- [ ] 2.2 Define `character-v1.yaml` — character profile schema with basic info, story role, arc, voice, relationships, source evidence, and appearance stats
- [ ] 2.3 Define `story-bible-v1.yaml` — story bible schema with synopses, character network, timeline, themes, foreshadowing tracking, and location index
- [ ] 2.4 Define `project-config-v1.yaml` — project configuration schema with llm_providers (encrypted keys), conversion_params, input chapters, and output settings
- [ ] 2.5 Define `annotation-v1.yaml` — annotation schema with severity, category taxonomy, target reference, source quote, alternatives, and confidence scoring
- [ ] 2.6 Create Python Pydantic models mirroring all 5 YAML schemas for validation
- [ ] 2.7 Write `docs/yaml-schema-guide.md` — standalone document explaining each schema's design rationale, field purposes, and trade-offs

## 3. Database & Storage Layer

- [ ] 3.1 Implement Project model and CRUD repository/service (UUID PK, name, status enum, config JSONB, timestamps)
- [ ] 3.2 Implement Chapter model and CRUD repository/service (project FK, number, title, raw_text, word_count, status)
- [ ] 3.3 Implement Script model and repository (project FK unique, version string, yaml_content text, metadata JSONB)
- [ ] 3.4 Implement Scene model and repository (script FK, scene_number, slug fields, summary, yaml_snippet)
- [ ] 3.5 Implement Character model and repository (project FK, name, aliases JSONB, role_type enum, traits JSONB)
- [ ] 3.6 Implement CharacterRelationship, Annotation, StoryBible, ConversionRun, and LLMProvider models
- [ ] 3.7 Implement API key encryption utility (AES-256-GCM encrypt/decrypt with SCRIPTFORGE_ENCRYPTION_KEY env var)
- [ ] 3.8 Run initial Alembic migration and verify schema creation

## 4. LLM Integration Layer

- [ ] 4.1 Implement LLMProvider CRUD endpoints (POST/GET/PUT/DELETE /api/providers) with key encryption on write, masking on read
- [ ] 4.2 Implement ChatModel factory: unified interface dispatching to ChatAnthropic or ChatOpenAI based on provider type
- [ ] 4.3 Build PromptTemplate registry for all pipeline stages (Stage 0 Bible, Stage 1 Conversion, Stage 2 Assembly) with variable substitution
- [ ] 4.4 Implement token counting and context window estimation utility
- [ ] 4.5 Frontend: Build model configuration page (add/edit/delete providers, assign stages, test connection button)

## 5. AI Conversion Pipeline (LangGraph)

- [ ] 5.1 Define ConversionState TypedDict with all pipeline fields (chapters, story_bible, chapter_scripts, assembled_script, errors, progress, quality_checks)
- [ ] 5.2 Implement Stage 0 node: validate_input — check chapter count ≥ 3, format validity
- [ ] 5.3 Implement Stage 0 node: stage_0_bible — invoke LLM with full-text analysis prompt, parse response into StoryBible Pydantic model
- [ ] 5.4 Implement Stage 0 quality gate: verify key character count ≥ 1, branch to retry (max 3) or human intervention
- [ ] 5.5 Implement Stage 1 map node: per-chapter parallel conversion — each chapter receives Story Bible context + preceding chapter script, produces list of Scenes
- [ ] 5.6 Implement Stage 2 node: stage_2_assemble — concatenate all scenes, assign sequential numbers, generate scene index, run consistency checks
- [ ] 5.7 Implement Stage 2 quality gate: scene count ≥ 10 check, character consistency check, timeline coherence check
- [ ] 5.8 Implement format_output node: validate final Script against Pydantic model, serialize to YAML, persist to DB and Git
- [ ] 5.9 Wire StateGraph edges with conditional routing for quality gates, add checkpoint persistence
- [ ] 5.10 Implement SSE streaming endpoint (GET /api/projects/{id}/convert/stream) emitting progress events per node
- [ ] 5.11 Implement conversion run lifecycle: create ConversionRun on start, update status/timing on completion/failure, support resume from checkpoint
- [ ] 5.12 Frontend: Build AI pipeline progress page with stage cards, live streaming script preview, and retry/background options

## 6. Project & Chapter Management (Frontend + Backend)

- [ ] 6.1 Implement Project CRUD REST endpoints (POST/GET/PUT/DELETE /api/projects)
- [ ] 6.2 Implement Chapter CRUD REST endpoints with text upload (POST/GET/PUT/DELETE /api/projects/{id}/chapters)
- [ ] 6.3 Implement Project config read/write endpoints (GET/PUT /api/projects/{id}/config)
- [ ] 6.4 Frontend: Build Dashboard page with project cards (name, progress, stats), create/delete project modals
- [ ] 6.5 Frontend: Build Chapter management page (upload via textarea paste + file upload, reorder via drag-and-drop, word count display)
- [ ] 6.6 Frontend: Build Project Settings page (target format, conversion parameters, chapter list)

## 7. Script Editor (Frontend)

- [ ] 7.1 Implement block-based data model (ScriptBlock = ActionBlock | DialogueBlock) with TypeScript types
- [ ] 7.2 Build ActionBlock component (content-editable text area, source reference footer, annotation badges)
- [ ] 7.3 Build DialogueBlock component (character name header, content-editable line, editable parenthetical, source reference, annotation badges)
- [ ] 7.4 Build Scene container component (slug line header, block list with drag-and-drop via @dnd-kit, add-block button)
- [ ] 7.5 Build scene timeline component (horizontal scrollable filmstrip cards with scene number, location emoji, character dots, page estimate, insert button)
- [ ] 7.6 Build left sidebar scene navigation (ordered scene list, character presence indicators, active scene highlighting)
- [ ] 7.7 Implement keyboard shortcuts: Enter (new block), Tab (toggle type), Cmd+K (command palette), Cmd+S (checkpoint), Shift+F (focus mode)
- [ ] 7.8 Build Focus Mode (full-screen, centered, Courier Prime, hide all chrome)
- [ ] 7.9 Build command palette (Cmd+K) with searchable actions
- [ ] 7.10 Implement source traceability: click source reference → popover with original chapter text and highlighted relevant sentences

## 8. Annotation System (Frontend + Backend)

- [ ] 8.1 Implement Annotation REST endpoints (GET /api/projects/{id}/annotations with filter params)
- [ ] 8.2 Implement annotation action endpoints (PUT annotation/{id} for accept/ignore/modify status)
- [ ] 8.3 Frontend: Build annotation sidebar panel with severity icons, category badges, confidence indicators
- [ ] 8.4 Frontend: Implement annotation filtering (by severity, category, confidence range)
- [ ] 8.5 Frontend: Implement hover-to-highlight (annotation → corresponding block pulses)
- [ ] 8.6 Frontend: Implement annotation actions (accept turns green, ignore dims, apply alternative replaces block content)
- [ ] 8.7 Frontend: Display global annotations in a dedicated "全局建议" section at script top

## 9. Version Management (Backend + Frontend)

- [ ] 9.1 Implement Git repository initialization per project (git init at /data/projects/{project_id}/)
- [ ] 9.2 Implement auto-save service (debounced timer, checks for file changes before commit)
- [ ] 9.3 Implement checkpoint creation (git commit with user message + optional tag)
- [ ] 9.4 Implement version timeline endpoint (GET /api/projects/{id}/versions — parses git log into structured version list with type tags)
- [ ] 9.5 Implement version diff endpoint (GET /api/projects/{id}/versions/diff?a=&b= — returns unified diff + change summary stats)
- [ ] 9.6 Implement version restore endpoint (POST /api/projects/{id}/versions/{version_id}/restore — git checkout + auto-save current state first)
- [ ] 9.7 Frontend: Build Version History page with vertical timeline (version cards with type icons, timestamps, descriptions, change summaries)
- [ ] 9.8 Frontend: Build Version Diff view (side-by-side Monaco DiffEditor with YAML syntax highlighting, change statistics)
- [ ] 9.9 Frontend: Build Checkpoint modal (description input, optional tags, change preview)
- [ ] 9.10 Frontend: Build Restore confirmation dialog (warning text, suggestion to checkpoint first)

## 10. Script Export (Backend + Frontend)

- [ ] 10.1 Implement YAML export endpoint (GET /api/projects/{id}/export/yaml — serves raw YAML file)
- [ ] 10.2 Implement Fountain export converter (Script YAML → Fountain syntax, handles slug lines, action, dialogue, transitions)
- [ ] 10.3 Implement PDF export using WeasyPrint with standard screenplay CSS (Courier Prime 12pt, proper margins, page numbers, CONTINUED markers)
- [ ] 10.4 Implement FDX export converter (Script YAML → Final Draft XML schema)
- [ ] 10.5 Implement batch export endpoint (POST /api/projects/{id}/export with format list → zip download)
- [ ] 10.6 Frontend: Build Export dialog (format checkboxes, PDF preview panel, format-specific options)

## 11. Character & Story Bible Views (Frontend)

- [ ] 11.1 Build Character management page (list + detail view, edit traits/relationships/arc)
- [ ] 11.2 Build character relationship graph visualization using @xyflow/react (nodes = characters, edges = relationships)
- [ ] 11.3 Build Story Bible view page (structured display of global analysis: synopsis tree, character network summary, timeline, themes)
- [ ] 11.4 Build Script Statistics dashboard (character dialogue/ appearance counts, scene distribution chart, sentiment/emotion arc)

## 12. Polish & Quality

- [ ] 12.1 Implement global error handling (backend exception handlers → structured error responses; frontend error boundaries)
- [ ] 12.2 Implement loading states for all async operations (skeleton screens, progress indicators)
- [ ] 12.3 Implement empty states for all list views (illustration + CTA for first action)
- [ ] 12.4 Build responsive layout adaptations (tablet: two-panel, mobile: preview-only)
- [ ] 12.5 Add Framer Motion page transitions and micro-interactions (card hover lift, AI progress pulse, block drop animation)
- [ ] 12.6 Build onboarding wizard (5-step guided flow: create project → upload chapters → configure model → start conversion → first edit)
- [ ] 12.7 Write unit tests for LLM provider factory, YAML schema validation (Pydantic), and Git version operations
- [ ] 12.8 Write integration tests for full conversion pipeline (mock LLM responses)
- [ ] 12.9 Write end-to-end frontend tests for editor flow (Playwright: upload → convert → edit → export)
