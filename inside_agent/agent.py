import logging
from typing import List, Dict, Any, Optional
from .models.base import BaseModel
from .tools.base import BaseTool
from .memory.base import BaseMemory
from .utils.context_manager import ContextManager

class Agent:
    """核心Agent类，实现完整的ReAct执行循环"""

    def __init__(
        self,
        model: BaseModel,
        tools: List[BaseTool],
        memory: BaseMemory,
        context_manager: ContextManager,
        name: str = "Inside Agent"
    ):
        self.model = model
        self.tools = tools
        self.memory = memory
        self.context_manager = context_manager
        self.name = name
        self.logger = logging.getLogger(__name__)

        if hasattr(self.model, 'tools'):
            self.model.tools = tools

    def run(self, user_input: str) -> str:
        """执行Agent的ReAct完整循环"""
        try:
            self.context_manager.add_message("user", user_input)
            context = self.context_manager.get_context()

            if hasattr(self.model, 'run_with_react'):
                response = self.model.run_with_react(context)
            elif hasattr(self.model, 'generate'):
                response = self.model.generate(context)
                response = response.get("content", response) if isinstance(response, dict) else response
            else:
                return "模型不支持generate或run_with_react方法"

            self.context_manager.add_message("assistant", str(response))
            self.memory.save_conversation(self.context_manager.get_full_history())

            return str(response)

        except Exception as e:
            self.logger.error(f"Agent执行出错: {str(e)}")
            return f"执行出错: {str(e)}"

    def run_stream(self, user_input: str) -> str:
        """执行Agent的ReAct完整循环，使用流式输出"""
        try:
            self.context_manager.add_message("user", user_input)
            context = self.context_manager.get_context()

            if hasattr(self.model, 'run_with_react'):
                response = self.model.run_with_react(context)
                print(response)
            elif hasattr(self.model, 'generate_stream'):
                response = self.model.generate_stream(context)
            elif hasattr(self.model, 'generate'):
                response = self.model.generate(context)
                response = response.get("content", response) if isinstance(response, dict) else response
                print(response)
            else:
                return "模型不支持generate或run_with_react方法"

            self.context_manager.add_message("assistant", str(response))
            self.memory.save_conversation(self.context_manager.get_full_history())

            return str(response)

        except Exception as e:
            self.logger.error(f"Agent执行出错: {str(e)}")
            error_msg = f"执行出错: {str(e)}"
            print(error_msg)
            return error_msg

    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]

            tool = next((t for t in self.tools if t.name == tool_name), None)

            if tool:
                try:
                    result = tool.execute(tool_args)
                    results.append({
                        "tool_call_id": tool_call["id"],
                        "tool_name": tool_name,
                        "result": result
                    })
                except Exception as e:
                    self.logger.error(f"工具执行出错 {tool_name}: {str(e)}")
                    results.append({
                        "tool_call_id": tool_call["id"],
                        "tool_name": tool_name,
                        "result": f"执行出错: {str(e)}"
                    })
            else:
                results.append({
                    "tool_call_id": tool_call["id"],
                    "tool_name": tool_name,
                    "result": f"工具未找到: {tool_name}"
                })

        return results
