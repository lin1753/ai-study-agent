import json
import logging
from typing import List, Dict, Callable

logger = logging.getLogger(__name__)

class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def run(self, *args, **kwargs):
        return self.func(*args, **kwargs)

class StudyAgent:
    def __init__(self, llm_service, max_steps: int = 3):
        self.llm = llm_service
        self.max_steps = max_steps
        self.tools: Dict[str, Tool] = {}
        
        self.system_prompt = """你是一个智能学习助理(Study Agent)。
你的任务是帮助用户学习、检索资料或解答问题。

### 工作流程 (ReAct):
1. **思考 (Thought)**: 仔细思考用户的请求，考虑是否需要调用工具。思考内容可以直接输出，不需要特殊标签。
2. **行动 (Action)**: 如果你要获取外部信息或执行操作，请务必严格使用以下格式调用工具：
<action name="工具名">{"参数名": "参数值"}</action>
3. **完成 (Final Answer)**: 当你获得足够且准确的信息准备好回答用户时，无论是否调用过工具，请始终将你给用户的最终答复包裹在下面标签中：
<final_answer>你的最终详细回答内容，可以使用Markdown进行排版。</final_answer>

### 可用工具:
{tool_descriptions}

### 注意事项:
- 单次回复中你可以包含多个思考步骤。
- 只有在需要额外信息时才触发 <action> 标签调用工具！
- 不要瞎编和猜测数据。
- 调用工具后，系统会补充 [工具返回: ...] 给到你，收到后请根据返回内容继续思考。
- 如果不使用任何工具也能回答（比如只是聊天或者打招呼），请直接思考片刻后输出 <final_answer>回复内容</final_answer>。
"""

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def _format_sse(self, data_type: str, content: str) -> str:
        """格式化为 SSE 协议字符串"""
        payload = json.dumps({"type": data_type, "content": content}, ensure_ascii=False)
        return f"data: {payload}\n\n"

    def run_stream(self, task_instruction: str, history: List[Dict] = None):
        """
        Runs the agent stream and yields SSE data containing 'thought' and 'message' chunks.
        """
        tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in self.tools.values()])
        system_msg = self.system_prompt.format(tool_descriptions=tool_descriptions)
        
        messages = [{"role": "system", "content": system_msg}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": task_instruction})
        
        logger.info("[Agent] Stream loop started")
        yield self._format_sse("thought", "[Agent] 正在思考与检索...\n")
        
        for step in range(self.max_steps):
            logger.debug(f"[Agent] Step {step+1}/{self.max_steps}")
            
            full_chunk_acc = ""
            current_action_name = None
            current_action_args = None
            in_final_answer = False
            
            for chunk in self.llm.chat_stream(messages):
                full_chunk_acc += chunk

                if not in_final_answer and "<final_answer>" in full_chunk_acc:
                    in_final_answer = True
                    split_parts = full_chunk_acc.split("<final_answer>", 1)
                    if len(split_parts) > 1 and len(split_parts[1]) > 0:
                        content_to_yield = split_parts[1]
                        yield self._format_sse("message", content_to_yield)
                    continue

                if in_final_answer:
                    clean_chunk = chunk
                    if "</final_answer>" in full_chunk_acc:
                        idx = clean_chunk.find("</final_answer>")
                        if idx != -1:
                            clean_chunk = clean_chunk[:idx]

                    if clean_chunk:
                        yield self._format_sse("message", clean_chunk)
                    
                    if "</final_answer>" in full_chunk_acc:
                        break # Done yielding message for this turn
                    
                else:
                    # we are in thought phase
                    yield self._format_sse("thought", chunk)
                    
                    import re
                    action_match = re.search(r'<action name="(.*?)">(.*?)</action>', full_chunk_acc, re.DOTALL)
                    if action_match:
                        current_action_name = action_match.group(1).strip()
                        current_action_args = action_match.group(2).strip()
                        break 
            
            if current_action_name:
                yield self._format_sse("thought", f"\n[尝试调用工具: {current_action_name}]...")
                logger.info(f"[Agent] Invoking tool {current_action_name}")
                
                result = "Tool not found."
                if current_action_name in self.tools:
                    try:
                        args = json.loads(current_action_args)
                        result = self.tools[current_action_name].run(**args)
                    except json.JSONDecodeError:
                        try:
                            result = self.tools[current_action_name].run(query=current_action_args)
                        except:
                            result = "Error: Invalid JSON parameters for tool."
                    except Exception as e:
                        result = f"Error executing tool {current_action_name}: {str(e)}"
                
                yield self._format_sse("thought", f"\n[工具返回: {str(result)[:50]}...]\n")
                
                messages.append({"role": "assistant", "content": full_chunk_acc})
                messages.append({"role": "user", "content": f"[工具返回: {result}]"})
                continue
            
            if "<final_answer>" in full_chunk_acc:
                break
                
            if step == self.max_steps - 1:
                yield self._format_sse("thought", "\n[System: Max steps reached]\n")
                
        yield self._format_sse("done", "")
