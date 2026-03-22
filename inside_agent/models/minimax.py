from anthropic import Anthropic
from typing import Dict, Any, List
from .base import BaseModel
import logging

class MiniMaxModel(BaseModel):
    """MiniMax M2.7模型实现，使用Anthropic SDK"""
    
    def __init__(self, api_key: str, model: str = "MiniMax-M2.7", base_url: str = "https://api.minimaxi.com/anthropic", temperature: float = 0.7, max_tokens: int = 10240):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        # 初始化Anthropic客户端
        self.client = Anthropic(
            api_key=api_key,
            base_url=base_url
        )
        self.logger = logging.getLogger(__name__)
    
    def generate(self, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成模型响应"""
        try:
            # 转换上下文格式以兼容Anthropic API
            messages = self._convert_context(context)
            
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
            # 转换上下文格式以兼容Anthropic API
            messages = self._convert_context(context)
            
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
        
        # 解析 XML 格式的工具调用
        xml_pattern = r'<tool_call>\s*name="([^"]+)"\s*(<parameter name="([^"]+)"[^>]*>([^<]+)</parameter>)?\s*</tool>'
        xml_matches = re.findall(xml_pattern, content, re.DOTALL)
        
        for match in xml_matches:
            tool_name = match[0]
            param_name = match[2]
            param_value = match[3]
            
            # 转换为标准工具调用格式
            tool_call = {
                "id": f"tool_{len(tool_calls)}",
                "type": "function",
                "function": {
                    "name": "file_tool",  # 映射到我们的file_tool
                    "arguments": {
                        "action": "list" if tool_name == "list_directory" else "read",
                        "directory": param_value if param_name == "path" else "."
                    }
                }
            }
            tool_calls.append(tool_call)
        
        # 解析 JSON 格式的工具调用
        json_pattern = r'\[TOOL_CALL\]\s*\{tool => "([^"]+)", args => \{\s*--([^\s]+) "([^"]+)"\s*\}\}\s*\[/TOOL_CALL\]'
        json_matches = re.findall(json_pattern, content, re.DOTALL)
        
        for match in json_matches:
            tool_name = match[0]
            param_name = match[1]
            param_value = match[2]
            
            # 转换为标准工具调用格式
            tool_call = {
                "id": f"tool_{len(tool_calls)}",
                "type": "function",
                "function": {
                    "name": "file_tool",  # 映射到我们的file_tool
                    "arguments": {
                        "action": "list" if tool_name == "list_directory" else "read",
                        "directory": param_value if param_name == "path" else "."
                    }
                }
            }
            tool_calls.append(tool_call)
        
        return tool_calls
    
    def _convert_context(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换上下文格式以兼容Anthropic API"""
        converted = []
        
        # 收集所有消息
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
        
        # 添加系统消息（如果有）
        if system_message:
            converted.append({
                "role": "system",
                "content": system_message
            })
        
        # 添加最近的几条消息
        # 保留最后2条用户消息和最后1条助手消息
        recent_messages = []
        
        # 添加最近的助手消息（如果有）
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
    

