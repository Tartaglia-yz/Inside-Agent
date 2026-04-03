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
        self._tools_info_injected = False
        if hasattr(self.base_model, 'tools'):
            self.base_model.tools = self.tools
        if hasattr(self.base_model, 'os_info') and os_info:
            self.base_model.os_info = os_info
        self.logger = logging.getLogger(__name__)

    def _build_tools_info(self) -> str:
        """构建工具信息字符串"""
        file_tool_info = """
### file_tool
用于文件操作：
- read: 读取文件内容
- write: 写入文件内容  
- list: 列出目录内容

参数：action (操作类型), file_path (文件路径), content (文件内容), directory (目录路径)
"""

        shell_tool_info = f"""
### shell_tool
用于执行系统命令：
- 执行Shell命令获取系统信息
- 执行各种终端命令

**当前系统环境：**
- 操作系统：{self.os_info.get('os_type', 'unknown').upper()}
- 默认Shell：{self.os_info.get('shell', 'bash')}
- 列出目录命令：{self.os_info.get('list_dir', 'ls')}
- 当前目录命令：{self.os_info.get('current_dir', 'pwd')}

**重要：请根据当前操作系统生成对应的命令！**
- Windows: dir, cd, type, etc.
- macOS/Linux: ls, cd, cat, etc.

参数：command (要执行的命令字符串)

**当你需要执行命令时，请使用shell_tool并提供完整的命令字符串。**
"""

        return file_tool_info + "\n" + shell_tool_info

    def _inject_tools_info(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """向上下文注入工具信息（仅注入一次）"""
        if self._tools_info_injected:
            return context

        self._tools_info_injected = True
        tools_info = self._build_tools_info()

        new_context = []
        for msg in context:
            if msg.get("role") == "system":
                new_context.append({
                    "role": "system",
                    "content": msg["content"] + "\n\n## 可用工具\n" + tools_info
                })
            else:
                new_context.append(msg)

        return new_context

    def generate(self, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成模型响应，支持ReAct循环（按需加载工具信息）"""
        react_context = context.copy()
        final_response = None
        first_call_without_tools = True

        for turn in range(self.MAX_REACT_TURNS):
            self.logger.info(f"ReAct循环第 {turn + 1} 轮")

            response = self.base_model.generate(react_context)

            if "tool_calls" in response and response["tool_calls"]:
                if first_call_without_tools:
                    self.logger.info("检测到工具调用需求，注入工具信息")
                    react_context = self._inject_tools_info(react_context)
                    first_call_without_tools = False
                    response = self.base_model.generate(react_context)

                tool_results = self._execute_tools(response.get("tool_calls", []))

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

    def run_with_react(self, context: List[Dict[str, Any]]) -> str:
        """使用ReAct模式运行完整的推理-行动循环

        按需加载策略：
        1. 首次调用不传递工具信息
        2. 如果模型需要工具，再注入工具信息后重新调用
        3. 后续循环继续使用已注入的上下文
        """
        react_context = context.copy()
        first_call_without_tools = True

        thoughts = []
        actions = []
        observations = []

        for turn in range(self.MAX_REACT_TURNS):
            self.logger.info(f"ReAct循环第 {turn + 1} 轮")

            response = self.base_model.generate(react_context)
            content = response.get("content", "")

            if "tool_calls" in response and response["tool_calls"]:
                thoughts.append(content)

                if first_call_without_tools:
                    self.logger.info("检测到工具调用需求，注入工具信息")
                    react_context = self._inject_tools_info(react_context)
                    first_call_without_tools = False
                    response = self.base_model.generate(react_context)
                    content = response.get("content", "")
                    if "tool_calls" in response and response["tool_calls"]:
                        thoughts.append(content)

                tool_results = self._execute_tools(response.get("tool_calls", []))
                actions.append(str(response.get("tool_calls", [])))

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

    def generate_stream(self, context: List[Dict[str, Any]]) -> str:
        """流式生成模型响应，支持ReAct工具调用（按需加载工具信息）"""
        react_context = context.copy()
        first_call_without_tools = True

        for turn in range(self.MAX_REACT_TURNS):
            self.logger.info(f"ReAct流式循环第 {turn + 1} 轮")

            if hasattr(self.base_model, 'generate_stream'):
                response = self.base_model.generate_stream(react_context)
            else:
                response = self.base_model.generate(react_context)
                if isinstance(response, dict):
                    response = response.get("content", "")
                print(response)
                return response

            tool_calls = self._parse_tool_calls_from_text(response)
            if tool_calls:
                if first_call_without_tools:
                    self.logger.info("检测到工具调用需求，注入工具信息")
                    react_context = self._inject_tools_info(react_context)
                    first_call_without_tools = False
                    response = self.base_model.generate_stream(react_context)
                    tool_calls = self._parse_tool_calls_from_text(response)

                tool_results = self._execute_tools(tool_calls)
                for tool_result in tool_results:
                    observation = f"\n[Observation] 工具 {tool_result['tool_name']} 执行结果:\n{tool_result['result']}\n[/Observation]\n"
                    react_context.append({
                        "role": "user",
                        "content": observation
                    })
                    print(f"\n{observation}")
                continue

            if any(stop_phrase.lower() in response.lower() for stop_phrase in self.STOP_PHRASES):
                self.logger.info("检测到停止短语，结束ReAct循环")
                return response

            if not response.strip() or response == "模型调用出错":
                continue

            return response

        return "Agent执行达到最大循环次数"

    def _parse_tool_calls_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中解析工具调用"""
        if hasattr(self.base_model, '_parse_tool_calls'):
            return self.base_model._parse_tool_calls(text)
        return []

    def get_name(self) -> str:
        """获取模型名称"""
        return f"ReAct-{self.base_model.get_name()}"
