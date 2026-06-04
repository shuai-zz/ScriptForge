## Why

小说作者希望将作品改编为剧本，但改编过程门槛高、耗时巨、需要专业编剧知识。ScriptForge 利用 AI 将 3 章以上的小说自动转换为结构化剧本（YAML 格式），让作者快速获得可编辑、可打磨的剧本初稿，将改编从"不可能的任务"变成"可迭代的创作过程"。

## What Changes

- **新建项目管理系统**：创建、管理、配置剧本改编项目，包含项目元数据、转换参数、输入章节管理
- **多模型可插拔 LLM 集成**：支持 Anthropic Claude、OpenAI、OpenAI 兼容接口（DeepSeek、Qwen、Ollama 等）多种模型，用户自备 API Key，不同 Pipeline 阶段可指定不同模型
- **AI 驱动的三阶段转换 Pipeline**：Stage 0 全文全局分析（故事圣经）→ Stage 1 逐章并行转换 → Stage 2 全局组装与一致性校验，基于 LangGraph 编排，支持流式进度推送
- **结构化剧本 YAML 格式**：设计 5 个 YAML Schema（剧本、角色、故事圣经、项目配置、注释），兼顾可读性与可程序化处理
- **Block-based 剧本编辑器**：自研块编辑器，剧本内容以动作块/对白块交错排列，支持拖拽排序、快捷键操作、原文追溯、AI 注释侧栏
- **AI 改编注释系统**：AI 的每次改编决策可追溯（置信度、备选方案、原文引用），作者可接受/忽略/修改建议
- **内置版本管理**：后端 Git 封装，用户看到的是"保存检查点 / 时间河流 / 对比 / 恢复"，底层是真实 Git，零学习成本
- **多格式导出**：支持 YAML（源格式）、PDF（标准剧本排版）、Fountain（纯文本标记）、FDX（Final Draft XML）
- **YAML Schema 文档**：独立的 Schema 定义文档，说明每个字段的设计理由与使用场景
- **前端应用（React + TailwindCSS）**：「暗房」视觉设计语言，深色创作主题，场景时间线、角色关系图、流式 AI 进度
- **后端服务（Python + FastAPI + LangGraph）**：异步 REST API + SSE 流式推送，PostgreSQL 存储，AES-256 加密 API Key

## Capabilities

### New Capabilities

- `project-management`: 项目 CRUD、章节上传与管理、转换参数配置
- `llm-integration`: 多模型 Provider 配置、API Key 加密存储、LangGraph Pipeline 编排与流式进度推送
- `script-conversion`: Stage 0 故事圣经生成、Stage 1 逐章转换、Stage 2 全局组装与一致性校验
- `script-editor`: Block-based 剧本编辑器（动作块/对白块）、场景时间线、拖拽排序、原文追溯、聚焦模式
- `annotation-system`: AI 改编注释的生成、展示、筛选（按置信度/类型）、接受/忽略/修改工作流
- `version-management`: 后端 Git 封装的版本历史、自动保存、检查点、版本对比、版本恢复
- `script-export`: YAML/PDF/Fountain/FDX 多格式导出、标准剧本排版预览
- `yaml-schema`: 5 个 YAML Schema 的定义文件与配套文档，说明设计理由

### Modified Capabilities

<!-- 全新项目，无已有 capabilities 需修改 -->

## Impact

- **新项目**：从零构建，无现有代码影响
- **技术栈**：Python 3.12 + FastAPI + LangGraph + LangChain + PostgreSQL + React 19 + TypeScript + TailwindCSS 4 + Monaco Editor
- **外部依赖**：LLM API（Anthropic、OpenAI 及兼容接口）、Git（后端版本管理）、PDF 生成库（WeasyPrint/ReportLab）
- **部署**：前端静态资源 + 后端 FastAPI 服务 + PostgreSQL 数据库 + 文件存储（项目 Git 仓库）
