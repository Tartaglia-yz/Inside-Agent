#!/usr/bin/env python3
"""
简化的工具调用解析测试脚本（不依赖 anthropic 模块）
"""

import re

def parse_tool_calls(content: str) -> list:
    """
    简化的工具调用解析函数
    """
    tool_calls = []

    # 匹配包含多个参数的TOOL_CALL格式（支持单引号和双引号）
    json_pattern = r'\[TOOL_CALL\]\s*\{tool =>\s*["\']([^"\']+)["\'],\s*args =>\s*\{(.*?)\}\}\s*\[/TOOL_CALL\]'
    json_matches = re.findall(json_pattern, content, re.DOTALL)

    for match in json_matches:
        tool_name = match[0]
        args_str = match[1]
        # 提取所有参数
        params = {}
        param_pattern = r'--([^\s]+)\s+["\']([^"\']+)["\']'
        param_matches = re.findall(param_pattern, args_str)
        for param_match in param_matches:
            params[param_match[0]] = param_match[1]
        # 优先使用command参数
        if 'command' in params:
            tool_call = {
                "function": {
                    "name": "shell_tool" if 'bash' in tool_name.lower() or 'shell' in tool_name.lower() else tool_name,
                    "arguments": {
                        "command": params['command']
                    }
                }
            }
            tool_calls.append(tool_call)

    # 匹配无括号的工具调用格式（支持单引号和双引号）
    unbracketed_pattern = r'\{tool\s*=>\s*["\']([^"\']+)["\'],\s*args\s*=>\s*\{(.*?)\}\}'
    unbracketed_matches = re.findall(unbracketed_pattern, content, re.IGNORECASE | re.DOTALL)

    for match in unbracketed_matches:
        tool_name = match[0]
        args_str = match[1]
        # 提取所有参数
        params = {}
        param_pattern = r'--([^\s]+)\s+["\']([^"\']+)["\']'
        param_matches = re.findall(param_pattern, args_str)
        for param_match in param_matches:
            params[param_match[0]] = param_match[1]
        # 优先使用command参数
        if 'command' in params:
            tool_call = {
                "function": {
                    "name": "shell_tool" if 'bash' in tool_name.lower() or 'shell' in tool_name.lower() else tool_name,
                    "arguments": {
                        "command": params['command']
                    }
                }
            }
            tool_calls.append(tool_call)

    return tool_calls

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
    tool_calls_1 = parse_tool_calls(test_content_1)
    print(f"解析结果: {tool_calls_1}")
    print(f"解析成功: {len(tool_calls_1) > 0}")
    if tool_calls_1:
        print(f"工具名称: {tool_calls_1[0]['function']['name']}")
        print(f"命令参数: {tool_calls_1[0]['function']['arguments'].get('command')}")
    
    # 测试用例 2
    print("\n测试用例 2: 无括号的工具调用格式")
    tool_calls_2 = parse_tool_calls(test_content_2)
    print(f"解析结果: {tool_calls_2}")
    print(f"解析成功: {len(tool_calls_2) > 0}")
    if tool_calls_2:
        print(f"工具名称: {tool_calls_2[0]['function']['name']}")
        print(f"命令参数: {tool_calls_2[0]['function']['arguments'].get('command')}")
    
    # 测试用例 3
    print("\n测试用例 3: 直接使用 shell_tool")
    tool_calls_3 = parse_tool_calls(test_content_3)
    print(f"解析结果: {tool_calls_3}")
    print(f"解析成功: {len(tool_calls_3) > 0}")
    if tool_calls_3:
        print(f"工具名称: {tool_calls_3[0]['function']['name']}")
        print(f"命令参数: {tool_calls_3[0]['function']['arguments'].get('command')}")

if __name__ == "__main__":
    test_tool_parsing()
    print("\n所有测试完成！")
