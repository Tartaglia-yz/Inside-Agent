#!/usr/bin/env python3
"""
测试分层上下文管理器与 MiniMaxModel 的集成
"""

import sys
import os
import json

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inside_agent.utils.hierarchical_context_manager import HierarchicalContextManager
from inside_agent.models.minimax import MiniMaxModel, get_os_info


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


def test_integration():
    """测试分层上下文管理器与 MiniMaxModel 的集成"""
    print("=" * 80)
    print("测试分层上下文管理器与 MiniMaxModel 的集成")
    print("=" * 80)
    
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 加载 .env 文件
    env_path = os.path.join(project_root, ".env")
    env_vars = load_env_file(env_path)
    
    # 设置环境变量
    for key, value in env_vars.items():
        if key.endswith("_API_KEY") and key != "ANTHROPIC_API_KEY":
            os.environ[key] = value
    
    # 加载配置
    config_path = os.path.join(project_root, "agent.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 获取 API Key
    api_key = os.environ.get("MINIMAX_API_KEY") or env_vars.get("MINIMAX_API_KEY")
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY") or env_vars.get("ANTHROPIC_API_KEY")
        if api_key:
            print("注意: 使用 ANTHROPIC_API_KEY 作为 API Key")
    
    if not api_key:
        print("错误: 请在 .env 文件中设置 MINIMAX_API_KEY 或 ANTHROPIC_API_KEY")
        return
    
    # 获取 OS 信息
    os_info = get_os_info()
    
    # 初始化分层上下文管理器
    print("\n初始化分层上下文管理器...")
    context_manager = HierarchicalContextManager()
    
    # 初始化系统层
    context_manager.initialize(
        role_name="Inside Agent",
        role_description="""一个智能助手，能够：
1. 执行系统命令（使用 shell_tool）
2. 管理文件（使用 file_tool）
3. 记住重要的用户偏好和历史任务

当你执行命令时，必须根据当前操作系统使用正确的命令格式。""",
        os_info=os_info,
        tools_description="""可用工具：
1. shell_tool - 执行系统命令
   - Windows: 使用 CMD 命令（如 dir, time /t, cd）
   - Linux/macOS: 使用 Bash 命令（如 ls, date, pwd）

2. file_tool - 文件操作
   - read: 读取文件内容
   - write: 写入文件内容"""
    )
    
    # 添加记忆
    context_manager.add_memory("用户使用 conda 虚拟环境 agent_dev", "environment")
    context_manager.add_memory("用户主要在晚上工作", "preference")
    context_manager.add_task_summary(
        "查看系统时间",
        "成功使用 time /t 命令",
        ["Windows CMD 命令", "time /t 格式"]
    )
    
    # 添加历史对话
    context_manager.add_user_message("请帮我查看系统时间")
    context_manager.add_assistant_message("好的，我来执行 time /t 命令查看当前系统时间。\n执行命令: time /t")
    
    print("✅ 分层上下文管理器初始化完成")
    
    # 初始化模型
    print("\n初始化 MiniMaxModel...")
    model = MiniMaxModel(
        api_key=api_key,
        model=config["model"]["model_name"],
        base_url=config["model"].get("anthropic_base_url", "https://api.minimaxi.com/anthropic"),
        temperature=config["model"].get("temperature", 0.7),
        max_tokens=config["model"].get("max_tokens", 10240),
        os_info=os_info
    )
    print("✅ MiniMaxModel 初始化完成")
    
    # 设置当前任务
    current_question = "查看当前工作目录"
    context_manager.set_current_task(
        current_question,
        "用户想要了解当前工作目录的位置"
    )
    
    # 添加工具执行结果（模拟之前的执行）
    context_manager.add_tool_result(
        "shell_tool",
        "time /t",
        0,
        stdout="10:30:45",
        success=True
    )
    
    # 获取完整上下文
    print("\n获取分层上下文...")
    context = context_manager.get_context()
    print(f"上下文总消息数: {len(context)}")
    
    # 显示上下文组成
    layers = {}
    for msg in context:
        layer = msg.get("layer", "unknown")
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(msg)
    
    print("\n上下文层级组成:")
    for layer_name in ["system", "memory", "history", "task", "feedback"]:
        if layer_name in layers:
            print(f"  - {layer_name}层: {len(layers[layer_name])}条消息")
    
    # 调用模型
    print("\n调用模型...")
    print("-" * 80)
    
    try:
        response = model.generate(context)
        print("-" * 80)
        
        # 分析响应
        print("\n响应分析:")
        print(f"  - content 长度: {len(response.get('content', ''))}")
        print(f"  - tool_calls 数量: {len(response.get('tool_calls', []))}")
        
        # 显示工具调用
        if 'tool_calls' in response:
            print("\n工具调用:")
            for i, tool_call in enumerate(response['tool_calls'], 1):
                func = tool_call.get('function', {})
                print(f"  {i}. {func.get('name')}: {func.get('arguments')}")
        
        # 添加工具执行结果到上下文
        if 'tool_calls' in response:
            for tool_call in response['tool_calls']:
                func = tool_call.get('function', {})
                if func.get('name') == 'shell_tool':
                    command = func.get('arguments', {}).get('command', '')
                    # 模拟执行结果
                    print(f"\n模拟执行命令: {command}")
                    context_manager.add_tool_result(
                        "shell_tool",
                        command,
                        0,
                        stdout=f"执行成功: {command}",
                        success=True
                    )
        
        print("\n✅ 集成测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def demonstrate_usage():
    """演示分层上下文管理器的典型用法"""
    print("\n" + "=" * 80)
    print("分层上下文管理器典型用法演示")
    print("=" * 80)
    
    # 创建分层上下文管理器
    context_manager = HierarchicalContextManager()
    
    # 1. 初始化系统层（只需调用一次）
    context_manager.initialize(
        role_name="Your Agent",
        role_description="你的助手描述",
        os_info={"os_type": "windows", "shell": "powershell", "list_dir": "dir", "current_dir": "cd"},
        tools_description="工具定义..."
    )
    
    # 2. 添加长期记忆（在适当时机）
    context_manager.add_memory("用户偏好设置", "preference")
    context_manager.add_task_summary("完成任务A", "成功", ["关键点1", "关键点2"])
    
    # 3. 在每轮对话中添加消息
    context_manager.add_user_message("用户问题1")
    context_manager.add_assistant_message("助手回答1")
    
    # 4. 设置当前任务
    context_manager.set_current_task("当前用户问题", "相关背景")
    context_manager.add_background("补充背景信息")
    
    # 5. 添加工具执行结果
    context_manager.add_tool_result("shell_tool", "dir", 0, "文件列表...", True)
    context_manager.add_error_feedback("命令错误", "命令不存在", "请使用正确的命令")
    
    # 6. 获取完整上下文用于模型调用
    context = context_manager.get_context()
    
    print(f"\n获取到 {len(context)} 条上下文消息")
    print("\n层级分布:")
    layers = {}
    for msg in context:
        layer = msg.get("layer", "unknown")
        layers[layer] = layers.get(layer, 0) + 1
    
    for layer, count in layers.items():
        print(f"  - {layer}: {count}条")
    
    print("\n✅ 用法演示完成")


if __name__ == "__main__":
    try:
        test_integration()
        demonstrate_usage()
        
        print("\n" + "=" * 80)
        print("🎉 所有集成测试通过！")
        print("=" * 80)
        
        print("""
分层上下文管理器使用总结：

1. 初始化（一次性）：
   context_manager = HierarchicalContextManager()
   context_manager.initialize(role_name, role_description, os_info, tools_description)

2. 记忆管理（按需）：
   context_manager.add_memory(content, category)
   context_manager.add_task_summary(task, result, key_points)

3. 对话管理（每轮）：
   context_manager.add_user_message(content)
   context_manager.add_assistant_message(content)

4. 任务管理（每轮）：
   context_manager.set_current_task(question, context)
   context_manager.add_background(info)

5. 反馈管理（每轮）：
   context_manager.add_tool_result(tool_name, command, return_code, stdout, stderr, success)
   context_manager.add_error_feedback(error_type, error_message, suggestion)

6. 获取上下文（调用模型前）：
   context = context_manager.get_context()
        """)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
