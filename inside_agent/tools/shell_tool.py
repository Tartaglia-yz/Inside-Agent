import subprocess
from typing import Dict, Any
from .base import BaseTool
import logging

class ShellTool(BaseTool):
    """Shell操作工具，用于执行系统命令"""
    
    def __init__(self):
        super().__init__(
            name="shell_tool",
            description="用于执行系统命令的工具"
        )
        self.logger = logging.getLogger(__name__)
    
    def execute(self, arguments: Dict[str, Any]) -> Any:
        """执行Shell命令"""
        command = arguments.get("command")
        
        if not command:
            return "错误: 未指定命令"
        
        try:
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # 设置30秒超时
            )
            
            # 构建响应
            output = f"命令执行结果:\n"
            output += f"返回码: {result.returncode}\n"
            
            if result.stdout:
                output += f"标准输出:\n{result.stdout}\n"
            
            if result.stderr:
                output += f"标准错误:\n{result.stderr}\n"
            
            return output
        except subprocess.TimeoutExpired:
            return "命令执行超时"
        except Exception as e:
            self.logger.error(f"执行命令出错: {str(e)}")
            return f"执行命令出错: {str(e)}"
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的Shell命令"
                    }
                },
                "required": ["command"]
            }
        }
