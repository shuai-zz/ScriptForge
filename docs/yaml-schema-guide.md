# ScriptForge YAML Schema Guide v1.0

本文档说明 ScriptForge 五个核心 YAML Schema 的设计 rationale、字段用途与 trade-offs。

---

## 1. script-v1.yaml — 剧本

### 设计 rationale

剧本是 ScriptForge 的**核心产出物**。选择 YAML 而非 Fountain/FDX 作为 canonical 格式的原因是：

- **结构化**：YAML 天然支持嵌套对象和列表，而 Fountain 是纯文本标记，FDX 是 XML，都需要额外解析才能拿到结构化数据
- **Git-friendly**：行级 diff 让版本对比一目了然
- **AI-friendly**：LLM 生成和解析 YAML 的准确率高于 XML，且比纯文本更容易约束结构

### 关键字段

| 字段 | 用途 | 设计决策 |
|------|------|----------|
| `metadata` | 剧本元信息（标题、来源小说、字数统计等） | 放在根级别而非嵌套在第一个 scene 中，方便快速读取 |
| `scenes[].slug` | 拆解为 `location_type` + `location_name` + `time` | 而非一条字符串，便于语义验证（如 `SlugLineValidator`）和前端渲染 |
| `scenes[].blocks` | 动作块/对白块交替排列 | 块模型（block-based）1:1 映射到 UI 编辑器，也便于拖拽排序 |
| `blocks[].source_ref` | 追溯原文出处 | 每个改编决策都可溯源，支撑 annotation 系统 |
| `scene_index` | 场景的扁平导航表 | 与嵌套的 `scenes` 并存，避免前端每次都要遍历嵌套结构来生成时间线 |

### Trade-offs

- **YAML 嵌套较深**：直接阅读 raw YAML 的体验不如 Fountain 流畅。缓解方案：UI 是主要编辑面，YAML 仅用于存储和 git diff
- **块模型牺牲了富文本**：不支持加粗/斜体等内联样式。决策依据：剧本格式本身就不使用富文本，Courier Prime 纯文本即行业标准

---

## 2. character-v1.yaml — 角色档案

### 设计 rationale

角色是**可复用的独立实体**。一个角色档案可以被多个剧本引用，也可以在项目间迁移。

### 关键字段

| 字段 | 用途 | 设计决策 |
|------|------|----------|
| `story_role.type` | protagonist / antagonist / supporting / minor | 四级分类足够覆盖绝大多数剧本，不过度细分 |
| `voice` | 说话风格、口头禅、词汇水平 | 直接喂给 LLM 的 system prompt，让 AI 生成有辨识度的对白 |
| `arc` | 起-中-终三态转变 | 简化版英雄之旅，Stage 0 生成后供 Stage 1 参照，确保角色发展一致性 |
| `source_evidence` | 原文引用支撑 | 让 AI 的角色分析有据可查，也便于作者核实 |
| `appearance_stats` | 出场次数、对白次数 | 运行时统计，支撑 `CharacterAppearanceValidator`（主角出场率 ≥ 20%） |

### Trade-offs

- **voice 字段偏主观**："speech_patterns" 是自然语言描述，而非结构化标签。决策依据：语音风格难以用离散标签精确描述，自然语言对 LLM 更友好
- **relationship 是单向的**：`target_char_id` 表示从当前角色出发的关系。如果需要双向关系，由后端根据两条单向记录合并。简化 schema，不引入图论复杂度

---

## 3. story-bible-v1.yaml — 故事圣经

### 设计 rationale

故事圣经是 **Stage 0 的全局分析输出**，也是 Stage 1 每个章节转换的**共享上下文**。它的核心使命是：把任意长度的小说压缩成 ~3K 字的结构化摘要，让 LLM 在处理单章时不会丢失全局信息。

### 关键字段

| 字段 | 用途 | 设计决策 |
|------|------|----------|
| `chapter_synopses` | 每章摘要 + 关键事件 | 事件标注 `significance`（major/minor/setup/payoff），直接支撑伏笔校验 |
| `character_network` | 节点+边的图结构 | 显式图结构便于 `@xyflow/react` 渲染关系图，也便于检查孤立角色 |
| `foreshadowing_tracking` | 追踪 setup/payoff 对 | 单独的 tracker 而非散落在 chapter_synopses 中，防止遗漏 |
| `location_index` | 地点目录 + 关键道具 | 防止 AI 在 Stage 1 中凭空创造地点或遗忘已引入的道具 |

### Trade-offs

- **timeline 只有单层**：不支持并行时间线或多宇宙。决策依据：v1 面向单线叙事小说，复杂时间结构留待 v2
- **overall_synopsis 是纯文本**：没有强制字数限制。决策依据：LLM 生成时通过 prompt 约束 ~500 字，schema 层面不硬编码，避免中英文差异

---

## 4. project-config-v1.yaml — 项目配置

### 设计 rationale

项目配置体现两个核心设计原则：

1. **用户自带 API Key**（BYOK）：不托管任何模型凭证，所有密钥 AES-256-GCM 加密后存于本地数据库
2. **Stage 级模型分配**：不同 pipeline 阶段可指定不同模型，平衡成本与质量

### 关键字段

| 字段 | 用途 | 设计决策 |
|------|------|----------|
| `llm_providers[].assigned_stages` | 一个 provider 可负责多个 stage | 灵活分配：例如 Stage 0 用便宜模型做分析，Stage 1 用 Claude 做创意转换 |
| `conversion_params.dialogue_preservation` | rewrite / preserve / enhance | 给用户控制权：忠于原文 vs. 自由改写 vs. 适度润色 |
| `conversion_params.auto_split` | 是否自动将长章节拆分为多场景 | 默认开启；关闭时用户可手动控制场景边界 |

### Trade-offs

- **provider_type 只有两类**：anthropic / openai_compatible。决策依据：覆盖 90%+ 的可用模型（OpenAI、DeepSeek、Qwen、Ollama 都兼容 OpenAI API 格式）。未来可增加 `google` 或 `local` 类型
- **API Key 加密但不哈希**：需要可逆加密（解密后传给 LLM SDK），因此不能用 bcrypt 等单向哈希。缓解方案：AES-256-GCM + 环境变量注入的 master key

---

## 5. annotation-v1.yaml — 改编批注

### 设计 rationale

Annotation 是 ScriptForge 的**信任机制**。AI 的每一次改编决策都留下痕迹，作者可以：

- 查看"为什么这样改"
- 对比备选方案
- 根据置信度决定是否需要人工复核

### 关键字段

| 字段 | 用途 | 设计决策 |
|------|------|----------|
| `severity` | error / warning / info / suggestion | 四级制，与 IDE linter 的级别对齐，用户直觉理解 |
| `category` | 8 个受控分类 | 受控词汇让批注可筛选、可统计，避免自由文本的混乱 |
| `alternatives` | 每个备选附带 pros/cons | 不是简单列出文本，而是强制分析 trade-off，帮助作者做知情决策 |
| `confidence` | 0.0–1.0 浮点 | 低于阈值的批注自动标红，提示必须 review |
| `auto_applied` | 区分 AI 自动生成 vs. 用户手动添加 | 支持用户自己写批注，也便于后续分析 AI 决策质量 |

### Trade-offs

- **category 只有 8 个**：初期覆盖主要改编场景，但不可能穷尽。缓解方案：`extra="allow"` 在 Pydantic 模型中保留扩展空间，未来可通过版本升级添加新分类
- `target_reference` 用 type + id 指针而非内联内容：避免数据冗余和同步问题，但也意味着前端渲染时需要额外查询

---

## Schema 演进策略

所有 schema 采用 **语义版本控制（vMAJOR.MINOR）**：

- **MAJOR 升级**：破坏性格式变更，需要迁移脚本
- **MINOR 升级**：向后兼容的字段新增，旧数据通过 `extra="allow"` 安全通过验证

当前所有 Pydantic 模型均配置 `ConfigDict(extra="allow")`，确保 MINOR 升级时不会拒绝旧数据。
