from services.agent_controller import Tool
from services.rag_service import search_related_blocks
from core.db import SessionLocal
import requests
import logging
import os

logger = logging.getLogger(__name__)

def get_rag_search_tool(space_id: str, db_session_factory=SessionLocal):
    def rag_search(query: str):
        db = db_session_factory()
        try:
            # We reuse search_related_blocks
            # For this tool, user config can be empty.
            blocks = search_related_blocks(db, space_id, query, top_k=5, user_config={})
            if not blocks:
                return "未找到相关本地文档内容。"
            return "\n\n".join([f"【资料片段】:\n{b.raw_text}" for b in blocks])
        except Exception as e:
            logger.error(f"RAG tool error: {e}")
            return f"Error executing RAG search: {e}"
        finally:
            db.close()
            
    return Tool(
        name="rag_search_tool",
        description="搜索当前科目上传的本地学习资料（PDF/PPT等）。参数格式为: {\"query\": \"你的搜索关键词\"}。你可以多次调用来搜索不同关键词。",
        func=rag_search
    )

def get_web_search_tool(api_key: str = None):
    def web_search(query: str):
        # We will use Tavily Search API
        tavily_key = api_key or os.getenv("TAVILY_API_KEY", "")
        if not tavily_key:
            return "Error: TAVILY_API_KEY is not configured. Web search is unavailable."
            
        try:
            url = "https://api.tavily.com/search"
            headers = {"Content-Type": "application/json"}
            payload = {
                "api_key": tavily_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": False,
                "include_images": False,
                "include_raw_content": False,
                "max_results": 3
            }
            logger.info(f"Executing Tavily web search for '{query}'")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                return "没有找到相关的网络搜索结果。"
                
            formatted_results = []
            for r in results:
                formatted_results.append(f"【来源: {r.get('title', 'Unknown')}】\n【内容】: {r.get('content', '')}")
                
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Web search tool error: {e}")
            return f"Error executing web search: {e}"

    return Tool(
        name="web_search_tool",
        description="在互联网上搜索最新资料或常识定义。只能传入搜索文本。参数格式: {\"query\": \"搜索事项\"}。",
        func=web_search
    )

def get_exam_generator_tool(space_id: str, db_session_factory=SessionLocal):
    def generate_exam(roadmap_json: str):
        db = db_session_factory()
        try:
            from core.llm_factory import get_llm_service
            space = db.query(ConversationSpace).filter(ConversationSpace.id == space_id).first()
            user_config = {}
            if space and space.config_data:
                import json
                user_config = json.loads(space.config_data)
            
            llm = get_llm_service(user_config)
            quiz = llm.generate_exam_quiz(roadmap_json, user_config)
            
            if not quiz:
                return "未能生成考题或解析错误。"
            
            formatted_quiz = []
            for i, q in enumerate(quiz, 1):
                formatted_quiz.append(f"第{i}题: {q.get('question_text')}\n选项: {q.get('options')}\n答案: {q.get('answer')}\n解析: {q.get('explanation')}")
            
            return "\n\n".join(formatted_quiz)
        except Exception as e:
            logger.error(f"Exam generator tool error: {e}")
            return f"生成考题失败: {e}"
        finally:
            db.close()
            
    return Tool(
        name="exam_generator_tool",
        description="根据提供的大纲或知识点结构 (JSON 格式) 生成针对性的练习题或考题。参数格式: {\"roadmap_json\": \"[ { ...章节信息和知识点 } ]\"}。",
        func=generate_exam
    )
