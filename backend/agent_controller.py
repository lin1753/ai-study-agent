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
        
        # System Prompt for the ReAct loop
        self.system_prompt = """你是一个智能学习助理(Study Agent)。
你在帮助用户解析学习资料或回答学习问题时，必须思考并可能调用工具。
可用的工具：
{tool_descriptions}

使用以下格式进行思考和行动：
Thought: 思考我接下来应该做什么。
Action: 要调用的工具名称（只能是[{tool_names}]之一）。
Action Input: 传递给工具的 JSON 格式参数，例如 {{"text": "需要处理的内容"}}。

当工具返回观察结果（Observation）后，继续思考。如果你已经获得了足够的信息来回答用户请求（或者完成任务），请以以下格式结束：
Thought: 我已经完成了任务。
Final Answer: 最终的结果或总结。
"""

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def run(self, task_instruction: str, context: str = "") -> str:
        tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in self.tools.values()])
        tool_names = ", ".join(self.tools.keys())
        
        system_msg = self.system_prompt.format(
            tool_descriptions=tool_descriptions,
            tool_names=tool_names
        )
        
        history = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"Context/State:\n{context}\n\nTask:\n{task_instruction}"}
        ]
        
        for step in range(self.max_steps):
            logger.debug(f"[Agent] Step {step+1}/{self.max_steps}")
            
            # Simple interaction assuming llm_service has a generic chat/completion method
            # We construct a local prompt for this simplified agent
            prompt_text = ""
            for msg in history:
                prompt_text += f"\n{msg['role'].upper()}: {msg['content']}"
            prompt_text += "\nASSISTANT: "
            
            response = self._call_llm_raw(prompt_text)
            logger.debug(f"[Agent] RAW Output: {response}")
            
            # Parse the response for Action and Final Answer
            if "Final Answer:" in response:
                return response.split("Final Answer:", 1)[1].strip()
                
            if "Action:" in response and "Action Input:" in response:
                action_part = response.split("Action:", 1)[1]
                action_name = action_part.split("Action Input:", 1)[0].strip()
                
                action_input_part = response.split("Action Input:", 1)[1].strip()
                # Enhanced JSON extraction:
                import re
                json_match = re.search(r"(\{.*\})", action_input_part, re.DOTALL)
                if json_match:
                    input_json_str = json_match.group(1).strip()
                else:
                    input_json_str = action_input_part.split("\n")[0].strip()
                
                try:
                    kwargs = json.loads(input_json_str)
                except json.JSONDecodeError:
                    # fallback
                    kwargs = {"text": input_json_str}
                    
                tool_result = "Tool not found."
                if action_name in self.tools:
                    try:
                        tool_result = str(self.tools[action_name].run(**kwargs))
                    except Exception as e:
                        tool_result = f"Error executing tool: {str(e)}"
                
                observation = f"Observation: {tool_result}"
                history.append({"role": "assistant", "content": response})
                history.append({"role": "user", "content": observation})
                logger.debug(f"[Agent] Tool {action_name} executed -> {tool_result[:100]}")
            else:
                # If the LLM doesn't follow the format, force break or return
                logger.warning("[Agent] LLM did not return an Action or Final Answer format.")
                return response
                
        return "Max steps reached without concluding."

    def _call_llm_raw(self, prompt: str) -> str:
        try:
            result = self.llm.generate_raw(prompt, temperature=0.3)
            if result.startswith("Error:"):
                return f"Final Answer: {result}"
            return result
        except Exception as e:
            return f"Final Answer: LLM completion failed: {e}"
