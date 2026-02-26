# AI Study Agent (AI 期末复习助手) 

> **从资料提取器到高并发双擎智能教学参谋的跨越进化。 (V3.0)**

这是一个专为期末复习设计的智能 Agent 系统。它不仅能够解析 PDF/PPT 资料自动规划结构化的教学路径，还在最新的 V3.0 架构中引入了 **云端/本地双擎 LLM 切换**、**Redis 异步并发消息队列** 以及 **基于 PGVector 的企业级 RAG 向量混合检索**。

---

##  核心亮点 (Core Highlights)

### 1. 结构化教学路径与动态追踪 (Pedagogical Roadmap)
系统将冰冷的文档萃取并转化为 **卡片式交互布局**。每个卡片（章节）包含：
- **核心知识点 (Points)**: 细粒度的定义、定理、公式。
- **典型例题 (Examples)**: 从文档提取且带有分步详解的练习题。
- **掌握度评估 (Mastery)**: 实时记录并可视化每个知识点的复习进度。

### 2. 双引擎配置系统 (Dual-Engine LLM Factory)
- **对话推理 (Generation)**: 前端支持无缝切换 **Local (本地 Ollama)** 与 **Cloud (云端 API，如 DeepSeek)**，并自动对齐不同端返回的 <think> 思考流。
- **向量锁定 (Embedding Guard)**: 无论对话端用什么模型，所有知识文档一律经由本地的 
omic-embed-text 转化为 768 维向量，彻底保障数据隐私，免除云端 Embedding 高额计费。

### 3. 企业级 RAG 架构 (Enterprise RAG Base)
- **基于 PostgreSQL + PGVector**: 极速的余弦相似度（Cosine Distance）检索，彻底抛弃老旧的内存或纯文本检索机制。
- **混合上下文注入 (Context Injection)**: 用户在主线/支线聊天框中的每一次发问，都会先经由 pgvector 捞出最为贴合的 Top-K 知识切片，有效杜绝大模型脱离教材胡说八道。

### 4. 高并发文件解析队列 (Async Message Queue)
- **Redis & RQ**: 摒弃了早期 FastAPI 阻塞式单线程文档解析（容易超时崩溃），将沉重的 PDF 多模态拆分动作压入 Redis 队列中后台消费。
- **前端状态轮询**: 前端根据 job_id 发起轮询并辅以极具质感的动态加载 UI，确保大文件的高并发安全。

### 5. 动态双线互动对话 (Dual-Thread Socratic Chat)
- **主线大纲控制 (Main Thread Mutation)**: 利用大模型的 XML 指令 <ACTION> 拦截输出，实现页面前端路线图的自发增修。
- **支线苏格拉底私教 (Branch Tutoring)**: 具有全局和原子的下钻能力，用引导式教育取代直接送答案。

---

##  技术栈 (Tech Stack)

### Backend (Python 3.10+, FastAPI)
- **核心框架**: FastAPI (通过 APIRouter 模块化组织)
- **数据库**: PostgreSQL + PGVector (经 Docker 部署) + SQLAlchemy 
- **缓存与队列**: Redis + RQ (Redis Queue)
- **LLM 层**: openai (云端兼容) + 
equests (本地 Ollama 本地化服务层)
- **解析器**: PyMuPDF (itz), python-pptx, pytesseract.

### Frontend (React + Vite)
- **框架**: React 18 
- **通讯**: Axios, Server-Sent Events (SSE 流式输出)
- **样式**: Tailwind CSS (去除了刺眼的渐变色，统一采用了质感的毛玻璃与沉稳的高级实色面板)
- **状态管理**: React Hooks + setInterval 定时器轮询设计。

---

##  系统架构 (Architecture)

### 模块解耦概览
- **
outers/**: chat.py, iles.py, spaces.py, 	hreads.py 严格分离 API 职责。
- **services/**: 存放业务核心。例如 upload_service.py (处理切分策略与 Redis), 
ag_service.py (PGVector 检索逻辑)。
- **schemas/**: Pydantic 数据参数防腐层。
- **llm_service.py (Factory)**: 融合父类 CloudAPIService 覆盖本地 OllamaService 实现任意时刻拔插切换。

---

##  快速开始 (Quick Start)

### 1. 容器及数据库准备 (基于 Docker)
确保安装了 Docker，并运行一个带有 pgvector 的隔离环境（我们使用的映射端口为 5433，以防与原生系统库冲突）：
`ash
docker run --name pgvector-db-final -e POSTGRES_PASSWORD=251399 -e POSTGRES_DB=ai_study_agent -p 5433:5432 -d timescale/timescaledb-ha:pg16
`
*(另外您还需要启动一个原生的 Redis 容器服务绑定 6379 端口作任务队列使用)*

### 2. 本地 LLM 环境安装
确保安装 [Ollama](https://ollama.com/)，在后台保持运行，并提前准备好两个本地基石模型：
`ash
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text
`

### 3. 后端启动
进入 ackend 目录，安装依赖：
`ash
pip install -r requirements.txt
`
如果首次启动新库，请初始化表：
`ash
python init_db.py
`
启动 FastAPI 服务：
`ash
uvicorn app:app --reload --port 8000
`

### 4. 前端启动
进入 rontend 目录：
`ash
npm install
npm run dev
`
访问 http://localhost:5173。进入新增科目，您可以在设置弹窗中将 AI Engine 随时在 Local 与 Cloud API 之间反复横跳！

---

##  未来规划 (Roadmap - V4.0)
- [ ] **全项目 Docker Compose 化**: 前端、后端、数据库、Redis 全部抽进统一的 Compose 面板。
- [ ] **CoT 提取可视化体系**: 对于更强算力的 R1 思维链 <think>，实装可折叠的解析器组件。
- [ ] **PDF 高亮锚点溯源**: 加入原文追溯，利用获取的 embedding 出处映射回源文档位置。