from anthropic import Anthropic
from typing import Dict, Any, List, Optional
from .base import BaseModel
import logging
import platform
import os

def get_os_info() -> Dict[str, str]:
    """獲取當前操作系統信息"""
    system = platform.system().lower()

    if system == "windows":
        return {
            "os_type": "windows",
            "shell": "powershell" if os.environ.get("PSModulePath") else "cmd",
            "list_dir": "dir",
            "current_dir": "cd",
            "path_separator": "\\"
        }
    elif system == "darwin":
        return {
            "os_type": "macos",
            "shell": "bash",
            "list_dir": "ls -la",
            "current_dir": "pwd",
            "path_separator": "/"
        }
    elif system == "linux":
        return {
            "os_type": "linux",
            "shell": "bash",
            "list_dir": "ls -la",
            "current_dir": "pwd",
            "path_separator": "/"
        }
    else:
        return {
            "os_type": system,
            "shell": "bash",
            "list_dir": "ls",
            "current_dir": "pwd",
            "path_separator": "/"
        }

class MiniMaxModel(BaseModel):
    """MiniMax M2.7模型实现，使用Anthropic SDK"""

    def __init__(self, api_key: str, model: str = "MiniMax-M2.7", base_url: str = "https://api.minimaxi.com/anthropic", temperature: float = 0.7, max_tokens: int = 10240, tools: List[Any] = None, os_info: Dict[str, str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = tools or []
        self.os_info = os_info or get_os_info()
        self.client = Anthropic(
            api_key=api_key,
            base_url=base_url
        )
        self.logger = logging.getLogger(__name__)

    def generate(self, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成模型响应"""
        try:
            messages = self._convert_context(context, self.tools)
            
            # 使用Anthropic SDK调用模型
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False
            )
            
            # 处理响应
            content_parts = []
            
            # 遍历响应内容
            for block in response.content:
                if block.type == "thinking":
                    # 包含思考过程
                    content_parts.append(f"\n[思考]\n{block.thinking}\n")
                elif block.type == "text":
                    # 包含文本内容
                    content_parts.append(block.text)
            
            # 组合所有内容
            full_content = "".join(content_parts)
            
            # 检查是否包含工具调用标记
            tool_calls = self._parse_tool_calls(full_content)
            if tool_calls:
                return {
                    "content": full_content,
                    "tool_calls": tool_calls
                }
            
            return {
                "content": full_content
            }
            
        except Exception as e:
            self.logger.error(f"模型调用出错: {str(e)}")
            return {
                "content": f"模型调用出错: {str(e)}"
            }
    
    def generate_stream(self, context: List[Dict[str, Any]]) -> str:
        """流式生成模型响应，支持thinking过程"""
        try:
            messages = self._convert_context(context, self.tools)
            
            # 使用Anthropic SDK调用模型，启用流式输出
            stream = self.client.messages.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )
            
            reasoning_buffer = ""
            text_buffer = ""
            
            for chunk in stream:
                if chunk.type == "content_block_start":
                    if hasattr(chunk, "content_block") and chunk.content_block:
                        if chunk.content_block.type == "text":
                            print("\n" + "=" * 60)
                            print("Response Content:")
                            print("=" * 60)
                
                elif chunk.type == "content_block_delta":
                    if hasattr(chunk, "delta") and chunk.delta:
                        if chunk.delta.type == "thinking_delta":
                            # 流式输出 thinking 过程
                            new_thinking = chunk.delta.thinking
                            if new_thinking:
                                print(new_thinking, end="", flush=True)
                                reasoning_buffer += new_thinking
                        elif chunk.delta.type == "text_delta":
                            # 流式输出文本内容
                            new_text = chunk.delta.text
                            if new_text:
                                print(new_text, end="", flush=True)
                                text_buffer += new_text
            
            print("\n")
            return text_buffer
            
        except Exception as e:
            self.logger.error(f"模型调用出错: {str(e)}")
            return f"模型调用出错: {str(e)}"
    
    def get_name(self) -> str:
        """获取模型名称"""
        return self.model
    
    def _parse_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """解析模型生成的工具调用标记"""
        import re
        tool_calls = []

        all_tool_names = ["file_tool", "shell_tool", "list_directory", "read_file", "write_file", "execute_command", "run"]

        xml_pattern = r'<tool_call>\s*name="([^"]+)"\s*(<parameter name="([^"]+)"[^>]*>([^<]+)</parameter>)?\s*</tool>'
        xml_matches = re.findall(xml_pattern, content, re.DOTALL)

        for match in xml_matches:
            tool_name = match[0]
            param_name = match[2]
            param_value = match[3]

            tool_call = self._create_tool_call(tool_name, param_name, param_value)
            if tool_call:
                tool_calls.append(tool_call)

        json_pattern = r'\[TOOL_CALL\]\s*\{tool => "([^"]+)", args => \{\s*--([^\s]+) "([^"]+)"\s*\}\}\s*\[/TOOL_CALL\]'
        json_matches = re.findall(json_pattern, content, re.DOTALL)

        for match in json_matches:
            tool_name = match[0]
            param_name = match[1]
            param_value = match[2]

            tool_call = self._create_tool_call(tool_name, param_name, param_value)
            if tool_call:
                tool_calls.append(tool_call)

        unbracketed_pattern = r'\{tool\s*=>\s*"([^"]+)",\s*args\s*=>\s*\{\s*--([^\s]+)\s+"([^"]+)"[^}]*\}\}'
        unbracketed_matches = re.findall(unbracketed_pattern, content, re.IGNORECASE | re.DOTALL)

        for match in unbracketed_matches:
            tool_name = match[0]
            param_name = match[1]
            param_value = match[2]

            tool_call = self._create_tool_call(tool_name, param_name, param_value)
            if tool_call:
                tool_calls.append(tool_call)

        simple_pattern = r'(?:tool_call|execute|run|call)\s*:\s*(\w+)[\s\(]+([^)]+)?'
        simple_matches = re.findall(simple_pattern, content, re.IGNORECASE)

        for match in simple_matches:
            tool_name = match[0].strip()
            param_value = match[1].strip() if len(match) > 1 and match[1] else ""

            tool_call = self._create_tool_call(tool_name, "command" if "shell" in tool_name or "command" in tool_name else "path", param_value)
            if tool_call:
                tool_calls.append(tool_call)

        return tool_calls

    def _create_tool_call(self, tool_name: str, param_name: str, param_value: str) -> Optional[Dict[str, Any]]:
        """根据工具名称创建标准化的工具调用"""
        tool_name_lower = tool_name.lower()
        if "shell" in tool_name_lower or "bash" in tool_name_lower or "command" in tool_name_lower or "execute" in tool_name_lower or "run" in tool_name_lower:
            return {
                "id": f"tool_{id(self)}",
                "type": "function",
                "function": {
                    "name": "shell_tool",
                    "arguments": {
                        "command": param_value or ""
                    }
                }
            }
        elif "file" in tool_name_lower or "read" in tool_name_lower or "write" in tool_name_lower or "list" in tool_name_lower:
            action = "read" if "read" in tool_name_lower else ("list" if "list" in tool_name_lower else "read")
            return {
                "id": f"tool_{id(self)}",
                "type": "function",
                "function": {
                    "name": "file_tool",
                    "arguments": {
                        "action": action,
                        "file_path": param_value if param_name in ["path", "file_path", "file"] else param_value
                    }
                }
            }
        elif tool_name in ["file_tool", "shell_tool", "Bash", "bash"]:
            if tool_name in ["shell_tool", "Bash", "bash"]:
                return {
                    "id": f"tool_{id(self)}",
                    "type": "function",
                    "function": {
                        "name": "shell_tool",
                        "arguments": {
                            "command": param_value or ""
                        }
                    }
                }
            else:
                return {
                    "id": f"tool_{id(self)}",
                    "type": "function",
                    "function": {
                        "name": "file_tool",
                        "arguments": {
                            "action": "read",
                            "file_path": param_value or ""
                        }
                    }
                }

        return None
    
    def _convert_context(self, context: List[Dict[str, Any]], tools: List[Any] = None) -> List[Dict[str, Any]]:
        """转换上下文格式以兼容Anthropic API

        注意：不再自动添加OS信息和工具说明
        - OS信息由InterleavedThinkingModel在需要时动态注入
        - 工具说明在检测到工具调用需求时动态注入
        """
        converted = []

        system_message = None
        user_messages = []
        assistant_messages = []

        for message in context:
            role = message["role"]
            content = message["content"]

            if role == "system":
                system_message = content
            elif role == "user":
                user_messages.append(content)
            elif role == "assistant":
                assistant_messages.append(content)

        if system_message:
            converted.append({
                "role": "system",
                "content": system_message
            })
        else:
            converted.append({
                "role": "system",
                "content": "你是 Inside Agent，一个智能助手。"
            })

        recent_messages = []

        if assistant_messages:
            recent_messages.append({
                "role": "assistant",
                "content": [{
                    "type": "text",
                    "text": assistant_messages[-1]
                }]
            })

        for i, msg in enumerate(reversed(user_messages)):
            if i < 2:
                recent_messages.insert(0, {
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": msg
                    }]
                })

        converted.extend(recent_messages)

        if not user_messages:
            converted.append({
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": "Hello"
                }]
            })

        return converted
    

