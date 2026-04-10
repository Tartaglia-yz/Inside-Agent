#!/usr/bin/env python3
"""
测试 bash 代码块格式的工具调用解析
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

    # 解析 bash 代码块格式
    bash_pattern = r'```bash\s*([^`]+)\s*```'
    bash_matches = re.findall(bash_pattern, content, re.DOTALL)

    for match in bash_matches:
        command = match.strip()
        if command:
            tool_call = {
                "function": {
                    "name": "shell_tool",
                    "arguments": {
                        "command": command
                    }
                }
            }
            tool_calls.append(tool_call)

    # 解析 shell 代码块格式
    shell_pattern = r'```shell\s*([^`]+)\s*```'
    shell_matches = re.findall(shell_pattern, content, re.DOTALL)

    for match in shell_matches:
        command = match.strip()
        if command:
            tool_call = {
                "function": {
                    "name": "shell_tool",
                    "arguments": {
                        "command": command
                    }
                }
            }
            tool_calls.append(tool_call)

    return tool_calls

# 测试用例
test_content = '''
[思考]
用户想要检查当前系统时间。我需要执行一个命令来获取系统时间。在 Linux/Unix 系统上，可以使用 `date` 命令来
查看当前日期和时间。
我来帮你检查当前的系统时间。

```bash
date
```

这个命令会显示当前的系统日期和时间，包括时区信息。
'''

# 测试解析
def test_tool_parsing():
    print("=== 测试 bash 代码块格式解析 ===")
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
