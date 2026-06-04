# ScriptForge Development Guidelines

## Project Structure

This is a monorepo with independent modules in subdirectories:

```
/
├── frontend/     # React 19 + TypeScript + Vite
├── backend/      # Python 3.12 + FastAPI + LangGraph
└── docs/         # Documentation
```

Each module should have its own dependency management (`package.json` / `pyproject.toml`) and be deployable independently.

## Branch Strategy

```
main  ←── dev  ←── feat/xxx
 ↑        ↑
stable   integration   feature branches
```

- **`main`**: Production-ready. Only merges from `dev`. Must always be runnable.
- **`dev`**: Integration branch. All feature PRs target `dev`.
- **`feat/*`**: Feature branches branched from `dev`. One feature per branch.

## PR Rules

### One PR, One Thing

Each PR must implement or modify a **single** function. Large features must be split into multiple independent, small, granular PRs. Encourage the smallest possible PR size.

### PR Title & Description (Chinese)

Every PR must include:

1. **标题 (Title)**: One sentence describing what this PR adds/modifies.
2. **功能描述 (Feature Description)**: What this feature does and how to use it.
3. **实现思路 (Implementation Approach)**: Brief explanation of technical choices or core logic.
4. **测试方式 (Testing)**: How to verify the feature works correctly.

### Post-Merge

After PR merge, the target branch (`dev` or `main`) must remain in a **runnable state**. Merging to `main` should always go through `dev` — never directly push to `main`.

## Commit Convention

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Build/tooling

## AI Assistant Notes

Before writing any code, review this file and the OpenSpec artifacts at `openspec/changes/script-forge-app/`:
- `proposal.md` — what and why
- `design.md` — technical decisions
- `specs/*/spec.md` — detailed requirements
- `tasks.md` — implementation checklist
