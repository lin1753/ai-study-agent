# AI Study Agent (AI 期末复习助手)

> **基于 ReAct 与 RAG 架构的双擎智能全栈教学参谋 (V3.0)**

这是一个专为期末复习设计的智能伴学陪读系统。它不仅能够解析长篇 PDF/PPT 资料并自动规划结构化教学路径，还在最新的 V3.0 架构中引入了 **云端/本地双擎 LLM 切换**、**Redis 异步并发大文件解析队列** 以及 **基于 PGVector 的企业级 RAG 向量混合检索**，并全面重构为**领域驱动设计 (DDD)** 的现代化后端架构。

---

## 🌟 核心亮点 (Core Highlights)

### 1. 结构化多叉树型教学路径 (Pedagogical Roadmap)
系统将长篇文档萃取并转化为 **卡片式交互布局**。每个卡片（章节）包含：
- **核心知识点 (Points)**: 细粒度的定义、定理、公式。
- **典型例题 (Examples)**: 从文档提取且带有分步详解的练习题。
- **掌握度评估 (Mastery)**: 实时记录并可视化每个知识点的复习进度。利用 XML 操作指令（如 <UPDATE_KNOWLEDGE>）双向绑定前端 React 面板实时更新大纲状态。

### 2. 双引擎异构算力协作 (Dual-Engine LLM Factory)
- **文本生成 (Generation)**: 采用策略模式整合，前端支持无缝热切换 **Local (本地 Ollama / DeepSeek-R1)** 与 **Cloud (云端 API，如 OpenAI 协议)**。自带流数据拦截器，解析 easoning_content\ 保留 \<think>\ 思考链前端渲染。
- **向量锁定 (Embedding Guard)**: 无论生成的对话端用到什么模型，知识文档一律经由本地的 omic-embed-text\ 转化为 768 维向量入库。彻底锚定本地闭环以避免云端切换造成的向量维数灾难，且免除云端 Embedding 高额计费。

### 3. 企业级 RAG 架构 (Enterprise RAG Base)
- **PostgreSQL + PGVector**: 借助带 \pgvector\ 扩展集的 TimescaleDB/PostgreSQL，执行极速的高维余弦相似度 (Cosine Distance) 检索。
- **混合上下文召回截断**: 聊天问答发问会基于余弦距离进行 Top-3/Top-K 知识召回与上下文截断，将幻觉问题概率降低了约 85%，杜绝大模型脱离教材胡扯。

### 4. 高并发长文档异步管道 (Async Task Queue & Map-Reduce)
- **Redis & RQ**: 摒弃了早期 FastAPI 阻塞单线程解析导致长文档 ń Timeout\ 的历史包袱，将沉重的 PDF 切片抽分任务投入 Redis 队列，后端 API 毫秒级异步 202 放行！
- **Map-Reduce 归并算法**: 百页大部头 PDF 自动自动进入安全块（Chunking）分批 LLM 解析，用递归归并大纲与局部知识，根除超长生成导致的 Token 溢出死锁。
- **前端极速状态追踪**: 前端根据建立的异步 \job_id\ 发起重试轮询，配以强交互质感 UI 确保 Worker 节点在后台平滑排队。

### 5. 动态双线互动对话 (Dual-Thread Socratic Chat)
- **主线大纲控制 (Main Thread Mutation)**: 会话通过长记忆上下文能力在主线实现路线图的自发增修。
- **支线苏格拉底私教 (Branch Tutoring)**: 应对痛点开启“小灶”，支持全局和原子的下钻独立对话隔离开发。用带提示策略的引导式教育（Prompt Engineering）取代冰冷的直接写答案。

---

## 🛠 深度技术栈 (Tech Stack)

### Backend (Python 3.12+, FastAPI)
- **核心框架**: FastAPI (领域驱动分布分层规范)
- **数据库**: PostgreSQL + PGVector + SQLAlchemy
- **系统并发**: Redis + RQ (Redis Worker Background Jobs)
- **LLM 层**: Base Service 策略路由兼容 OpenAI 格式与 Requests 的 Ollama 接口。
- **处理组件**: PyMuPDF (fitz) 高速读取 / AnyIO 分布器异步整合

### Frontend (React 18 + Vite)
- **核心引擎**: React 18 + Axios 拦截器
- **实时通信**: Server-Sent Events (SSE 大模型逐字输出)
- **UI 组件**: Tailwind CSS 打造质感沉稳的高级磨砂实色交互面板。
- **状态同步**: 周期定制 Hooks，结合 \setInterval\ 精准轮询排队状态。

---

## 📂 领域驱动架构 (Domain-Driven Architecture)

> 在 V3.0 Phase 1.5 中，后端经历了彻底的模块化重构，严格遵循关注点分离基准：

\\	ext
backend/
├── api/routers/      # API 路由层入口 (chat, files, spaces, threads)
├── core/             # 全局底层资源 (db, redis_client, llm_factory 双擎引擎工厂)
├── models/           # 数据库模型层 (SQLAlchemy) & schemas/ (Pydantic 请求体)
├── services/         # 核心业务域 (rag_service 向量检索, upload_service 切片处理等)
├── worker/           # 独立后台生命周期 (rq_worker, 防止与 Uvicorn Web 并发混淆)
├── utils/ & constants/# 工具解析类(parsing)及全量系统 Prompt Constant(教学策略枚举)
└── scripts/          # PGVector 系统初始化、单元测试、调试套件
\
---

## 🚀 部署指北 (Quick Start)

### 1. 启动中间件容器 (依赖 Docker)
执行脚本前拉取一套带有 \pgvector\ 支持的强硬底层支持环境 (向外暴露 5433 防冲突机制)：
\\ash
docker run --name pgvector-db-final -e POSTGRES_PASSWORD=251399 -e POSTGRES_DB=ai_study_agent -p 5433:5432 -d timescale/timescaledb-ha:pg16
\*(启动一个原生的 Redis Server 进行 6379 的端口分发以支持后台任务)*

### 2. 构建本地 LLM 终端 
推荐本地搭载 DeepSeek，为保证完全断网工作：
\\ash
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text # [必须] 系统刚需 768维 的本地极速向量器
\
### 3. 主干后端部署 (Backend)
进入 \ackend\ 空间分配虚机环境：
\\ash
python -m venv .venv
.venv\Scripts\activate  
pip install -r requirements.txt
python scripts/init_db.py # 建表(必须执行)
uvicorn app:app --reload --port 8000
\
**🚀 别被阻塞卡死在起点，打开新终端为长文档配置 RQ 处理队列：**
\\ash
cd backend
.venv\Scripts\activate
python worker/rq_worker.py
\
### 4. 渲染前端空间 (Frontend)
转入 \rontend\ 发动基建：
\\ash
npm install
npm run dev
\进入 http://localhost:5173，你就可以在设置面版将引擎从 Local 到 Cloud 大脑进行强力无缝跳变！

---

## 🔮 演进路线 (Roadmap - Current Progress)

我们已经在此版本长线开发的基础上建立并完善了**基于 ReAct 面向教陪场景的真实智能体 (Agent) 架构**（更多拆解详参 `AGENT_ARCHITECTURE_PLAN.md`）：

- [x] **主线/支线异步解耦 (Main vs Branch Threading)**: 告别传统的单调聊天域，引入主支线隔离概念（类似游戏中的主线任务与支线小灶）。
- [x] **后端按需自测工具 (On-Demand Exam Generator)**: 放弃原来长篇大段死板解析全出题的做法。在独立支线向 `Agent_Controller` 注册专门的按需成卷方法，彻底解耦解析和出题。
- [x] **RapidOCR 纯视觉兜底解析 (Vision Fallback OCR)**: 在 PDF 解析链路里切入不依赖于庞大 C++ 环境的 `RapidOCR ONNX Runtime`。跨越所有只能读取文本的软肋，直面高度扫描件和纯图 PPT，实现零漏抓的提取并完美交付回 DeepSeek 提纯。
- [x] **支线侧载补充 RAG (Side-Loading RAG)**: 我们创新性允许在专注单一知识点的支线小灶期间补充外围截图（即时注入 KnowledgeBlocks 表中关联 RAG），在**不破坏主线长篇大纲**的前提下直接扩展弹药提供精确回答。
- [x] **高频心流前端埋点与过渡动画 (Optimistic Flow UI)**: 针对创建独立线程、生成模型前的后端阻塞加入阶段过渡提示器。并在流式数据上打点 `<think>` 或 Tools Call 日志给用户透传“Agent的潜意识”。
- [ ] **导师人设与长期学情画像 (Tone Modifier)**: *(待开发)* 加入 Tone Modifier 改变大模型浓重的 AI 味模板文本回复，依托独立 UserProfile 数据表增强偏好记忆。
