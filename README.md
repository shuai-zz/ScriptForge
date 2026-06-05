# ScriptForge

AI 辅助剧本创作工具 — 将小说自动转换为结构化剧本。

## 项目结构

```
/
├── frontend/     # React 19 + TypeScript + Vite
├── backend/      # Python 3.12 + FastAPI + LangGraph
└── docs/         # 文档
```

## 快速开始

### 后端

```bash
cd backend
cp .env.example .env
# 编辑 .env 填入你的 LLM API Key
uv sync
uv run uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```
