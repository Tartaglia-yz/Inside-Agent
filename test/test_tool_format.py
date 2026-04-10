#!/usr/bin/env python3
"""
测试模型输出的工具调用格式是否能被正确解析
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模拟工具调用解析函数
def parse_tool_calls(content: str):
    """
    模拟 MiniMaxModel._parse_tool_calls 方法的解析逻辑
    """
    import re
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

    return tool_calls

# 测试用例
test_content = '''
[思考]
用户想查看当前目录下的文件。我应该使用 `ls` 命令来列出当前目录的内容。
[TOOL_CALL] 
 {tool => 'Bash', args => { 
   --command "ls -la" 
   --timeout 10000 
 }} 
 [/TOOL_CALL] 
'''

# 测试解析
def test_tool_parsing():
    print("=== 测试工具调用格式解析 ===")
    print("测试内容:")
    print(test_content)
    
    tool_calls = parse_tool_calls(test_content)
    print("\n解析结果:")
    print(tool_calls)
    
    if tool_calls:
        print("\n解析成功!")
        print(f"工具名称: {tool_calls[0]['function']['name']}")
        print(f"命令参数: {tool_calls[0]['function']['arguments'].get('command')}")
        print("\n这个命令可以被 shell_tool 执行。")
    else:
        print("\n解析失败!")

if __name__ == "__main__":
    test_tool_parsing()
