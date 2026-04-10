#!/usr/bin/env python3
"""
测试系统信息处理功能的脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inside_agent.models.interleaved_thinking import InterleavedThinkingModel

# 创建一个模拟的基础模型类
class MockBaseModel:
    def __init__(self, os_info=None):
        self.os_info = os_info
    
    def generate(self, context):
        return {
            "content": "测试响应",
            "tool_calls": []
        }
    
    def get_name(self):
        return "mock_model"

# 测试系统信息处理
def test_system_info():
    print("=== 测试系统信息处理 ===")
    
    # 测试 Windows 系统信息
    print("\n测试 Windows 系统信息:")
    windows_os_info = {
        "os_type": "windows",
        "shell": "powershell",
        "list_dir": "dir",
        "current_dir": "cd",
        "path_separator": "\\"
    }
    
    base_model = MockBaseModel(os_info=windows_os_info)
    model = InterleavedThinkingModel(base_model=base_model)
    
    # 测试 os_info 是否正确传递
    print(f"OS Info: {model.os_info}")
    print(f"OS Type: {model.os_info.get('os_type')}")
    
    # 测试工具信息构建
    tools_info = model._build_tools_info()
    print("\n工具信息包含 Windows 命令:", "Windows命令示例" in tools_info)
    print("工具信息包含 dir 命令:", "列出目录：dir" in tools_info)
    print("工具信息包含 type 命令:", "查看文件内容：type" in tools_info)
    
    # 测试工具信息注入
    test_context = [{"role": "system", "content": "你是一个智能助手"}]
    injected_context = model._inject_tools_info(test_context)
    print("\n工具信息注入成功:", len(injected_context) > 0)
    print("系统信息已注入:", "当前系统环境" in injected_context[0]['content'])
    
    # 测试重复注入防止
    second_injection = model._inject_tools_info(injected_context)
    print("\n重复注入防止:", second_injection is injected_context)
    
    # 测试 Linux 系统信息
    print("\n\n测试 Linux 系统信息:")
    linux_os_info = {
        "os_type": "linux",
        "shell": "bash",
        "list_dir": "ls -la",
        "current_dir": "pwd",
        "path_separator": "/"
    }
    
    base_model_linux = MockBaseModel(os_info=linux_os_info)
    model_linux = InterleavedThinkingModel(base_model=base_model_linux)
    
    tools_info_linux = model_linux._build_tools_info()
    print("工具信息包含 Linux 命令:", "Linux/macOS命令示例" in tools_info_linux)
    print("工具信息包含 ls 命令:", "列出目录：ls -la" in tools_info_linux)
    print("工具信息包含 cat 命令:", "查看文件内容：cat" in tools_info_linux)

if __name__ == "__main__":
    test_system_info()
    print("\n所有测试完成！")
