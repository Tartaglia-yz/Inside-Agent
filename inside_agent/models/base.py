from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseModel(ABC):
    """模型基类，定义模型的基本接口"""
    
    @abstractmethod
    def generate(self, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成模型响应"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取模型名称"""
        pass
