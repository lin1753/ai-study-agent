# AI Study Agent - 接口文档 (API Reference V3.0)

该文档整理了最新重构后的 `backend/routers/` 目录下所有的核心 API 路由及相关说明。项目基于 FastAPI 框架开发，采用了云端/本地双擎 LLM 和基于 Redis 的队列机制。

## 基础地址 (Base URL)
默认情况下：`http://localhost:8000` (或您配置的实际服务端口)

---

## 1. 空间管理 (Spaces) -> `routers/spaces.py`

科目空间（Space）是隔离不同学习科目的顶层容器。

### 1.1 创建科目空间
* **URL**: `/spaces`
* **Method**: `POST`
* **Request Body**:
  ```json
  { "name": "高等数学" }
  ```
* **说明**: 创建空间时会自动关联主线对话 (MainThread)。

### 1.2 获取所有科目空间
* **URL**: `/spaces`
* **Method**: `GET`
* **Response**: `200 OK`

### 1.3 更新空间配置 (双引擎大模型配置)
* **URL**: `/spaces/{space_id}/config`
* **Method**: `PUT`
* **Request Body**:
  ```json
  {
    "priority_chapters": ["第一章", "第二章"],
    "llm_provider": "cloud",
    "llm_api_key": "sk-your-key",
    "llm_base_url": "https://api.deepseek.com/v1",
    "llm_model": "deepseek-chat"
  }
  ```
* **说明**: 客户端可通过此接口随时热切换底层运算是靠本地 Ollama 还是外部云引擎。

---

## 2. 资料上传与知识 RAG 切片 (Files) -> `routers/files.py`

### 2.1 异步上传学习资料 (PDF/PPT)
* **URL**: `/spaces/{space_id}/upload`
* **Method**: `POST`
* **Content-Type**: `multipart/form-data`
* **Form-Data**:
  * `file`: (Binary File - PDF或PPT)
* **Response**: `202 Accepted`
  ```json
  {
    "job_id": "redis_task_id",
    "message": "File uploaded, processing started in background."
  }
  ```
* **说明**: 将大文件解析任务压入 Redis Queue 进行异步处理，解决超时问题。同时文本将被 `nomic-embed-text` 切块存入 PostgreSQL (pgvector)。

### 2.2 轮询解析状态
* **URL**: `/spaces/{space_id}/upload/status/{job_id}`
* **Method**: `GET`
* **Response**: `200 OK`
  ```json
  { "status": "finished", "result": "Success" }
  ```

---

## 3. RAG 加持大模型对话 (Chat) -> `routers/chat.py`

### 3.1 主线全局对话 (Streaming)
* **URL**: `/chat/main`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "thread_id": "main_thread_uuid",
    "content": "请帮我复习第一章内容"
  }
  ```
* **Response**: `text/event-stream` (SSE)
* **说明**: 在将消息交给 LLM 之前，系统会调取 `rag_service.py` 将用户问题转化为高维向量，在 PostgreSQL 中执行相似度检索，找回资料片段一同注入给大模型。流式回复过程中系统支持识别 `<ACTION>` XML 指令动态改变前端大纲视图。

### 3.2 支线私教对话 (Streaming)
* **URL**: `/chat/stream`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "thread_id": "branch_thread_uuid",
    "content": "我推导出来等于 1，对吗？"
  }
  ```
* **Response**: `text/event-stream` (SSE)

---

## 4. 对话分支维护 (Threads) -> `routers/threads.py`

### 4.1 获取主线复习大纲
* **URL**: `/spaces/{space_id}/main_thread`
* **Method**: `GET`
* **Response**: `200 OK`

### 4.2 创建分支对话
* **URL**: `/threads/branch`
* **Method**: `POST`
* **Request Body**:
  ```json
  {
    "space_id": "space_uuid",
    "context": "具体的知识点文本段落...",
    "title": "泰勒展开式"
  }
  ```
* **说明**: 如果没有对应该知识点的历史聊天室，则新建，并通过底层基建运算保存该段落锚点的 Embedding，保障支线知识连续性。
