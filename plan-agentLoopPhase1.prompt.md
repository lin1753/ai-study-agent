## 优化方案：Agent 云端 API 兼容性修复 (generate_raw)

### 背景
在使用 NVIDIA Cloud API 进行 PDF 解析时，遇到请求耗时 0.43s 直接返回失败，且未正确解析出主线。
经查，核心原因为 StudyAgent (backend/agent_controller.py) 的 _call_llm_raw 方法中，硬编码了针对本地 Ollama API 的请求 (/api/generate) ，以及发生了错误的属性引用 (self.llm.model_name，针对云端应该为 self.model)，从而绕过了标准的请求管道体系。这在云端 API 部署时直接导致 AttributeError 闪退崩溃。

### 优化设计
建立统一的一般性纯文本对话生成方法 generate_raw。分离本地及云端的差异化请求，避免上层 Agent 直接处理底层 HTTP 通信：

1. 接口层升级 (BaseLLMService)
   在 backend/llm_service.py 的基类中定义抽象方法。
   
2. 本地模型适配 (OllamaService)
   封装向本地代理发起的 /api/generate 的 POST 请求。

3. 云侧模型适配 (CloudAPIService)
   调用兼容 OpenAI 消息结构的 /chat/completions 端点。将文本组装为 messages=role: user。

4. 解耦代理引擎 (StudyAgent)
   清理 backend/agent_controller.py 的臃肿网络代码，改为调用 self.llm.generate_raw。
