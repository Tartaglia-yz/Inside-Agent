from typing import List, Dict, Any
import logging

class ContextManager:
    """上下文管理器，用于管理对话历史和上下文"""
    
    def __init__(self, max_tokens: int = 8192):
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)
    
    def add_message(self, role: str, content: Any):
        """添加消息到对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        
        # 检查是否需要清理上下文
        self._manage_context()
    
    def get_context(self) -> List[Dict[str, Any]]:
        """获取当前上下文"""
        return self.conversation_history
    
    def get_full_history(self) -> List[Dict[str, Any]]:
        """获取完整的对话历史"""
        return self.conversation_history.copy()
    
    def _manage_context(self):
        """管理上下文，确保不超过token限制"""
        # 这里可以实现更复杂的上下文管理逻辑
        # 例如基于token数量的清理，或者基于重要性的摘要
        
        # 简单实现：如果历史记录超过一定长度，只保留最近的消息
        if len(self.conversation_history) > 100:
            self.logger.info("对话历史过长，清理旧消息")
            # 保留系统消息和最近的50条消息
            system_messages = [msg for msg in self.conversation_history if msg["role"] == "system"]
            recent_messages = self.conversation_history[-50:]
            self.conversation_history = system_messages + recent_messages
    
    def clear(self):
        """清空对话历史"""
        self.conversation_history = []
