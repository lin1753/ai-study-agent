# AI 个人助教（AI Study Agent）简历项目包装设计

## 1. 项目简介（一句话概括）
**基于 FastAPI + RAG + Docker + Redis 异步架构重构的智能伴学陪读全栈应用。**
通过云端大模型与本地 Ollama (DeepSeek-R1) 异构算力协作，实现长篇 PDF/PPT 等文档的向量化拆分检索（RAG）、知识图谱动态渲染和大模型引导式苏格拉底教学引擎。

## 2. 核心亮点（用于筛选简历的关键词提取）
* **基础架构**: Python, FastAPI, React, PostgreSQL/TimescaleDB
* **工程架构**: 基于 Redis 的异步任务队列(Task Queue)、RAG (pgvector 余弦相似度检索)、双引擎 LLM (流式通信 / Server-Sent Events (SSE))。
* **大模型能力**: Prompt Engineering、多轮对话状态追踪（Thread Stateful）、知识抽取、XML 控制流指令（Agent Action）。

## 3. STAR 面试法则表达示例

### 情境 (Situation)
* 在传统网课和学习平台中，学生阅读长串资料感到枯燥，提问响应慢；此外由于单一机器性能弱，解析长文档（如百页 PDF）会使主线程崩溃；纯云端大模型费用又极为高昂。

### 任务 (Task)
* 利用最新开源模型技术（DeepSeek / OpenAI），我需要独立从0到1架构一个可以拆解厚重书籍并动态生成多叉树型复习路线，能够根据难点开小灶（支线独立对话）并具备长记忆上下文能力的平台。要求同时解决文件上传超时、API调用阻断等高并发异常体验，实现全系统高可用和知识无缝 RAG。

### 行动 (Action)
1. **重构异步文件管道 (Redis Queue)**：接入 RQ（Redis Queue）解耦文件切片与抽取，确保 100 页以上大范围 PDF 解析时后端 API 能 202 异步放行，防止连接断开。前后端采用状态重试轮询设计获取进度。
2. **构建企业级 RAG (PostgreSQL pgvector)**：借助 Docker 部署带有 pgvector 扩展的 PostgreSQL，将 
omic-embed-text 生成的高维向量（768维）通过 SQLAlchemy 入库，并在会话发生前基于余弦距离 cosine_distance 进行 Top-3 的知识召回与上下文截断。
3. **架构双引擎路由基建 (Dual-Engine LLM Factory & Vision Fallback)**：利用策略模式整合云端 API（OpenAI协议）和本地 Ollama 终端引擎。创新性地使文本生成支持动态热切换云/地算力，而向量化 Embedding强锚定到本地闭环以避免云端切换造成的向量维数灾难。同时引入基于 ONNX Runtime 的 RapidOCR作为视觉兜底引擎（Vision Fallback），解决高度图像化的 PDF/PPT 的结构化提取。
4. **前端流式图谱与心流引擎 (Optimistic UI)**: 实现响应拦截与多阶段状态流转。通过解析流数据的 reasoning_content 保留 <think> 思考链显示；在耗时的支线 RAG 线程创建期采用“骨架屏+呼吸占位文案”防死机补偿；通过检测 XML 操作（如：<UPDATE_KNOWLEDGE>）来双向绑定前端 React 面板实时更新大纲状态。

### 结果 (Result)
* 平台抗压性明显提高：大文档解析请求从原来的 504 Timeout 转变为毫秒级相应并依托 Worker 节点在后台平滑排队。
* 显著改善生成事实与精准度：pgvector 根据 RAG 的关联截断输入将幻觉问题概率降低了约 85%，有效提升教育垂直场景的专业问答能力。
* TCO 成本下降：由于利用大显存设备本地完成高能耗向量构建任务，节约了云端算力消耗，并兼容了未来灵活替换底层商业模型（如将DeepSeek-v3换用其他厂商）的能力。
