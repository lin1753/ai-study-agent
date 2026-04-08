import requests
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Generator

logger = logging.getLogger(__name__)

class BaseLLMService(ABC):
    @abstractmethod
    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        pass

    @abstractmethod
    def generate_roadmap(self, text: str) -> list:
        pass

    @abstractmethod
    def generate_raw(self, prompt: str, temperature: float = 0.3) -> str:
        pass

    @abstractmethod
    def generate_summary(self, text: str) -> str:
        pass

    @abstractmethod
    def check_connection(self) -> bool:
        pass

    @abstractmethod
    def analyze_page(self, page_text: str, previous_chapter: str, user_config: dict = None) -> dict:
        pass

    @abstractmethod
    def generate_exam_quiz(self, roadmap_json: str, user_config: dict) -> list:
        pass

class OllamaService(BaseLLMService):
    def __init__(self, model: str = "deepseek-r1:7b", embed_model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.model = model
        self.embed_model = embed_model
        self.base_url = base_url

    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        try:
            with requests.post(url, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        body = json.loads(line)
                        if "message" in body and "content" in body["message"]:
                            yield body["message"]["content"]
                        if body.get("done", False):
                            break
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama: {str(e)}")
            yield f"Error communicating with Ollama: {str(e)}"

    def generate_raw(self, prompt: str, temperature: float = 0.3) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Error in generate_raw: {e}")
            return f"Error: {str(e)}"

    def generate_summary(self, text: str) -> str:
        url = f"{self.base_url}/api/generate"
        logger.debug(f"Generating summary for text (len={len(text)})...")
        prompt = f"请总结以下内容的知识点，提取核心概念，保持简洁：\n\n{text}"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120) 
            response.raise_for_status()
            res_text = response.json().get("response", "")
            logger.debug(f"Summary generated (len={len(res_text)}): {res_text[:50]}...")
            return res_text
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError: Ollama is not running.")
            return "Error: 无法连接到本地大模型。请确保 Ollama 已经启动并在 11434 端口运行。"
        except Exception as e:
            logger.error(f"Generate summary failed: {e}")
            return f"Error generating summary: {str(e)}"

    def check_connection(self) -> bool:
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=5)
            # Only return true if 200 OK
            return res.status_code == 200
        except Exception as e:
            logger.error(f"[Ollama] Connection check failed: {e}")
            return False

    def analyze_page(self, page_text: str, previous_chapter: str, user_config: dict = None) -> dict:
        """
        Atomic Page Analysis: Analyzes a single page of text to extract knowledge points and examples,
        and determines if it belongs to the previous chapter or a new one.
        """
        # Read from config if provided
        model_name = self.model
        if user_config and user_config.get("llm_provider") == "local" and user_config.get("local_model_name"):
            model_name = user_config.get("local_model_name")
            
        url = f"{self.base_url}/api/generate"
        
        prompt = f"""你是一个课程梳理专家。请分析以下PPT/PDF的【单页】内容，并提取原子知识点。
如果该页没有实质内容（如仅为目录或空白），可留空。

上一页所属章节名称：{previous_chapter if previous_chapter else "无"}

当前页内容：
{page_text}

请严格输出一段纯JSON格式（绝对不能包含 ```json 标签或 <think> 内容）：
{{
    "chapter_title": "当前页的章节标题（可沿用上一页的名称，如果发现明显是新章节则命名新的）",
    "points": [
        {{"name": "概念名称", "content": "详细的一句话解释", "importance": 3, "original_questions": ["在此概念附近发现的原题/习题1", "原想2"]}}
    ],
    "examples": [
        {{"question": "必须100%来自原文的例题题干（如果没有这页则返回空）", "solution": "严格使用原文解答"}}
    ]
}}
"""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            res = requests.post(url, json=payload, timeout=120)
            res.raise_for_status()
            res_text = res.json().get("response", "")
            
            # Remove <think> tags for DeepSeek
            import re
            cleaned_text = re.sub(r'<think>.*?</think>', '', res_text, flags=re.DOTALL)
            
            # Find JSON block
            match = re.search(r'\{.*\}', cleaned_text.replace("```json", "").replace("```", ""), re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {"chapter_title": previous_chapter or "未分类", "points": [], "examples": []}
            
        except Exception as e:
            logger.error(f"[Ollama] analyze_page failed: {e}")
            return {"chapter_title": previous_chapter or "未分类", "points": [], "examples": []}

    def ocr_image(self, image_bytes: bytes) -> str:
        import base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        url = f"{self.base_url}/api/generate"
        prompt = "识别并转录图片中的所有文字，保持原有排版。不要输出任何解释性文字，只输出识别内容。"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [base64_image],
            "stream": False
        }
        
        logger.debug("Sending image to LLM for OCR...")
        try:
            response = requests.post(url, json=payload, timeout=180) 
            if response.status_code != 200:
                logger.error(f"Ollama OCR returned {response.status_code}: {response.text}")
                return ""
            res_text = response.json().get("response", "")
            logger.debug(f"OCR result (len={len(res_text)}): {res_text[:50]}...")
            return res_text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def generate_exam_quiz(self, roadmap_json: str, user_config: dict) -> list:
        url = f"{self.base_url}/api/generate"
        weight_context = self._build_config_context(user_config) if user_config else "默认出题均衡"
        
        prompt = f"""你是一个资深的考卷出题专家。请根据以下大纲知识点和用户指定的【考试题型权重】，出一套高还原度的课后测验题。
        
【用户考试题型偏好】:
{weight_context}

【知识点大纲】:
{roadmap_json}

请严格输出合法的 JSON 数组结构，每个元素是一道独立的题目，格式如下：
[
    {{ "type": "choice|blank|short|calc", "question": "题目内容", "options": ["选项A", "选项B"], "answer": "答案/解析" }}
]
注意：如果不是选择题，options字段填空数组[]。绝对禁止随附任何markdown标志或者多余文本。
"""
        payload = { "model": self.model, "prompt": prompt, "stream": False, "format": "json" }
        logger.debug("Generating independent exam quiz based on parsed knowledge...")
        try:
            import requests, json
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                res_text = response.json().get("response", "")
                try:
                    return json.loads(res_text)
                except:
                    import re
                    match = re.search(r'\[.*\]', res_text, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
        except Exception as e:
            logger.error(f"[Ollama] Failed to generate exam quiz: {e}")
        return []

    def analyze_subject_domain(self, text: str) -> dict:
        """
        全量分析：识别文档学科领域和教学侧重点 (V2.0 Phase 2)
        """
        logger.info("[V2.0] Analyzing subject domain...")
        # 提取前5000字足以判断学科
        sample_text = text[:5000]
        
        system_prompt = (
            "你是一个资深的教学研究员。请分析这段教材/笔记片段，识别其所属学科领域，并给出教学策略建议。\n"
            "输出结果必须是合法的 JSON 格式，如下例：\n"
            "{\n"
            "  \"subject_type\": \"math | history | law | CS | finance | medical | other\",\n"
            "  \"subject_name\": \"具体学科名\",\n"
            "  \"focus\": \"该学科的核心复习侧重点（如：公式推导、案例分析、时间线记忆等）\",\n"
            "  \"strategy\": \"针对该学科的路径图生成策略建议\"\n"
            "}"
        )
        
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n待分析的内容：\n{sample_text}",
            "stream": False,
            "format": "json"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=30)
            res_json = response.json()
            analysis = json.loads(res_json.get("response", "{}"))
            logger.info(f"[V2.0] Domain Analysis Result: {analysis.get('subject_name')} ({analysis.get('subject_type')})")
            return analysis
        except Exception as e:
            logger.error(f"[V2.0] Domain analysis failed: {e}")
            return {"subject_type": "other", "subject_name": "未知学科", "focus": "常规文本提取", "strategy": "通用模式"}

    def _build_config_context(self, user_config: dict) -> str:
        """根据用户配置生成 Prompt 指令上下文 (V2.0 Intelligence)"""
        if not user_config:
            return ""
        
        context_parts = []
        
        # 重点章节指令
        priority_chapters = user_config.get("priority_chapters", [])
        if priority_chapters:
            chapters_str = "、".join([f"第{ch}章" for ch in priority_chapters])
            context_parts.append(
                f"⚠️ **用户标注的考试重点**: {chapters_str}\n"
                f"请为这些章节的所有知识点设置更高的 `importance` (≥8)，并多配置练习例题。"
            )
        
        # 题型占比指令
        exam_weights = user_config.get("exam_weights", {})
        if exam_weights:
            # Find top 2 exam types by weight
            sorted_types = sorted(exam_weights.items(), key=lambda x: x[1], reverse=True)
            
            type_map = {
                "choice": ("选择题", "概念辨析", "增加易混淆知识点对比，标注关键词"),
                "blank": ("填空题", "关键术语", "标注必背公式和定义"),
                "judge": ("判断题", "概念理解", "列举常见误区"),
                "short": ("简答题", "论述理解", "多生成论述类知识点，要求逻辑性"),
                "calc": ("计算题", "公式应用", "确保提取关键的计算公式"),
                "comprehensive": ("综合应用题", "跨章节融合", "强调知识点间的关联")
            }
            
            # Build instructions for top exam types
            for exam_type, weight in sorted_types[:2]:  # Focus on top 2
                if weight > 0 and exam_type in type_map:
                    type_name, focus, instruction = type_map[exam_type]
                    context_parts.append(
                        f"⚠️ **{type_name}重点** → {instruction}。【绝对纪律】：如果且仅如果原文中出现了此类相关的题目或例题，**必须一字不差地（Verbatim）将原题题干与原解析提取到 examples 中，严禁任何形式的改写、缩写或自行编造！**如果没有，则 `examples` 保持为空。"
                    )
        
        return "\n\n".join(context_parts)

    def _build_domain_context(self, domain_analysis: dict) -> str:
        """根据学科分析结果生成 Prompt 指令上下文 (V2.0 Phase 2)"""
        if not domain_analysis or domain_analysis.get("subject_type") == "other":
            return ""
        
        subject_name = domain_analysis.get("subject_name", "该学科")
        focus = domain_analysis.get("focus", "")
        strategy = domain_analysis.get("strategy", "")
        
        return (
            f"🧠 **AI 学科分析报告**:\n"
            f"- 当前学科: {subject_name}\n"
            f"- 复习侧重: {focus}\n"
            f"- 建议策略: {strategy}\n"
            f"请务必遵循上述学科特性进行深度提取。"
        )

    def generate_roadmap(self, text: str, user_config: dict = None, domain_analysis: dict = None) -> list:
        url = f"{self.base_url}/api/generate"
        logger.debug(f"Generating pedagogical roadmap (input len={len(text)})...")
        logger.debug(f"Input Preview: {text[:200]}...")
        
        # Build contexts (V2.0)
        config_context = ""
        if user_config:
            config_context = ''
            logger.info(f"[V2.0] Injecting user config: {config_context[:100]}...")
        
        domain_context = ""
        if domain_analysis:
            domain_context = self._build_domain_context(domain_analysis)
            logger.info(f"[V2.0] Injecting domain context: {domain_context[:100]}...")
        
        system_prompt = (
            "你是一个专业的考前辅导老师。你的任务是将学生的复习资料转化为一个结构化的“复习路径图”。\n"
            "即使资料没有明确的章节标题（如：第一章、Section 1），你也必须根据内容的逻辑性将其拆分为多个逻辑章节（Chapter）。\n\n"
            "关键提取准则：\n"
            "1. **全面性**：严禁漏掉核心定义、公式、定理或关键事实。如果文档内容较多，请确保提取密度。\n"
            "2. **问答/题库适配**：如果输入是“问题+答案”格式（如复习题、题库），请将每个问题作为一个 Point (name=问题, content=核心答案)，并在 Examples 中提供更详细的解答步骤。\n"
            "3. **逻辑聚类**：对于散乱的笔记或无标题文本，请自发定义有意义的章节标题（如“基础概念”、“核心原理”、“应用实例”）。\n\n"
            "输出必须是一个合法的 JSON 数组，格式如下例：\n"
            "[\n"
            "  {\n"
            "    \"id\": \"chap_1\",\n"
            "    \"title\": \"严格提取文档中的章节标题（若无标题，请根据逻辑自行总结，如：计算机网络概论）\",\n"
            "    \"summary\": \"本章核心考点与重难点总结\",\n"
            "    \"points\": [\n"
            "      { \"id\": \"p1\", \"name\": \"具体概念/公式名\", \"content\": \"详细定义、公式内容及物理/几何意义\", \"importance\": 5, \"type\": \"concept\", \"original_questions\": [\"散落于此知识点附近的原题或课后习题题干1\", \"原题2\"] }\n"
            "    ],\n"
            "    \"examples\": [\n"
            "      { \"question\": \"文档原文中的题目描述\", \"solution\": \"原文中提供或能直接推导出的详细解答步骤\" }\n"
            "    ]\n"
            "  }\n"
            "]\n\n"
            "严格要求：\n"
            "1. **章节标题 (Title)**：优先使用原标题。若无原标题，请赋予一个逻辑一致的标题，切勿留空。\n"
            "2. **知识点 (Points)**：颗粒度要细。定义、定理、推论必须拆分为单独的 Point。不要漏掉任何重要概念。\n"
            "3. **例题 (Examples) [🚨反幻觉警告🚨]**：必须 **100% 来源于当前提供的文本**。如果当前页没有具体的例题、习题或案例分析，该字段必须返回空数组 `[]`！绝对禁止自行编造文本中不存在的例题！\n"
            "4. **JSON 格式**：只输出 JSON 数组，不带 Markdown 标记，不带废话。"
        )
        
        # Assemble final prompt with user guidance and domain context
        prompt_parts = [system_prompt]
        if config_context:
            prompt_parts.append(config_context)
        if domain_context:
            prompt_parts.append(domain_context)
        
        prompt_parts.append(f"待处理的内容：\n{text}")
        prompt = "\n\n".join(prompt_parts)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
            # REMOVED: "format": "json" - can be too restrictive for small models
        }
        
        try:
            # 180s is enough for a summary. If it takes longer, just fallback.
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            res_text = response.json().get("response", "")
            logger.debug(f"Raw Roadmap Response (first 200 chars): {res_text[:200]}")
            # Robust JSON extraction: remove <think> tags first
            import re
            res_text = re.sub(r'<think>.*?</think>', '', res_text, flags=re.DOTALL)
            
            match = re.search(r'(\[.*\])', res_text, re.DOTALL)
            if match:
                res_json_str = match.group(1)
            else:
                res_json_str = res_text
            
            # ATTEMPT 1: Direct Parse
            try:
                roadmap = json.loads(res_json_str)
                logger.info("JSON parsed successfully.")
            except Exception as e2:
                logger.error(f"JSON repair failed: {e2}")
                # FALLBACK: Create a single chapter with the raw text
                logger.warning("Using fallback roadmap with raw text.")
                return [{
                    "id": "fallback_1",
                    "title": "复习指南 (解析失败备份)",
                    "summary": "AI 生成的数据格式存在微小错误，已为您保留原始内容。",
                    "points": [
                        {
                            "id": "raw_content",
                            "name": "核心内容",
                            "content": res_text[:1000] + "...", # Truncate to avoid huge cards
                            "importance": 5,
                            "type": "concept"
                        }
                    ],
                    "examples": []
                }]

            if not isinstance(roadmap, list):
                if isinstance(roadmap, dict):
                    roadmap = [roadmap]
                else:
                    logger.warning(f"Roadmap is not a list/dict: {type(roadmap)}. Using fallback.")
                    return [{
                        "id": "fallback_type",
                        "title": "复习指南 (类型错误备份)",
                        "summary": "AI 返回的数据格式不符合预期列表，已为您保留部分内容。",
                        "points": [{"id": "p_msg", "name": "提示", "content": str(roadmap)[:500], "importance": 5, "type": "concept"}],
                        "examples": []
                    }]

            logger.debug(f"Roadmap generated with {len(roadmap)} chapters.")
            return roadmap
            
        except requests.exceptions.Timeout:
            logger.warning("Roadmap generation timed out. Using fallback.")
            return [{
                "id": "fallback_timeout",
                "title": "复习指南 (生成超时备份)",
                "summary": "AI 思考时间过长，已为您保留原始内容。",
                "points": [
                    {
                        "id": "raw_content",
                        "name": "核心内容",
                        "content": text[:1500] + "...", 
                        "importance": 5,
                        "type": "concept"
                    }
                ],
                "examples": []
            }]
            
        except Exception as e:
            logger.error(f"Generate roadmap failed: {e}")
            if 'res_text' in locals():
                logger.debug(f"Full failed response: {res_text}")
            
            # Also fallback on generic error if possible
            return [{
                "id": "fallback_error",
                "title": "复习指南 (系统异常备份)",
                "summary": "生成过程中发生错误，已为您保留原始内容。",
                "points": [
                     {
                        "id": "raw_content",
                        "name": "核心内容",
                        "content": text[:1500] + "...", 
                        "importance": 5,
                        "type": "concept"
                    }
                ],
                "examples": []
            }]

    def get_embedding(self, text: str) -> list[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.embed_model,
            "prompt": text
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("embedding", [])
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

class CloudAPIService(OllamaService):
    """
    OpenAI-compatible Cloud API Service (inherits prompt building from OllamaService to avoid duplication)
    """
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1", model: str = "deepseek-chat"):
        super().__init__(model=model, base_url=base_url)
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_embedding(self, text: str) -> list[float]:
        """
        🚨 RAG 基石：死锁本地化 🚨
        无论用户把 Generation (对话) 切到哪个云端模型，
        为了保持 PG_Vector 内 768 维库的完整性并节省大量的 API 计费，
        所有的向量化运算统统拦截到本机的 Ollama (nomic-embed-text)。
        """
        import requests
        url = "http://localhost:11434/api/embeddings"
        payload = {
            "model": "nomic-embed-text",
            "prompt": text
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("embedding", [])
        except Exception as e:
            logger.error(f"Cloud API intercepted but local Ollama embedding failed: {e}")
            return []

    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        url = f"{self.base_url}/chat/completions"
        payload = {"model": self.model, "messages": messages, "stream": True}
        try:
            with requests.post(url, json=payload, headers=self.headers, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:].strip()
                            if data_str == '[DONE]': break
                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if choices and "delta" in choices[0]:
                                    delta = choices[0]["delta"]
                                    
                                    # 对齐 DeepSeek-R1：将云端独有的 reasoning_content 拼接为前端熟悉的 <think> 标签
                                    if "reasoning_content" in delta and delta["reasoning_content"]:
                                        yield f"<think>{delta['reasoning_content']}</think>"
                                    # 常规内容
                                    if "content" in delta and delta["content"]:
                                        yield delta["content"]
                                        
                            except Exception:
                                pass
        except Exception as e:
            logger.error(f"Cloud API Stream Error: {e}")
            yield f"Error communicating with Cloud API: {str(e)}"

    def generate_raw(self, prompt: str, temperature: float = 0.3) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": temperature
        }
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=180)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error in generate_raw (Cloud API): {e}")
            return f"Error: {str(e)}"

    def _generate_cloud(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        response = requests.post(url, json=payload, headers=self.headers, timeout=180)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def generate_summary(self, text: str) -> str:
        return self._generate_cloud("你是一个专业的助手。请总结以下内容的知识点，提取核心概念，保持简洁。", text)

    def generate_exam_quiz(self, roadmap_json: str, user_config: dict) -> list:
        url = f"{self.base_url}/api/generate"
        weight_context = self._build_config_context(user_config) if user_config else "默认出题均衡"
        
        prompt = f"""你是一个资深的考卷出题专家。请根据以下大纲知识点和用户指定的【考试题型权重】，出一套高还原度的课后测验题。
        
【用户考试题型偏好】:
{weight_context}

【知识点大纲】:
{roadmap_json}

请严格输出合法的 JSON 数组结构，每个元素是一道独立的题目，格式如下：
[
    {{ "type": "choice|blank|short|calc", "question": "题目内容", "options": ["选项A", "选项B"], "answer": "答案/解析" }}
]
注意：如果不是选择题，options字段填空数组[]。绝对禁止随附任何markdown标志或者多余文本。
"""
        payload = { "model": self.model, "prompt": prompt, "stream": False, "format": "json" }
        logger.debug("Generating independent exam quiz based on parsed knowledge...")
        try:
            import requests, json
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                res_text = response.json().get("response", "")
                try:
                    return json.loads(res_text)
                except:
                    import re
                    match = re.search(r'\[.*\]', res_text, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
        except Exception as e:
            logger.error(f"[Ollama] Failed to generate exam quiz: {e}")
        return []

    def analyze_subject_domain(self, text: str) -> dict:
        sample_text = text[:5000]
        system_prompt = (
            "你是一个资深的教学研究员。请分析这段教材/笔记片段，识别其所属学科领域，并给出教学策略建议。\n"
            "输出结果必须是合法的 JSON 格式，如下例：\n"
            "{\n"
            "  \"subject_type\": \"math | history | law | CS | finance | medical | other\",\n"
            "  \"subject_name\": \"具体学科名\",\n"
            "  \"focus\": \"该学科的核心复习侧重点\",\n"
            "  \"strategy\": \"针对该学科的路径图生成策略建议\"\n"
            "}"
        )
        try:
            res_text = self._generate_cloud(system_prompt, sample_text)
            import re
            res_text = re.sub(r'<think>.*?</think>', '', res_text, flags=re.DOTALL)
            match = re.search(r'(\{.*\})', res_text, re.DOTALL)
            if match:
                res_text = match.group(1)
            return json.loads(res_text)
        except Exception as e:
            logger.error(f"[V2.0] Domain analysis failed: {e}")
            return {"subject_type": "other", "subject_name": "未知学科", "focus": "常规文本提取", "strategy": "通用模式"}

    def generate_roadmap(self, text: str, user_config: dict = None, domain_analysis: dict = None) -> list:
        # Re-use the prompt part from the parent
        config_context = '' if user_config else ""
        domain_context = self._build_domain_context(domain_analysis) if domain_analysis else ""
        
        system_prompt = (
            "你是一个专业的考前辅导老师。你的任务是将学生的复习资料转化为一个结构化的“复习路径图”。\n"
            "即使资料没有明确的章节标题（如：第一章、Section 1），你也必须根据内容的逻辑性将其拆分为多个逻辑章节（Chapter）。\n\n"
            "关键提取准则：\n"
            "1. **全面性**：严禁漏掉核心定义、公式、定理或关键事实。如果文档内容较多，请确保提取密度。\n"
            "2. **问答/题库适配**：如果输入是“问题+答案”格式（如复习题、题库），请将每个问题作为一个 Point (name=问题, content=核心答案)，并在 Examples 中提供更详细的解答步骤。\n"
            "3. **逻辑聚类**：对于散乱的笔记或无标题文本，请自发定义有意义的章节标题（如“基础概念”、“核心原理”、“应用实例”）。\n\n"
            "输出必须是一个合法的 JSON 数组，格式如下例：\n"
            "[\n"
            "  {\n"
            "    \"id\": \"chap_1\",\n"
            "    \"title\": \"严格提取文档中的章节标题（若无标题，请根据逻辑自行总结，如：计算机网络概论）\",\n"
            "    \"summary\": \"本章核心考点与重难点总结\",\n"
            "    \"points\": [\n"
            "      { \"id\": \"p1\", \"name\": \"具体概念/公式名\", \"content\": \"详细定义、公式内容及物理/几何意义\", \"importance\": 5, \"type\": \"concept\", \"original_questions\": [\"散落于此知识点附近的原题或课后习题\"], \"examples\": [\"详细的解答步骤\"] }\n"
            "    ],\n"
            "    \"examples\": [\n"
            "      { \"question\": \"文档原文中的题目描述\", \"solution\": \"原文中提供或能直接推导出的详细解答步骤\" }\n"
            "    ]\n"
            "  }\n"
            "]\n\n"
            "严格要求：\n"
            "1. **章节标题 (Title)**：优先使用原标题。若无原标题，请赋予一个逻辑一致的标题，切勿留空。\n"
            "2. **知识点 (Points)**：颗粒度要细。定义、定理、推论必须拆分为单独的 Point。不要漏掉任何重要概念。\n"
            "3. **例题 (Examples) [🚨反幻觉警告🚨]**：必须 **100% 来源于当前提供的文本**。如果当前页没有具体的例题、习题或案例分析，该字段必须返回空数组 `[]`！绝对禁止自行编造文本中不存在的例题！\n"
            "4. **JSON 格式**：只输出 JSON 数组，不带 Markdown 标记，不带废话。"
        )
        
        prompt_parts = [system_prompt]
        if config_context: prompt_parts.append(config_context)
        if domain_context: prompt_parts.append(domain_context)
        final_sys = "\n\n".join(prompt_parts)
        
        try:
            res_text = self._generate_cloud(final_sys, f"待处理的内容：\n{text}")
            import re
            res_text = re.sub(r'<think>.*?</think>', '', res_text, flags=re.DOTALL)
            match = re.search(r'(\[.*\])', res_text, re.DOTALL)
            if match:
                res_json_str = match.group(1)
            else:
                res_json_str = res_text
            
            # Simple escape fix
            def escape_fix(m):
                seq = m.group(0)
                if seq in ['\\"', '\\\\', '\\/', '\\b', '\\f', '\\n', '\\r', '\\t']: return seq
                if seq.startswith('\\u'): return seq
                return '\\\\' + seq[1]
            fixed_str = re.sub(r'\\(.)', escape_fix, res_json_str)
            
            try:
                roadmap = json.loads(fixed_str)
            except Exception:
                roadmap = []
            
            if not isinstance(roadmap, list):
                roadmap = [roadmap] if isinstance(roadmap, dict) else []
                
            return roadmap
            
        except Exception as e:
            logger.error(f"Cloud API generate roadmap failed: {e}")
            return []


def get_llm_service(user_config: dict = None) -> BaseLLMService:
    if user_config:
        provider = user_config.get("llm_provider", "local")
        if provider == "cloud":
            api_key = user_config.get("llm_api_key", "")
            base_url = user_config.get("llm_base_url", "https://api.deepseek.com/v1")
            model = user_config.get("llm_model", "deepseek-chat")
            if api_key:
                return CloudAPIService(api_key=api_key, base_url=base_url, model=model)
                
    # Fallback to Local Ollama
    return OllamaService(model="deepseek-r1:7b")
