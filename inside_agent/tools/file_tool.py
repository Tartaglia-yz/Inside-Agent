import os
from typing import Dict, Any
from .base import BaseTool
import logging

class FileTool(BaseTool):
    """文件系统工具，用于读写文件"""
    
    def __init__(self):
        super().__init__(
            name="file_tool",
            description="用于读写文件的工具"
        )
        self.logger = logging.getLogger(__name__)
    
    def execute(self, arguments: Dict[str, Any]) -> Any:
        """执行文件操作"""
        action = arguments.get("action")
        
        if action == "read":
            return self._read_file(arguments)
        elif action == "write":
            return self._write_file(arguments)
        elif action == "list":
            return self._list_files(arguments)
        else:
            return f"不支持的操作: {action}"
    
    def _read_file(self, arguments: Dict[str, Any]) -> str:
        """读取文件"""
        file_path = arguments.get("file_path")
        
        if not file_path:
            return "错误: 未指定文件路径"
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except Exception as e:
            self.logger.error(f"读取文件出错: {str(e)}")
            return f"读取文件出错: {str(e)}"
    
    def _write_file(self, arguments: Dict[str, Any]) -> str:
        """写入文件"""
        file_path = arguments.get("file_path")
        content = arguments.get("content")
        
        if not file_path:
            return "错误: 未指定文件路径"
        
        if content is None:
            return "错误: 未指定文件内容"
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"文件写入成功: {file_path}"
        except Exception as e:
            self.logger.error(f"写入文件出错: {str(e)}")
            return f"写入文件出错: {str(e)}"
    
    def _list_files(self, arguments: Dict[str, Any]) -> str:
        """列出目录中的文件"""
        directory = arguments.get("directory", ".")
        
        try:
            files = os.listdir(directory)
            return f"目录 {directory} 中的文件: {', '.join(files)}"
        except Exception as e:
            self.logger.error(f"列出文件出错: {str(e)}")
            return f"列出文件出错: {str(e)}"
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "write", "list"],
                        "description": "操作类型"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容"
                    },
                    "directory": {
                        "type": "string",
                        "description": "目录路径"
                    }
                },
                "required": ["action"]
            }
        }
