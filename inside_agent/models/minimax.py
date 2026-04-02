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
        if "shell" in tool_name.lower() or "command" in tool_name.lower() or "execute" in tool_name.lower() or "run" in tool_name.lower():
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
        elif "file" in tool_name.lower() or "read" in tool_name.lower() or "write" in tool_name.lower() or "list" in tool_name.lower():
            action = "read" if "read" in tool_name.lower() else ("list" if "list" in tool_name.lower() else "read")
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
        elif tool_name in ["file_tool", "shell_tool"]:
            if tool_name == "shell_tool":
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
        """转换上下文格式以兼容Anthropic API"""
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

        os_info_str = f"""

## 当前运行环境
- 操作系统类型：{self.os_info['os_type'].upper()}
- 默认Shell：{self.os_info['shell']}
- 路径分隔符：{self.os_info['path_separator']}

**重要提示：**
- 请根据上述操作系统类型生成相应的命令
- Windows 系统使用 PowerShell 或 cmd 命令（如 dir, cd, type 等）
- macOS/Linux 系统使用 Bash 命令（如 ls, cd, cat 等）
- 路径格式：Windows 使用反斜杠 \\，Unix 系统使用正斜杠 /
- 当前工作目录命令：{self.os_info['current_dir']}
- 列出目录命令：{self.os_info['list_dir']}
"""

        tools_info = ""
        if tools:
            tools_info = """
## 可用工具
你可以通过生成特殊标记来调用工具。支持的工具：

### file_tool
用于文件操作：
- read: 读取文件内容
- write: 写入文件内容
- list: 列出目录内容

参数：action (操作类型), file_path (文件路径), content (文件内容), directory (目录路径)

### shell_tool
用于执行系统命令：
- 执行Shell命令获取系统信息
- 执行各种终端命令

参数：command (要执行的命令字符串)

**重要：当你需要执行命令时，请使用shell_tool并提供完整的命令字符串。**
**请确保命令符合当前操作系统环境！**

调用格式示例：
<tool_call>name="shell_tool"<parameter name="command">""" + self.os_info['list_dir'] + """</parameter></tool_call>
"""

        if system_message:
            if tools_info and tools_info not in system_message:
                system_message = system_message + os_info_str + tools_info
            elif os_info_str not in system_message:
                system_message = system_message + os_info_str
            converted.append({
                "role": "system",
                "content": system_message
            })
        else:
            converted.append({
                "role": "system",
                "content": "你是 Inside Agent，一个智能助手。" + os_info_str + tools_info
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
        
        # 添加最近的用户消息（如果有）
        for i, msg in enumerate(reversed(user_messages)):
            if i < 2:  # 只保留最近2条
                recent_messages.insert(0, {
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": msg
                    }]
                })
        
        # 将最近的消息添加到转换后的上下文中
        converted.extend(recent_messages)
        
        # 如果没有用户消息，添加一个默认消息
        if not user_messages:
            converted.append({
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": "Hello"
                }]
            })
        
        return converted
    

