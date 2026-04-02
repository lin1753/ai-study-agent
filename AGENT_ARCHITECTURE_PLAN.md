# AI Study Agent - 智能体架构演进方案 (v2.0)

## 1. 架构目标
当前的系统基于“检索增强生成（RAG）+ LLM”的传统线性链路。为了解决幻觉严重、功能单一、无法自主纠错等问题，我们计划将系统全面升级为**基于 ReAct (Reasoning and Acting) 思想的真实智能体 (Agent) 架构**。

## 2. 核心架构设计

新系统将基于以下工作流：
`用户指令 -> Agent Controller (规划与拆解) -> 循环 [ 思考(Thought) -> 行动(Action/Tool) -> 观察(Observation) ] -> 整理回答 -> 记忆持久化`

### 2.1 核心模块拆解
1. **Agent Controller (大脑/中枢)**
   - 负责意图识别与任务拆解。
   - 维护短期的 ReAct 循环，防止系统陷入死循环（最高迭代限制）。
2. **Tool Registry (工具箱)**
   - **`rag_search_tool`**: 专职从本地数据库检索知识点/原题。隔离考试配置的干扰。
   - **`ocr_vision_tool`**: 解析复杂数学公式或错题图片。
   - **`web_search_tool`**: （可选引申）当本地内容不足时，调用外部搜索进行补充。
   - **`exam_generator_tool`**: 根据考试权重配置（例如选/填/计比例），在获取局部知识点后进行定制化出题，负责彻底切割“解析”与“出题”逻辑，解决幻觉。
3. **Memory System (记忆组件)**
   - **短期记忆 (Session Context)**: 位于当前聊天的历史记录中。
   - **长期记忆 (User Profile)**: 构建学情画像。包含：用户常错题型总结、用户的表达偏好、用户薄弱科目设定等。
4. **Tone Modifier (语气过滤器)**
   - 新增输出后处理管道。对带有强烈“AI味”（“首先、其次、综上所述、作为AI模型”）的文本进行降级改写，或通过极强的 System Prompt 配合 Few-Shot 给定导师拟人风格。

---

## 3. 分阶段实施路线 (Roadmap)

### ✅ Phase 1: 底层基础设施改造与性能调优 (已完成)
- **成就**:
  1. 引入并手写了基于 Python 函数映射的轻量级 Agent Controller 工具链。
  2. 完成了 `DocumentParserTool` 与 `ExamGenerator` 的解耦，通过 Map-Reduce 大纲归并算法，根除超长 PDF 生成卡死与 Token 溢出问题。
  3. 将重型处理任务剥离至 Redis + RQ Background Worker 中，主线程解耦，支持超大并发上传。

### 🔄 Phase 1.5: 项目重构与模块优化 (当前阶段)
- **目标**: 解决 `backend` 目录下过于臃肿（意大利面条代码）、缺乏统一规范的问题，优化项目结构。
- **任务**:
  1. 标准化分层架构（将其划分为 `api`, `core`, `services`, `models`, `workers` 五个核心组件域）。
  2. 提取散落的配置与环境变量（Database URL, API Keys）。
  3. 梳理清理废弃与冗余脚本。

### Phase 2: 导师人设与记忆系统介入 (规划中)
- **目标**: 消除 AI 刻板语气，建立用户学习画像。
- **任务**:
  1. 在 `backend/teaching_styles.py` 中扩充并重构 `System Prompt`。
  2. 在数据库模型中增加 `UserProfile` 和 `MemoryLogs`。
  3. 在 Agent 反馈最终结果前，通过中间件拦截，如果判定套话过多，执行一次重写(Rewrite)。

### Phase 3: 工具箱扩展与前端流式反馈完善 (2周)
- **目标**: 支持更多模态，缓解由于多次思考带来的推理高延迟。
- **任务**:
  1. 接入 DuckDuckGo/Tavily 做轻量化外网资料拉取。
  2. 前端 `MainThread.jsx` 和 `ChatInterface.jsx` 改造：不再是单纯响应文本，需要通过 Server-Sent Events (SSE) 或 Websocket 实时的推送 Agent 的内心戏（例如：页面显示 `[思考中...] 正在查找第一章例题...` -> `[工具调用] 本地没有找到原题，停止出题...`）。

---

## 4. 当前技术栈面临的挑战点 & 对策
* **模型函数调用能力不足(Function Calling)**
  * *问题*: DeepSeek-r1:7b 在多轮 ReAct 下，直接输出符合 JSON Schema 规范的函数调用字符串可能会崩。
  * *对策*: 我们将采用 **XML/Markdown Tag 格式** 来替代死板的 JSON，小模型对 Tag (`<action>search</action>`) 的解析准确率远高于 JSON。
* **延迟 (Latency)**
  * *问题*: 分布式长考（多轮Prompt交互）会让首字输出的时间从 3 秒拉长到 10 秒以上。
  * *对策*: 强依赖前端 UI/UX 的补偿动画。在终端推送详细的 Agent Trace Log，给前端透传 State。