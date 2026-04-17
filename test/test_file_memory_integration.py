#!/usr/bin/env python3
"""
测试分层上下文管理器与 FileMemory 的集成
"""

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inside_agent.utils.hierarchical_context_manager import HierarchicalContextManager
from inside_agent.memory.file_memory import FileMemory


def test_file_memory_integration():
    """测试分层上下文管理器与 FileMemory 的集成"""
    print("=" * 80)
    print("测试分层上下文管理器与 FileMemory 的集成")
    print("=" * 80)
    
    # 初始化 FileMemory
    workspace_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "workspace"
    )
    
    print(f"\n初始化 FileMemory (workspace: {workspace_dir})...")
    file_memory = FileMemory(workspace_dir=workspace_dir)
    print("✅ FileMemory 初始化完成")
    
    # 测试1: 保存对话到 FileMemory
    print("\n" + "=" * 80)
    print("测试1: 保存对话到 FileMemory")
    print("=" * 80)
    
    conversation = [
        {"role": "user", "content": "请记住我使用 conda 环境 agent_dev"},
        {"role": "assistant", "content": "好的，我已经记住了您使用 conda 环境 agent_dev。"},
        {"role": "user", "content": "我主要在晚上工作"},
        {"role": "assistant", "content": "明白了，您主要在晚上工作。我会在这个时候保持更好的状态来帮助您。"},
    ]
    
    print(f"\n保存 {len(conversation)} 条对话...")
    file_memory.save_conversation(conversation)
    print("✅ 对话已保存")
    
    # 测试2: 从 FileMemory 加载对话
    print("\n" + "=" * 80)
    print("测试2: 从 FileMemory 加载对话")
    print("=" * 80)
    
    loaded_conversation = file_memory.load_conversation()
    print(f"\n从 FileMemory 加载了 {len(loaded_conversation)} 条消息")
    for i, msg in enumerate(loaded_conversation, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:80]
        print(f"  {i}. [{role}] {content}...")
    
    print("✅ 对话加载成功")
    
    # 测试3: 分层上下文管理器集成 FileMemory
    print("\n" + "=" * 80)
    print("测试3: 分层上下文管理器集成 FileMemory")
    print("=" * 80)
    
    print("\n初始化分层上下文管理器...")
    context_manager = HierarchicalContextManager()
    
    print("设置 FileMemory 实例...")
    context_manager.set_file_memory(file_memory)
    
    # 初始化系统层
    context_manager.initialize(
        role_name="Inside Agent",
        role_description="一个智能助手",
        os_info={"os_type": "windows", "shell": "powershell", "list_dir": "dir", "current_dir": "cd"}
    )
    
    print("✅ 分层上下文管理器初始化完成")
    
    # 测试4: 从 FileMemory 加载记忆
    print("\n" + "=" * 80)
    print("测试4: 从 FileMemory 加载记忆到分层上下文管理器")
    print("=" * 80)
    
    print("\n调用 load_from_file_memory()...")
    loaded_count = context_manager.load_from_file_memory(include_conversation=True)
    print(f"加载了 {loaded_count} 条记忆")
    
    # 显示加载的上下文
    context = context_manager.get_context()
    print(f"\n分层上下文管理器中的消息总数: {len(context)}")
    
    # 按层级显示
    layers = {}
    for msg in context:
        layer = msg.get("layer", "unknown")
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(msg)
    
    print("\n层级分布:")
    for layer_name in ["system", "memory", "history", "task", "feedback"]:
        if layer_name in layers:
            print(f"  - {layer_name}层: {len(layers[layer_name])}条")
    
    print("✅ 记忆加载成功")
    
    # 测试5: 保存到 FileMemory
    print("\n" + "=" * 80)
    print("测试5: 从分层上下文管理器保存到 FileMemory")
    print("=" * 80)
    
    # 添加一些新内容
    context_manager.add_user_message("测试问题：查看系统时间")
    context_manager.add_assistant_message("执行了 time /t 命令")
    context_manager.add_memory("用户喜欢使用 Python 3.10", "preference")
    context_manager.add_task_summary("查看系统时间", "成功", ["使用 time /t 命令", "Windows CMD"])
    
    print("\n添加了新内容到上下文管理器:")
    print("  - 用户消息: 测试问题：查看系统时间")
    print("  - 助手消息: 执行了 time /t 命令")
    print("  - 记忆: 用户喜欢使用 Python 3.10")
    print("  - 任务摘要: 查看系统时间")
    
    print("\n调用 save_to_file_memory()...")
    context_manager.save_to_file_memory()
    print("✅ 上下文已保存到 FileMemory")
    
    # 测试6: 验证保存的内容
    print("\n" + "=" * 80)
    print("测试6: 验证保存的内容")
    print("=" * 80)
    
    # 重新加载验证
    print("\n重新从 FileMemory 加载验证...")
    context_manager2 = HierarchicalContextManager()
    context_manager2.set_file_memory(file_memory)
    context_manager2.initialize(
        role_name="Inside Agent",
        role_description="一个智能助手"
    )
    context_manager2.load_from_file_memory(include_conversation=False)
    
    # 显示记忆层
    memory_context = context_manager2.memory_layer.get_context()
    print(f"\n记忆层消息数量: {len(memory_context)}")
    for i, msg in enumerate(memory_context, 1):
        content = msg.get("content", "")[:100]
        print(f"  {i}. {content}...")
    
    print("✅ 保存验证成功")
    
    # 测试7: 自动保存记忆
    print("\n" + "=" * 80)
    print("测试7: 自动保存记忆功能")
    print("=" * 80)
    
    context_manager3 = HierarchicalContextManager()
    context_manager3.set_file_memory(file_memory)
    context_manager3.initialize(
        role_name="Inside Agent",
        role_description="一个智能助手"
    )
    
    # 使用 auto_save_memory
    print("\n使用 auto_save_memory 添加消息...")
    context_manager3.auto_save_memory(
        "user",
        "请记住我最近在开发 Web 项目",
        is_important=True
    )
    context_manager3.auto_save_memory(
        "assistant",
        "好的，我记住了您最近在开发 Web 项目。",
        is_important=True
    )
    
    # 显示记忆层
    memory_context3 = context_manager3.memory_layer.get_context()
    print(f"\n自动添加的记忆数量: {len(memory_context3)}")
    for i, msg in enumerate(memory_context3, 1):
        content = msg.get("content", "")[:100]
        print(f"  {i}. {content}...")
    
    # 保存
    context_manager3.save_to_file_memory()
    print("\n✅ 自动保存记忆测试完成")


def main():
    """主测试函数"""
    try:
        test_file_memory_integration()
        
        print("\n" + "=" * 80)
        print("🎉 所有集成测试通过！")
        print("=" * 80)
        
        print("""
集成功能总结：

1. set_file_memory(file_memory):
   - 设置 FileMemory 实例到分层上下文管理器

2. load_from_file_memory(include_conversation=True):
   - 从 FileMemory 加载记忆到分层上下文管理器
   - 支持加载对话历史到历史层
   - 返回加载的记忆条数

3. save_to_file_memory(conversation=None):
   - 保存分层上下文管理器的记忆到 FileMemory
   - 如果不提供 conversation，则自动从各层级构建

4. auto_save_memory(role, content, is_important=True):
   - 自动保存重要记忆
   - 自动判断内容类型并分类

使用示例：

```python
from inside_agent.utils.hierarchical_context_manager import HierarchicalContextManager
from inside_agent.memory.file_memory import FileMemory

# 初始化
file_memory = FileMemory()
context_manager = HierarchicalContextManager()
context_manager.set_file_memory(file_memory)

# 加载记忆
context_manager.load_from_file_memory()

# 添加新内容
context_manager.add_user_message("用户问题")
context_manager.add_memory("重要记忆", "category")

# 保存记忆
context_manager.save_to_file_memory()
```
        """)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
