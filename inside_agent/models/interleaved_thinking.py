from typing import Dict, Any, List
from .base import BaseModel
import logging

class InterleavedThinkingModel(BaseModel):
    """支持交错思维的模型包装器"""
    
    def __init__(self, base_model: BaseModel):
        self.base_model = base_model
        self.logger = logging.getLogger(__name__)
    
    def generate(self, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成模型响应，支持交错思维"""
        # 1. 首先调用基础模型获取响应
        response = self.base_model.generate(context)
        
        # 2. 处理交错思维
        if "content" in response and response["content"]:
            # 检查响应中是否包含思考内容
            content = response["content"]
            
            # 这里可以添加更复杂的交错思维处理逻辑
            # 例如识别思考标记、处理多轮思考等
            
            # 简单实现：直接返回响应
            return response
        elif "tool_calls" in response:
            # 处理工具调用
            return response
        else:
            # 错误处理
            return {
                "content": "模型响应格式错误"
            }
    
    def get_name(self) -> str:
        """获取模型名称"""
        return f"Interleaved-{self.base_model.get_name()}"
