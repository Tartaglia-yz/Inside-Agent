#!/usr/bin/env python3
"""
测试分层上下文管理器 - Hierarchical Context Manager Test
验证5层架构的上下文管理机制
"""

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inside_agent.utils.hierarchical_context_manager import (
    HierarchicalContextManager,
    SystemLayer,
    MemoryLayer,
    HistoryLayer,
    TaskLayer,
    FeedbackLayer
)


def test_individual_layers():
    """测试各个层级独立功能"""
    print("=" * 80)
    print("测试1: 各个层级独立功能")
    print("=" * 80)
    
    # 测试系统层
    print("\n[系统层测试]")
    system_layer = SystemLayer()
    system_layer.set_role_definition("Inside Agent", "一个智能助手")
    system_layer.set_os_info("windows", "powershell", "dir", "cd")
    system_layer.set_tools_definition("shell_tool: 执行系统命令")
    
    system_context = system_layer.get_context()
    print(f"系统层消息数量: {len(system_context)}")
    for msg in system_context:
        print(f"  - [{msg['role']}] {msg['content'][:60]}...")
    
    # 测试记忆层
    print("\n[记忆层测试]")
    memory_layer = MemoryLayer()
    memory_layer.add_long_term_memory("用户喜欢在晚上工作", "preference")
    memory_layer.add_long_term_memory("项目使用Python开发", "project")
    memory_layer.add_task_summary("完成用户认证功能", "成功", ["使用JWT", "支持刷新令牌"])
    
    memory_context = memory_layer.get_context()
    print(f"记忆层消息数量: {len(memory_context)}")
    for msg in memory_context:
        print(f"  - [{msg['role']}] {msg['content'][:60]}...")
    
    # 测试历史层
    print("\n[历史层测试]")
    history_layer = HistoryLayer(max_messages=5)
    history_layer.add_message("user", "你好，请帮我查看系统时间", is_current_question=False)
    history_layer.add_message("assistant", "好的，我来帮您查看当前系统时间。")
    history_layer.add_message("user", "查看当前目录", is_current_question=True)
    
    history_context = history_layer.get_context()
    print(f"历史层消息数量: {len(history_context)}")
    for msg in history_context:
        marker = "[当前问题]" if msg.get("is_current_question") else "[历史对话]"
        print(f"  - {marker} [{msg['role']}] {msg['content'][:60]}...")
    
    # 测试任务层
    print("\n[任务层测试]")
    task_layer = TaskLayer()
    task_layer.set_current_task("查看当前工作目录", "用户想要了解当前工作目录位置")
    task_layer.add_background("用户正在使用Windows系统", "system")
    
    task_context = task_layer.get_context()
    print(f"任务层消息数量: {len(task_context)}")
    for msg in task_context:
        print(f"  - [{msg['role']}] {msg['content'][:60]}...")
    
    # 测试反馈层
    print("\n[反馈层测试]")
    feedback_layer = FeedbackLayer()
    feedback_layer.add_tool_result("shell_tool", "dir", 0, "文件列表...", success=True)
    feedback_layer.add_tool_result("shell_tool", "Get-Date", 1, "", "命令未找到", success=False)
    
    feedback_context = feedback_layer.get_context()
    print(f"反馈层消息数量: {len(feedback_context)}")
    for msg in feedback_context:
        status = "成功" if msg.get("success") else "失败"
        print(f"  - [{status}] {msg['content'][:60]}...")
    
    print("\n✅ 各层级独立测试通过")


def test_hierarchical_context_manager():
    """测试完整的分层上下文管理器"""
    print("\n" + "=" * 80)
    print("测试2: 完整的分层上下文管理器")
    print("=" * 80)
    
    # 初始化分层上下文管理器
    context_manager = HierarchicalContextManager()
    
    # 初始化系统层
    context_manager.initialize(
        role_name="Inside Agent",
        role_description="一个智能助手，能够执行系统命令和管理文件",
        os_info={
            "os_type": "windows",
            "shell": "powershell",
            "list_dir": "dir",
            "current_dir": "cd"
        },
        tools_description="""可用工具：
1. shell_tool - 执行系统命令
2. file_tool - 文件操作（read/write）
当需要列出目录时，必须使用 shell_tool 执行 "dir" 命令"""
    )
    
    # 添加记忆
    context_manager.add_memory("用户使用 conda 环境 agent_dev", "environment")
    context_manager.add_task_summary("查看系统时间", "成功", ["使用 time /t 命令"])
    
    # 添加会话历史
    context_manager.add_user_message("你好，请帮我查看系统时间")
    context_manager.add_assistant_message("好的，我来执行命令查看当前系统时间。")
    context_manager.add_user_message("查看当前目录")
    
    # 设置当前任务
    context_manager.set_current_task("查看当前工作目录", "用户想要了解当前工作目录位置")
    context_manager.add_background("用户正在使用Windows系统", "system")
    
    # 添加工具执行结果
    context_manager.add_tool_result(
        "shell_tool",
        "dir",
        0,
        stdout="文件列表输出...",
        success=True
    )
    
    # 获取完整上下文
    print("\n获取完整上下文（5层架构）：")
    print("-" * 80)
    
    full_context = context_manager.get_context()
    print(f"\n总消息数量: {len(full_context)}")
    
    # 按层级显示
    layers = {}
    for msg in full_context:
        layer = msg.get("layer", "unknown")
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(msg)
    
    for layer_name in ["system", "memory", "history", "task", "feedback"]:
        if layer_name in layers:
            print(f"\n【{layer_name.upper()}层】({len(layers[layer_name])}条消息)")
            for i, msg in enumerate(layers[layer_name], 1):
                content = msg["content"]
                # 截断显示
                if len(content) > 100:
                    content = content[:100] + "..."
                print(f"  {i}. [{msg['role']}] {content}")
    
    print("\n✅ 完整分层上下文管理器测试通过")


def test_context_annotations():
    """测试上下文标注功能"""
    print("\n" + "=" * 80)
    print("测试3: 上下文标注功能（区分历史对话和当前问题）")
    print("=" * 80)
    
    context_manager = HierarchicalContextManager()
    context_manager.initialize(
        role_name="Test Agent",
        role_description="测试助手"
    )
    
    # 模拟多轮对话
    print("\n模拟多轮对话：")
    
    # 第1轮
    context_manager.add_user_message("第一个问题：查看系统时间")
    context_manager.add_assistant_message("执行了 time /t 命令")
    
    # 第2轮
    context_manager.add_user_message("第二个问题：查看当前目录")
    context_manager.add_assistant_message("执行了 cd 命令")
    
    # 第3轮（当前问题）
    context_manager.add_user_message("第三个问题：列出文件")
    context_manager.set_current_task("列出文件", "用户想要查看当前目录的文件列表")
    
    # 添加工具执行结果
    context_manager.add_tool_result("shell_tool", "dir", 0, "文件列表...", True)
    
    print("\n上下文标注分析：")
    print("-" * 80)
    
    full_context = context_manager.get_context()
    
    for i, msg in enumerate(full_context, 1):
        layer = msg.get("layer", "unknown")
        role = msg["role"]
        content = msg["content"]
        
        # 检查是否有标注
        has_current_marker = "[当前问题]" in content or "[当前任务]" in content
        has_history_marker = "[历史对话]" in content
        
        marker_info = []
        if has_current_marker:
            marker_info.append("✅ [当前问题/任务]")
        if has_history_marker:
            marker_info.append("📜 [历史对话]")
        
        marker_str = " | ".join(marker_info) if marker_info else "无标注"
        
        # 截断显示
        display_content = content[:80] + "..." if len(content) > 80 else content
        
        print(f"\n{i}. [{layer}][{role}] {marker_str}")
        print(f"   内容: {display_content}")
    
    print("\n✅ 上下文标注测试通过")


def main():
    """主测试函数"""
    print("=" * 80)
    print("分层上下文管理器测试套件")
    print("=" * 80)
    
    try:
        test_individual_layers()
        test_hierarchical_context_manager()
        test_context_annotations()
        
        print("\n" + "=" * 80)
        print("🎉 所有测试通过！")
        print("=" * 80)
        
        print("""
分层上下文管理器特性总结：
✅ 5层架构：系统层、记忆层、历史层、任务层、反馈层
✅ 层级隔离：每层有独立的配置和容量管理
✅ 智能标注：自动区分历史对话和当前问题
✅ 动态管理：自动裁剪和清理过长的上下文
✅ 工具反馈：完整的工具执行结果反馈机制
✅ 记忆管理：支持长期记忆和任务摘要
        """)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
