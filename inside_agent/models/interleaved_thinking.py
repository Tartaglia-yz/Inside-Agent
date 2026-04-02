from typing import Dict, Any, List, Callable, Optional
from .base import BaseModel
import logging

class InterleavedThinkingModel(BaseModel):
    """支持交错思维和ReAct模式的模型包装器"""

    MAX_REACT_TURNS = 15
    STOP_PHRASES = ["final_answer", "final answer", "答案", "完成", "完成了", "就这样"]

    def __init__(self, base_model: BaseModel, tools: List[Any] = None, os_info: Dict[str, str] = None):
        self.base_model = base_model
        self.tools = tools or []
        self.os_info = os_info
        if hasattr(self.base_model, 'tools'):
            self.base_model.tools = self.tools
        if hasattr(self.base_model, 'os_info') and os_info:
            self.base_model.os_info = os_info
        self.logger = logging.getLogger(__name__)

    def generate(self, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成模型响应，支持ReAct循环"""
        react_context = context.copy()
        final_response = None

        for turn in range(self.MAX_REACT_TURNS):
            self.logger.info(f"ReAct循环第 {turn + 1} 轮")

            response = self.base_model.generate(react_context)

            if "tool_calls" in response and response["tool_calls"]:
                tool_results = self._execute_tools(response["tool_calls"])

                for tool_result in tool_results:
                    observation = f"\n[Observation] 工具 {tool_result['tool_name']} 执行结果:\n{tool_result['result']}\n[/Observation]\n"
                    react_context.append({
                        "role": "user",
                        "content": observation
                    })

                continue

            content = response.get("content", "")

            if any(stop_phrase.lower() in content.lower() for stop_phrase in self.STOP_PHRASES):
                self.logger.info("检测到停止短语，结束ReAct循环")
                final_response = response
                break

            final_response = response
            break

        if final_response is None:
            final_response = {"content": "Agent执行达到最大循环次数"}

        return final_response

    def run_with_react(self, context: List[Dict[str, Any]], user_input: str) -> str:
        """使用ReAct模式运行完整的推理-行动循环"""
        react_context = context.copy()
        react_context.append({"role": "user", "content": user_input})

        thoughts = []
        actions = []
        observations = []

        for turn in range(self.MAX_REACT_TURNS):
            self.logger.info(f"ReAct循环第 {turn + 1} 轮")

            response = self.base_model.generate(react_context)
            content = response.get("content", "")

            if "tool_calls" in response and response["tool_calls"]:
                thoughts.append(content)

                tool_results = self._execute_tools(response["tool_calls"])
                actions.append(str(response["tool_calls"]))

                for tool_result in tool_results:
                    observation = f"\n[Observation] 工具 {tool_result['tool_name']} 执行结果:\n{tool_result['result']}\n[/Observation]\n"
                    observations.append(observation)
                    react_context.append({
                        "role": "user",
                        "content": observation
                    })

                continue

            if any(stop_phrase.lower() in content.lower() for stop_phrase in self.STOP_PHRASES):
                self.logger.info("检测到停止短语，结束ReAct循环")
                return content

            if turn == 0 and not content.strip():
                return "我没有收到有效的响应，请重试。"

            if not content.strip():
                continue

            return content

        return "Agent执行达到最大循环次数"

    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name", "")
            tool_args = tool_call.get("function", {}).get("arguments", {})

            tool = next((t for t in self.tools if getattr(t, "name", "") == tool_name), None)

            if tool:
                try:
                    result = tool.execute(tool_args)
                    results.append({
                        "tool_name": tool_name,
                        "result": result
                    })
                    self.logger.info(f"工具 {tool_name} 执行成功")
                except Exception as e:
                    self.logger.error(f"工具 {tool_name} 执行出错: {str(e)}")
                    results.append({
                        "tool_name": tool_name,
                        "result": f"执行出错: {str(e)}"
                    })
            else:
                self.logger.warning(f"工具未找到: {tool_name}")
                results.append({
                    "tool_name": tool_name,
                    "result": f"工具未找到: {tool_name}"
                })

        return results

    def get_name(self) -> str:
        """获取模型名称"""
        return f"ReAct-{self.base_model.get_name()}"
