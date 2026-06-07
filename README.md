# ScriptForge

> AI 驱动的小说转剧本工具 — 将长篇小说智能改编为结构化专业剧本。

ScriptForge 是一款面向编剧、小说作者和影视内容创作者的 AI 辅助创作平台。它通过 LangGraph 驱动的三阶段流水线，把小说章节自动转换为符合行业标准格式（YAML / Fountain / PDF / Final Draft）的剧本，并提供块级编辑器、角色关系网络、版本管理和语义质量校验等完整工具链。

---

## ✨ 核心亮点

- **AI 三阶段转换流水线**
  - Stage 0：故事圣经 — 全局分析角色、关系、时间线与主题
  - Stage 1：逐章转换 — 并行生成场景边界、动作与对白
  - Stage 2：全局组装 — 场景编号、一致性校验与多格式输出
  - 支持 SSE 实时进度流，随时查看转换状态

- **结构化 YAML 剧本格式**
  - 完整的 `script-v1`、`character-v1`、`story-bible-v1` 等 5 大 Schema
  - Pydantic 强校验，保证输出格式稳定、可扩展

- **块级剧本编辑器**
  - 动作块 / 对白块自由切换与拖拽排序
  - Scene Timeline 场景胶片条快速导航
  - 专注模式（Focus Mode）沉浸式创作
  - 原文溯源：点击 source ref 查看小说出处段落

- **角色与故事圣经视图**
  - 角色资料卡、成长弧线与台词风格
  - `@xyflow/react` 角色关系图谱
  - 全局故事圣经：梗概、时间线、主题、伏笔追踪

- **注释与质量校验**
  -  AI 自动标注改进建议（严重 / 警告 / 建议）
  -  语义校验器：角色一致性、Slug 格式、场次连续性、时间线一致性等
  -  一键采纳 / 忽略 / 应用替代方案

- **版本管理**
  - 每个项目独立 Git 仓库
  - 自动保存、手动 Checkpoint、版本对比与回滚
  - 基于 Monaco DiffEditor 的 YAML 差异视图

- **多格式导出**
  - YAML（ScriptForge 原生）
  - Fountain（纯文本编剧格式）
  - PDF（标准剧本格式，reportlab 渲染）
  - Final Draft `.fdx`（XML 格式）

- **响应式界面 + 新手引导**
  - 桌面端图标栏侧边栏，移动端抽屉菜单
  - Framer Motion 页面过渡与微交互
  - 5 步 Onboarding Wizard 引导首次使用

---

## 🎥 视频演示

📺 [Bilibili：ScriptForge 项目介绍与功能演示](https://www.bilibili.com/video/BV1DQEx6MEMm/?vd_source=a7cd440f3d6b387634e694fc865d9e24)

## 🏗 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 19 + TypeScript + Vite 6 + TailwindCSS 4 + Framer Motion |
| 后端 | Python 3.12+ + FastAPI + SQLAlchemy 2.0（async）+ Alembic |
| AI 引擎 | LangGraph + LangChain（Anthropic / OpenAI Compatible） |
| 数据库 | PostgreSQL 16 |
| 版本存储 | GitPython（每个项目独立仓库） |
| 测试 | pytest + Playwright |

---

## 📁 项目结构

```
/
├── frontend/          # React 19 + TypeScript + Vite
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   ├── components/      # 通用组件 & 编辑器组件
│   │   └── lib/             # 工具函数
│   └── e2e/                 # Playwright E2E 测试
├── backend/           # Python + FastAPI + LangGraph
│   ├── app/
│   │   ├── routers/         # REST API
│   │   ├── pipeline/        # LangGraph 转换流水线
│   │   ├── services/        # 业务逻辑与校验器
│   │   ├── models/          # SQLAlchemy ORM
│   │   └── schemas/         # Pydantic 模型
│   ├── tests/               # pytest 测试
│   └── alembic/             # 数据库迁移
├── landing/           # GitHub Pages 项目介绍页
├── docs/              # 文档
│   └── yaml-schema-guide.md # YAML Schema 设计指南
├── openspec/          # OpenSpec 需求规格
└── docker-compose.yml # PostgreSQL 开发环境
```

---

## 🚀 快速开始

### 前置依赖

- [Python 3.12+](https://www.python.org/) + [uv](https://docs.astral.sh/uv/)
- [Node.js 20+](https://nodejs.org/) + npm
- [Docker](https://www.docker.com/)（用于 PostgreSQL）

### 1. 启动 PostgreSQL

```bash
docker compose up -d
```

默认会暴露 `localhost:5432`，数据库为 `scriptforge`，用户名/密码均为 `postgres`。

### 2. 启动后端

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key（Anthropic / OpenAI）和 SCRIPTFORGE_ENCRYPTION_KEY
uv sync
source .venv/bin/activate
uv run uvicorn app.main:app --reload
```

后端默认运行在 http://localhost:8000，API 前缀为 `/api`。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器默认运行在 http://localhost:5173，并通过 Vite proxy 转发 `/api` 到后端。

---

## 🧪 测试

### 后端测试

```bash
cd backend
source .venv/bin/activate
uv run pytest
```

### 前端 E2E 测试

```bash
cd frontend
npx playwright install chromium   # 首次运行需要安装浏览器
npx playwright test --project=chromium
```

---

## 📖 相关文档

- [YAML Schema 设计指南](docs/yaml-schema-guide.md)
- [OpenSpec 归档规格](openspec/changes/archive/2026-06-06-script-forge-app/)
- [GitHub Pages 项目介绍](https://shuai-zz.github.io/ScriptForge/)

---

## 🤝 贡献

本项目遵循 `feat/xxx` → `dev` → `main` 的分支策略。提交信息使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

---

## 📄 License

MIT
