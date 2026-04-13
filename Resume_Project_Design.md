# AI 个人助教（AI Study Agent）简历项目包装与面试指南

## 1. 项目简介（一句话概括）
**基于 FastAPI + RAG + Docker + Redis 异步架构重构的智能伴学陪读全栈应用。**
通过云端大模型与本地 Ollama (DeepSeek) 异构算力协作，实现长篇 PDF/PPT 等文档的向量化拆分检索（RAG）、知识图谱动态渲染和大模型引导式苏格拉底教学引擎。

## 2. 核心亮点（用于筛选简历的关键词提取）
* **教育垂直领域设计**: 基于认知科学的苏格拉底启发式教学引擎 (Confusion Guard)；LLM-as-a-Judge 双模型博弈教研员 (Teaching Judge)；动态知识图谱重构 (Roadmap Mutation)。
* **基础架构**: Python, FastAPI, React, PostgreSQL/pgvector, Redis
* **工程架构**: 基于 Redis 和 RQ 的异步任务队列(Task Queue) 解决高并发及耗时任务；RAG (pgvector 纯 SQL 级联检索) 解决大模型业务核心痛点；双引擎 LLM (流式通信 / Server-Sent Events (SSE))。
* **大模型能力**: 纯手工构建 ReAct Agent (不依赖 LangChain)、自定义 Tool Calling 引擎（原生 XML 解析拦截）、多轮对话状态追踪（Thread Stateful）、纯本地 OCR (RapidOCR) 多模态降级容灾、基于认知负荷理论的多层级启发对话引擎 (Pedagogical Engine)。

---

## 3. 面试简历书写指南 (Resume Bullet Points)

以下是从两个不同侧重点出发的简历写法，请根据面试岗位自行调整：

### 侧重全栈/后端架构方向
**项目名称**：AI 个人智能助教平台 (全栈开发)
**技术栈**：FastAPI, React, PostgreSQL (pgvector), Redis, RQ, Docker, Ollama
**项目描述**：基于 LLM 与 RAG 技术构建的文档级智能伴学平台，支持长篇 PDF/PPT 等复杂文档的向量化拆分检索与启发式教学。
**核心工作**：
1. **异步文档解析流水线**：接入 RQ（Redis Queue）解耦百页长文档的文件切片、OCR识别与向量化。确保大范围 PDF 解析时后端 API 能直接 202 异步放行，防止 HTTP 连接断开（解决 504 Timeout 问题），响应速度达毫秒级。
2. **构建企业级 RAG 系统**：借助 Docker 部署带有 pgvector 扩展的 PostgreSQL。将高维向量通过 SQLAlchemy 入库，并在业务层基于余弦距离 (`cosine_distance`) 进行 Top-k 知识召回与上下文截断，同时保证了向量数据和关系型元数据（文件ID/页码）的一致性。
3. **自研 Tool Calling 与流式交互**：不依赖黑盒框架，开发基于 Thought-Action-Observation 范式的 ReAct 流水线和 XML 工具调用引擎。利用 SSE (Server-Sent Events) 实现在拦截 `<action>` 标签执行后台方法的同时，还能使前端打字机式流式渲染思考链 (`<think>`) 和状态栏。
4. **多算力/多模态引擎路由**：架构双引擎 LLM Factory，支持 OpenAI 接口与本地 Ollama 算力的动态热切换。集成 RapidOCR 处理图像/扫描版 PDF 进行视觉兜底 (Vision Fallback)。
5. **教研级启发式对话引擎 (Confusion Guard)**：在业务架构中深度融入教育学“最近发展区”理论。通过 `confusion_guard.py` 控制 AI 知识推导节奏（从符号认知到逻辑推导），禁止大模型“填鸭式”直接给出答案；并使用 LLM-as-a-Judge 架构 (Teaching Judge) 实现双模型博弈，强制评估并优化回传给用户的教学话术语气。

### 侧重 AI 应用/大模型落地方向
**项目名称**：基于 RAG 与 Agent 架构的智能伴学系统
**技术栈**：Python, RAG (pgvector), Ollama (DeepSeek/Qwen), Prompt Engineering, ReAct
**项目描述**：基于大模型技术从 0 开发的结构化知识伴聊系统，实现对用户长篇教辅资料的自主学习排期与答雷排雷功能。
**核心工作**：
1. **Agent 工作流与 Tool Calling**：脱离 LangChain 约束，原生实现基于 XML 指令的自定义 工具调用（Tool Calling）循环。模型自主判断何时调用 RAG 检索工具或 API 操作数据库，并在执行后将 `Observation` 注入上下文闭环。
2. **多态知识点图谱抽取**：基于页面结构化语义树自动抽取提纲、知识点及例题。根据用户的问答情况和模型自主下发的 XML Action `<UPDATE_KNOWLEDGE>` 实时修改前端掌握度状态。
3. **RAG 质量优化与幻觉阻断**：利用本地算力生成 Embedding，并在查询检索后施加 Prompt Context 约束拦截，避免通用大模型进行无中生有的解答，精确度与可用性大幅提升。
4. **动态知识图谱引擎 (Roadmap Mutation)**：区别于传统只能聊天的 RAG 平台，本系统赋予了模型实时重构学习路径的写权限。解析大模型输出的 `<ACTION>ADD_POINT` 等指令，在生成流式回复的同时，双向绑定并异步修改前端的 React 树状大纲。

---

## 4. STAR 面试法则表达示例 (讲述项目经历时使用)

### 情境 (Situation)
在传统网课和学习平台中，学生阅读长串资料感到枯燥，提问响应慢；此外由于单一机器性能弱，解析长文档（如百页 PDF）会使主线程崩溃；纯云端大模型费用又极为高昂，教育场景对数据隐私也有要求。

### 任务 (Task)
我需要从 0 到 1 架构一个能够拆解厚重书籍、动态生成复习路线，同时具备长记忆能力的平台。工程挑战上，我必须解决大文件上传解析导致的 API 阻塞异常，并实现一套能让模型自动调用外部工具的系统引擎。

### 行动 (Action)
*(参照上方简历核心工作，挑选最重要的说)*
1. **重构异步文件管道 (Redis Queue)**：接入 RQ 解耦文件切片与抽取，确保长文档解析时后端 API 异步响应，防止 HTTP 连接断开超时。
2. **构建自研 Tool Calling 引擎**：没有使用 LangChain 而是纯手搓了基于 XML 标签的动作拦截及执行引擎。大模型通过输出 `<action name="rag_search">` 来动态调取后端的 PostgreSQL pgvector 数据库。
3. **架构双引擎 (Dual-Engine)**：抽象 LLM Factory 服务实现流式调用，利用 OLLAMA 在本地兜底。引入 ONNX Runtime 的 RapidOCR 处理包含插图和复杂公式的图像 PDF。

### 结果 (Result)
* **抗压性显著提高**：大文档上传解析请求从原来的动辄 504 Timeout 转变为毫秒级返回任务 ID，重任务平滑排队。
* **扩展性与控制力极高**：自研的 XML 工具调用方式完美适配了不能支持结构化 JSON Function Calling 的本地开源小模型（如早期 Qwen 或 DeepSeek），使 Agent 的执行成功率提高了 100%。

---

## 5. 面试官必定“拷打”的题库与完美应对指南

*(前 5 题按上述版本保持不变... 以下新增关键题型)*

### ❓ 拷打 1：为什么要用 Redis Queue (RQ) 做文件异步？文件不大不能直接同步处理吗？
*(同上...)*

### ❓ 拷打 2：你的 RAG 检索为什么选 pgvector，没选 Milvus/Qdrant 等专属向量库？
*(同上...)*

### ❓ 拷打 3：你手写 Agent 逻辑？使用现成的 LangChain / LlamaIndex 不是更容易吗？
*(同上...)*

### ❓ 拷打 4：大文件处理中怎么解决大模型幻觉与上下文长度限制？
*(同上...)*

### ❓ 拷打 5：谈谈前端流式对话（Streaming / SSE）实现中遇到过哪些坑？
*(同上...)*



### ❓ 拷打 6：你是怎么实现大模型工具调用 (Tool Calling) 的？为什么不用 OpenAI 原生的 Function Calling API？
*(原文已有...)*

### ❓ 拷打 7：你项目里的“苏格拉底启发式教学引擎 (Confusion Guard)”具体是怎么做的？和写个 Prompt 提示词有什么区别？
*   **面试官考察动机**：考察你在垂直业务场景（教育/客服等）中，是否只会粗暴地写 Prompt，还是有更深层的代码控制流和状态机设计思维。
*   **完美回答**：
    “单纯靠 System Prompt 让大模型‘像老师一样启发式提问’极不稳定，聊两轮模型就会妥协直接把答案丢给学生。我因此抛弃了纯 Prompt 方案，改用代码层的**状态机与判定路由 (Confusion Guard)** 来做强约束。
    1. **认知分层**：我们在代码里把知识理解分为四个递进层级：符号 (`symbol`) -> 量词 (`quantifier`) -> 依赖 (`dependency`) -> 证明 (`proof`)。
    2. **进度锁定**：在 `Thread` 记忆上下文中记录学生当前的认知层级。如果学生还在问基本符号是什么意思，代码层面的 `confusion_rules` 会直接拦截并修改 LLM 的生成条件，绝不允许模型输出任何包含高级 `proof`（证明逻辑） 的内容。
    3. **双模型裁判 (Teaching Judge)**：为了保证语气的绝对师者风范，我采用了 LLM-as-a-Judge 框架。后台让低成本小模型生成两个不同版本的教学回复，然后让裁判模型进行打分，挑选出‘最不急躁、最循循善诱’的那一条再推给前端。这种**工程化护栏 + 双路博弈**，是单靠几句 Prompt 绝对做不到的。”

### ❓ 拷打 8：RAG 文档解析怎么处理图片 PDF 或者扫描件？
*   **面试官考察动机**：考验 RAG 项目中至关重要的 Document Parsing（文档后处理）真实经验。
*   **完美回答**：
    “纯文本提取库遇到扫描版的教辅资料会全部抓瞎。我的策略是**先尝试提取文本，检测到无本或乱码比例过高时，自动走视觉降级通道 (OCR Fallback)**。
    为了贯彻极轻量、去云端依赖的策略，我没有选择调公有云 OCR。而是直接使用 `PyMuPDF (fitz)` 将 PDF 页面按 300 DPI 渲染成高分辨率位图，然后送入基于 ONNX Runtime 的 `RapidOCR` 引擎进行纯本地推理。
    同时，我编写了一层专门针对教育教辅资料的后置清洗 Pipeline，包含垂直文本纠偏、去除因为 OCR 导致的多余换行符。这一层清洗使得我的检索入库 Embedding 的向量质量提升了极大台阶，直接决定了检索不会拿满屏乱码去喂给生成模型。”

