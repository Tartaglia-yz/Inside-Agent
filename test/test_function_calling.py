#!/usr/bin/env python3
"""测试模型是否使用 Function Calling 格式返回系统命令"""

import os
import sys
import json

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inside_agent.models.minimax import MiniMaxModel, get_os_info
from inside_agent.tools.shell_tool import ShellTool
from inside_agent.tools.file_tool import FileTool


def load_env_file(env_path):
    """从 .env 文件加载环境变量"""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def test_function_calling():
    """测试 Function Calling 功能"""
    print("=" * 80)
    print("测试 Function Calling 格式返回系统命令")
    print("=" * 80)
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 加载 .env 文件
    env_path = os.path.join(project_root, ".env")
    env_vars = load_env_file(env_path)
    
    # 设置环境变量（优先使用 .env 中的值）
    for key, value in env_vars.items():
        if key.endswith("_API_KEY") and key != "ANTHROPIC_API_KEY":
            os.environ[key] = value
    
    # 加载配置
    config_path = os.path.join(project_root, "agent.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 获取 API Key（优先从环境变量获取，然后从 .env 获取）
    api_key = os.environ.get("MINIMAX_API_KEY") or env_vars.get("MINIMAX_API_KEY")
    if not api_key:
        # 尝试使用 ANTHROPIC_API_KEY
        api_key = os.environ.get("ANTHROPIC_API_KEY") or env_vars.get("ANTHROPIC_API_KEY")
        if api_key:
            print("注意: 使用 ANTHROPIC_API_KEY 作为 API Key")
    
    if not api_key:
        print("错误: 请在 .env 文件中设置 MINIMAX_API_KEY 或 ANTHROPIC_API_KEY")
        print(f"检查路径: {env_path}")
        return
    
    # 获取 OS 信息
    os_info = get_os_info()
    print(f"\n当前系统信息:")
    print(f"  - OS 类型: {os_info.get('os_type', 'unknown')}")
    print(f"  - Shell: {os_info.get('shell', 'unknown')}")
    print(f"  - 列出目录命令: {os_info.get('list_dir', 'unknown')}")
    print(f"  - 当前目录命令: {os_info.get('current_dir', 'unknown')}")
    
    # 初始化工具
    shell_tool = ShellTool()
    file_tool = FileTool()
    
    # 初始化模型
    model = MiniMaxModel(
        api_key=api_key,
        model=config["model"]["model_name"],
        base_url=config["model"].get("anthropic_base_url", "https://api.minimaxi.com/anthropic"),
        temperature=config["model"].get("temperature", 0.7),
        max_tokens=config["model"].get("max_tokens", 10240),
        tools=[shell_tool, file_tool],
        os_info=os_info
    )
    
    print(f"\n模型配置:")
    print(f"  - 模型名称: {config['model']['model_name']}")
    print(f"  - Temperature: {config['model'].get('temperature', 0.7)}")
    print(f"  - Max Tokens: {config['model'].get('max_tokens', 10240)}")
    
    # 测试问题
    test_questions = [
        "获取当前系统时间",
        "列出当前目录下的文件",
        "查看当前工作目录"
    ]
    
    for question in test_questions:
        print("\n" + "=" * 80)
        print(f"测试问题: {question}")
        print("=" * 80)
        
        # 构建上下文
        context = [
            {
                "role": "system",
                "content": f"""你是 Inside Agent，一个智能助手。当前操作系统信息：
- OS 类型: {os_info.get('os_type', 'unknown')}
- Shell: {os_info.get('shell', 'unknown')}

当需要执行系统命令时，请使用 shell_tool 工具。"""
            },
            {
                "role": "user",
                "content": question
            }
        ]
        
        # 调用模型
        print("\n模型返回内容:")
        print("-" * 80)
        response = model.generate(context)
        print("-" * 80)
        print("-" * 80)
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print("-" * 80)
        
        # 分析响应
        print("\n响应分析:")
        print(f"  - 是否包含 content: {'content' in response}")
        if 'content' in response:
            content_preview = response['content'][:200] + "..." if len(response['content']) > 200 else response['content']
            print(f"  - content 内容: {content_preview}")
        
        print(f"  - 是否包含 tool_calls: {'tool_calls' in response}")
        if 'tool_calls' in response:
            print(f"  - tool_calls 数量: {len(response['tool_calls'])}")
            for i, tool_call in enumerate(response['tool_calls']):
                print(f"\n  工具调用 #{i+1}:")
                print(f"    - 工具名称: {tool_call.get('function', {}).get('name', 'unknown')}")
                print(f"    - 参数: {tool_call.get('function', {}).get('arguments', {})}")
                
                # 执行命令
                tool_name = tool_call.get('function', {}).get('name', '')
                tool_args = tool_call.get('function', {}).get('arguments', {})
                
                if tool_name == 'shell_tool' and 'command' in tool_args:
                    print(f"\n  执行命令: {tool_args['command']}")
                    result = shell_tool.execute(tool_args)
                    print(f"  执行结果:\n{result}")
        
        print("\n")
    
    print("=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_function_calling()
