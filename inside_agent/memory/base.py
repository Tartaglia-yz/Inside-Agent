from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseMemory(ABC):
    """记忆基类，定义记忆的基本接口"""
    
    @abstractmethod
    def save_conversation(self, conversation: List[Dict[str, Any]]):
        """保存对话"""
        pass
    
    @abstractmethod
    def load_conversation(self) -> List[Dict[str, Any]]:
        """加载对话"""
        pass
    
    @abstractmethod
    def clear(self):
        """清空记忆"""
        pass
