# AI Study Agent (AI 期末复习助手) 

> **从资料提取器到高并发双擎智能教学参谋的跨越进化。 (V3.0)**

这是一个专为期末复习设计的智能 Agent 系统。它不仅能够解析 PDF/PPT 资料自动规划结构化的教学路径，还在最新的 V3.0 架构中引入了 **云端/本地双擎 LLM 切换**、**Redis 异步并发消息队列** 以及 **基于 PGVector 的企业级 RAG 向量混合检索**，并全面重构为**领域驱动设计 (DDD)** 的现代化后端架构。

---

## 🌟 核心亮点 (Core Highlights)

### 1. 结构化教学路径与动态追踪 (Pedagogical Roadmap)
系统将冰冷的文档萃取并转化为 **卡片式交互布局**。每个卡片（章节）包含：
- **核心知识点 (Points)**: 细粒度的定义、定理、公式。
- **典型例题 (Examples)**: 从文档提取且带有分步详解的练习题。
- **掌握度评估 (Mastery)**: 实时记录并可视化每个知识点的复习进度。

### 2. 双引擎配置系统 (Dual-Engine LLM Factory)
- **对话推理 (Generation)**: 前端支持无缝切换 **Local (本地 Ollama)** 与 **Cloud (云端 API，如 DeepSeek/OpenAI)**，并自动对齐不同端返回的 <think> 思考流。
- **向量锁定 (Embedding Guard)**: 无论对话端用什么模型，所有知识文档一律经由本地的 
omic-embed-text 转化为 768 维向量，彻底保障数据隐私，免除云端 Embedding 高额计费。

### 3. 企业级 RAG 架构 (Enterprise RAG Base)
- **基于 PostgreSQL + PGVector**: 极速的余弦相似度（Cosine Distance）检索，彻底抛弃老旧的内存或纯文本检索机制。
- **混合上下文注入 (Context Injection)**: 用户在主线/支线聊天框中的每一次发问，都会先经由 pgvector 捞出最为贴合的 Top-K 知识切片，有效杜绝大模型脱离教材胡说八道。

### 4. 高并发文件解析队列 (Async Message Queue & Map-Reduce)
- **Redis & RQ**: 摒弃了早期 FastAPI 阻塞式单线程文档解析（容易超时崩溃），将沉重的 PDF 多模态拆分动作压入 Redis 队列中后台消费。
- **Map-Reduce 切块处理**: 针对长文档和大尺寸 PDF，系统自动对内容进行切块（Chunking）分批交给 LLM 解析，最后通过 Map-Reduce 归并，彻底解决了大型教材带来的 Token 溢出与注意力崩溃问题。
- **前端状态轮询**: 前端根据 job_id 发起轮询并辅以极具质感的动态加载 UI，确保大文件的高并发安全。

### 5. 动态双线互动对话 (Dual-Thread Socratic Chat)
- **主线大纲控制 (Main Thread Mutation)**: 利用大模型的 XML 指令 <ACTION> 拦截输出，实现页面前端路线图的自发增修。
- **支线苏格拉底私教 (Branch Tutoring)**: 具有全局和原子的下钻能力，用引导式教育取代直接送答案。

---

## 🛠 技术栈 (Tech Stack)

### Backend (Python 3.12+, FastAPI)
- **核心框架**: FastAPI (领域驱动分层架构)
- **数据库**: PostgreSQL + PGVector + SQLAlchemy (ORM)
- **缓存与队列**: Redis + RQ (Redis Queue)
- **LLM 层**: OpenAI API (云端兼容) + Requests/Ollama (本地化服务层)
- **文档解析**: PyMuPDF (fitz), python-pptx, pytesseract

### Frontend (React 18 + Vite)
- **核心框架**: React 18
- **通讯协议**: Axios, Server-Sent Events (SSE 流式输出)
- **UI & 样式**: Tailwind CSS (磨砂玻璃质感、无级响应式组件)
- **状态管理**: React Hooks + 定时器轮询机制

---

## 📂 领域驱动架构 (Domain-Driven Architecture)

在 V3.0 中，后端经历了彻底的模块化重构，严格遵循关注点分离原则：

`	ext
backend/
├── api/routers/      # API 路由层 (chat, files, spaces, threads) - 处理 HTTP 请求
├── core/             # 核心配置与资源层 (db, redis_client, llm_factory) - 全局单例与基础组件
├── models/           # 数据模型层
│   ├── database.py   # SQLAlchemy ORM 实体表模型
│   └── schemas/      # Pydantic 数据验证结构 (Request/Response 模型)
├── services/         # 业务逻辑层 (rag_service, upload_service, agent_controller 等)
├── worker/           # 后台任务层 (rq_worker, 队列监听控制)
├── utils/            # 无状态工具类 (parsing, embedding)
├── constants/        # 系统常量与枚举 (教学目标、风格、策略等)
└── scripts/          # 初始化、迁移、测试脚本与调试工具
`

---

## 🚀 快速开始 (Quick Start)

### 1. 容器及数据库准备 (推荐 Docker)
确保安装了 Docker，并运行一个带有 pgvector 的隔离环境（使用 5433 端口防冲突）：
`ash
docker run --name pgvector-db-final -e POSTGRES_PASSWORD=251399 -e POSTGRES_DB=ai_study_agent -p 5433:5432 -d timescale/timescaledb-ha:pg16
`
*(同时需要启动一个原生的 Redis 容器服务，绑定默认的 6379 端口以作任务队列)*

### 2. 本地 LLM 环境安装
系统重度依赖本地模型进行向量化和本地推演。请安装 [Ollama](https://ollama.com/) 并在后台挂起：
`ash
# 获取默认推理模型（按需可调整）
ollama pull deepseek-r1:7b
# [必须] 获取统一配置的词嵌入模型 
ollama pull nomic-embed-text
`

### 3. 后端启动
进入 ackend 目录，安装并激活环境：
`ash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
`
初始化表结构 (重要: 现在位于脚本层)：
`ash
python scripts/init_db.py
`
启动 FastAPI API 服务：
`ash
uvicorn app:app --reload --port 8000
`
**启动 RQ 后台消费服务 (新终端中运行)**：
`ash
cd backend
.venv\Scripts\activate
python worker/rq_worker.py
`

### 4. 前端启动
进入 rontend 目录：
`ash
npm install
npm run dev
`
访问 http://localhost:5173 体验沉浸式学习空间。

---

## 🔮 演进路线 (Roadmap - V4.0)

- [ ] **CoT 提取可视化体系**: 针对更强算力的 R1 级思考流 <think>，实装可折叠、强动态的解析器悬浮组件。
- [ ] **Tool-use Agent 架构**: 根据 AGENT_ARCHITECTURE_PLAN.md 引入 ReAct 多模态思维器，支持代码执行、Web 检索沙盒机制。
- [ ] **多模态考卷生成**: 从目前的内容总结进阶为真正的全真模拟考卷自动化生成器。
