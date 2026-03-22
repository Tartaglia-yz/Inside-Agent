import logging
from typing import List, Dict, Any, Optional
from .models.base import BaseModel
from .tools.base import BaseTool
from .memory.base import BaseMemory
from .utils.context_manager import ContextManager

class Agent:
    """核心Agent类，实现完整的执行循环"""
    
    def __init__(
        self,
        model: BaseModel,
        tools: List[BaseTool],
        memory: BaseMemory,
        context_manager: ContextManager,
        name: str = "Inside Agent"
    ):
        self.model = model
        self.tools = tools
        self.memory = memory
        self.context_manager = context_manager
        self.name = name
        self.logger = logging.getLogger(__name__)
    
    def run(self, user_input: str) -> str:
        """执行Agent的完整循环"""
        try:
            # 1. 处理用户输入，添加到上下文
            self.context_manager.add_message("user", user_input)
            
            # 2. 获取历史上下文
            context = self.context_manager.get_context()
            
            # 3. 调用模型获取响应
            response = self.model.generate(context)
            
            # 4. 处理模型响应
            if "tool_calls" in response:
                # 处理工具调用
                tool_results = self._execute_tools(response["tool_calls"])
                
                # 将工具结果添加到上下文
                for tool_result in tool_results:
                    self.context_manager.add_message("tool", tool_result)
                
                # 再次调用模型获取最终响应
                context = self.context_manager.get_context()
                final_response = self.model.generate(context)
                
                # 添加最终响应到上下文
                self.context_manager.add_message("assistant", final_response["content"])
                
                # 保存到记忆
                self.memory.save_conversation(self.context_manager.get_full_history())
                
                return final_response["content"]
            else:
                # 直接返回模型响应
                self.context_manager.add_message("assistant", response["content"])
                
                # 保存到记忆
                self.memory.save_conversation(self.context_manager.get_full_history())
                
                return response["content"]
        
        except Exception as e:
            self.logger.error(f"Agent执行出错: {str(e)}")
            return f"执行出错: {str(e)}"
    
    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]
            
            # 查找对应的工具
            tool = next((t for t in self.tools if t.name == tool_name), None)
            
            if tool:
                try:
                    result = tool.execute(tool_args)
                    results.append({
                        "tool_call_id": tool_call["id"],
                        "tool_name": tool_name,
                        "result": result
                    })
                except Exception as e:
                    self.logger.error(f"工具执行出错 {tool_name}: {str(e)}")
                    results.append({
                        "tool_call_id": tool_call["id"],
                        "tool_name": tool_name,
                        "result": f"执行出错: {str(e)}"
                    })
            else:
                results.append({
                    "tool_call_id": tool_call["id"],
                    "tool_name": tool_name,
                    "result": f"工具未找到: {tool_name}"
                })
        
        return results
