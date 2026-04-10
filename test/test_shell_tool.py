#!/usr/bin/env python3
"""
测试 shell_tool 功能的脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inside_agent.tools.shell_tool import ShellTool
from inside_agent.tools.file_tool import FileTool
from inside_agent.models.interleaved_thinking import InterleavedThinkingModel

# 创建一个模拟的基础模型类
class MockBaseModel:
    def __init__(self, os_info=None):
        self.os_info = os_info
    
    def generate(self, context):
        # 模拟返回包含工具调用的响应
        return {
            "content": "[思考] 我需要执行一个测试命令",
            "tool_calls": [{
                "function": {
                    "name": "shell_tool",
                    "arguments": {
                        "command": "echo Test command executed successfully"
                    }
                }
            }]
        }
    
    def get_name(self):
        return "mock_model"

# 测试 shell_tool 直接调用
def test_shell_tool_direct():
    print("=== 测试 shell_tool 直接调用 ===")
    tool = ShellTool()
    result = tool.execute({"command": "echo Hello World"})
    print("测试结果:", result)
    print("执行成功" if "Hello World" in result else "执行失败")
    print()

# 测试 InterleavedThinkingModel 工具调用
def test_interleaved_thinking_model():
    print("=== 测试 InterleavedThinkingModel 工具调用 ===")
    
    # 创建模拟的 OS 信息
    os_info = {
        "os_type": "windows",
        "shell": "powershell",
        "list_dir": "dir",
        "current_dir": "cd"
    }
    
    # 初始化模型和工具
    base_model = MockBaseModel(os_info=os_info)
    tools = [ShellTool(), FileTool()]
    model = InterleavedThinkingModel(base_model=base_model, tools=tools)
    
    # 测试 os_info 是否正确传递
    print("OS Info:", model.os_info)
    
    # 测试工具信息构建
    tools_info = model._build_tools_info()
    print("工具信息构建成功")
    print("包含 shell_tool:", "shell_tool" in tools_info)
    
    # 测试工具执行
    test_context = [{"role": "user", "content": "执行测试命令"}]
    response = model.run_with_react(test_context)
    print("模型响应:", response)
    print()

if __name__ == "__main__":
    test_shell_tool_direct()
    test_interleaved_thinking_model()
    print("所有测试完成！")
