#!/usr/bin/env python3
"""
直接测试 ShellTool 类的 execute 方法
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inside_agent.tools.shell_tool import ShellTool

# 创建 ShellTool 实例
shell_tool = ShellTool()

# 测试命令列表
test_commands = [
    "echo Hello World",  # 测试基本输出
    "dir",  # Windows 命令，列出当前目录
    "echo %PATH%",  # Windows 命令，查看环境变量
]

# 测试执行命令
def test_shell_tool():
    print("=== 测试 ShellTool 直接执行命令 ===")
    
    for command in test_commands:
        print(f"\n测试命令: {command}")
        try:
            result = shell_tool.execute({"command": command})
            print("执行结果:")
            print(result)
            print("执行成功!")
        except Exception as e:
            print(f"执行失败: {e}")

if __name__ == "__main__":
    test_shell_tool()
