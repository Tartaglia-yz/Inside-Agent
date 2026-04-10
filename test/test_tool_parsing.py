#!/usr/bin/env python3
"""
测试工具调用解析功能的脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inside_agent.models.minimax import MiniMaxModel

# 创建一个测试实例
test_model = MiniMaxModel(api_key='test_key')

# 测试用例 1: 包含多个参数的 TOOL_CALL 格式
test_content_1 = '''
[思考]
用户想查看当前目录下的文件。我应该使用 `ls` 命令来列出当前目录的内容。
[TOOL_CALL]
{tool => 'Bash', args => {
  --command "ls -la"
  --timeout 10000
}}
[/TOOL_CALL]
'''

# 测试用例 2: 无括号的工具调用格式
test_content_2 = '''
[思考]
用户想查看当前目录下的文件。我应该使用 `ls` 命令来列出当前目录的内容。
{tool => 'Bash', args => {
  --command "ls -la"
  --timeout 10000
}}
'''

# 测试用例 3: 直接使用 shell_tool
test_content_3 = '''
[思考]
用户想查看当前目录下的文件。我应该使用 `ls` 命令来列出当前目录的内容。
[TOOL_CALL]
{tool => 'shell_tool', args => {
  --command "ls -la"
}}
[/TOOL_CALL]
'''

def test_tool_parsing():
    print("=== 测试工具调用解析 ===")
    
    # 测试用例 1
    print("\n测试用例 1: 包含多个参数的 TOOL_CALL 格式")
    tool_calls_1 = test_model._parse_tool_calls(test_content_1)
    print(f"解析结果: {tool_calls_1}")
    print(f"解析成功: {len(tool_calls_1) > 0}")
    if tool_calls_1:
        print(f"工具名称: {tool_calls_1[0]['function']['name']}")
        print(f"命令参数: {tool_calls_1[0]['function']['arguments'].get('command')}")
    
    # 测试用例 2
    print("\n测试用例 2: 无括号的工具调用格式")
    tool_calls_2 = test_model._parse_tool_calls(test_content_2)
    print(f"解析结果: {tool_calls_2}")
    print(f"解析成功: {len(tool_calls_2) > 0}")
    if tool_calls_2:
        print(f"工具名称: {tool_calls_2[0]['function']['name']}")
        print(f"命令参数: {tool_calls_2[0]['function']['arguments'].get('command')}")
    
    # 测试用例 3
    print("\n测试用例 3: 直接使用 shell_tool")
    tool_calls_3 = test_model._parse_tool_calls(test_content_3)
    print(f"解析结果: {tool_calls_3}")
    print(f"解析成功: {len(tool_calls_3) > 0}")
    if tool_calls_3:
        print(f"工具名称: {tool_calls_3[0]['function']['name']}")
        print(f"命令参数: {tool_calls_3[0]['function']['arguments'].get('command')}")

if __name__ == "__main__":
    test_tool_parsing()
    print("\n所有测试完成！")
