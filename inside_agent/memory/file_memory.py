import os
from datetime import datetime
from typing import List, Dict, Any
from .base import BaseMemory
import logging

class FileMemory(BaseMemory):
    """基于文件的持久化记忆实现"""
    
    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace_dir = workspace_dir
        self.memory_dir = os.path.join(workspace_dir, "memory")
        self.core_memory_file = os.path.join(workspace_dir, "core-memory.md")
        # 初始化logger
        self.logger = logging.getLogger(__name__)
        # 确保目录结构存在
        os.makedirs(self.memory_dir, exist_ok=True)
        # 初始化核心记忆文件
        self._init_core_memory()
    
    def _init_core_memory(self):
        """初始化核心记忆文件"""
        if not os.path.exists(self.core_memory_file):
            core_content = """# Agent 核心记忆

## 身份
我是 Inside Agent，一个基于 MiniMax M2.7 模型构建的智能助手。

## 职责
1. 帮助用户完成各种任务
2. 提供准确的信息和建议
3. 执行文件操作和系统命令
4. 保持对话历史的持久化
5. 不断学习和改进

## 能力
- 文件系统操作：读写文件、列出目录
- Shell 命令执行：运行系统命令
- 上下文管理：智能处理长对话
- 记忆管理：保存和加载对话历史

## 工作方式
- 我会使用交错思维来处理复杂问题
- 我会根据需要调用工具来完成任务
- 我会保存对话历史以便后续参考
- 我会在每次启动时加载核心记忆和当天的对话历史
"""
            with open(self.core_memory_file, "w", encoding="utf-8") as f:
                f.write(core_content)
            self.logger.info(f"核心记忆文件已创建: {self.core_memory_file}")
    
    def save_conversation(self, conversation: List[Dict[str, Any]]):
        """保存对话"""
        try:
            # 过滤对话内容，只保存重要信息
            filtered_conversation = self._filter_conversation(conversation)
            
            # 如果没有重要内容，不保存
            if not filtered_conversation:
                return
            
            # 生成当前日期的文件名
            date_str = datetime.now().strftime("%Y-%m-%d")
            memory_file = os.path.join(self.memory_dir, f"{date_str}-memory.md")
            
            # 将对话转换为Markdown格式
            markdown_content = self._convert_to_markdown(filtered_conversation)
            
            with open(memory_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            self.logger.info(f"对话已保存到 {memory_file}")
        except Exception as e:
            self.logger.error(f"保存对话出错: {str(e)}")
    
    def _filter_conversation(self, conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤对话内容，只保留重要信息"""
        filtered = []
        
        for message in conversation:
            role = message["role"]
            content = message["content"]
            
            # 跳过系统消息（核心记忆已经包含）
            if role == "system":
                continue
            
            # 跳过错误信息
            if "错误" in content or "error" in content.lower():
                continue
            
            # 跳过工具消息（通常是执行结果，不是重要信息）
            if role == "tool":
                continue
            
            # 检查是否是重要信息
            if self._is_important_message(role, content):
                filtered.append(message)
        
        return filtered
    
    def _is_important_message(self, role: str, content: str) -> bool:
        """判断消息是否重要"""
        # 重要关键词
        important_keywords = [
            "记录", "保存", "记住", "重要", "需要记住", "不要忘",
            "note", "remember", "save", "important", "don't forget"
        ]
        
        # 检查是否包含重要关键词
        content_lower = content.lower()
        for keyword in important_keywords:
            if keyword in content_lower:
                return True
        
        # 检查是否是用户的第一条消息（通常是介绍自己）
        if role == "user" and len(content) > 10:
            return True
        
        # 检查是否是Agent的重要回复
        if role == "assistant" and len(content) > 50:
            return True
        
        return False
    
    def load_conversation(self) -> List[Dict[str, Any]]:
        """加载对话"""
        conversation = []
        try:
            # 首先加载核心记忆
            if os.path.exists(self.core_memory_file):
                with open(self.core_memory_file, "r", encoding="utf-8") as f:
                    core_content = f.read()
                # 将核心记忆添加到对话历史
                conversation.append({
                    "role": "system",
                    "content": f"# 核心记忆\n{core_content}"
                })
                self.logger.info(f"已加载核心记忆: {self.core_memory_file}")
            
            # 然后加载今天的记忆文件
            date_str = datetime.now().strftime("%Y-%m-%d")
            memory_file = os.path.join(self.memory_dir, f"{date_str}-memory.md")
            
            if os.path.exists(memory_file):
                with open(memory_file, "r", encoding="utf-8") as f:
                    content = f.read()
                # 将Markdown转换回对话格式
                daily_conversation = self._convert_from_markdown(content)
                conversation.extend(daily_conversation)
                self.logger.info(f"从 {memory_file} 加载对话")
            else:
                self.logger.info(f"今天的记忆文件不存在: {memory_file}")
            
            return conversation
        except Exception as e:
            self.logger.error(f"加载对话出错: {str(e)}")
            return []
    
    def clear(self):
        """清空记忆"""
        try:
            # 清空今天的记忆文件
            date_str = datetime.now().strftime("%Y-%m-%d")
            memory_file = os.path.join(self.memory_dir, f"{date_str}-memory.md")
            
            if os.path.exists(memory_file):
                os.remove(memory_file)
                self.logger.info(f"记忆已清空: {memory_file}")
            else:
                self.logger.info("今天的记忆文件不存在，无需清空")
        except Exception as e:
            self.logger.error(f"清空记忆出错: {str(e)}")
    
    def _convert_to_markdown(self, conversation: List[Dict[str, Any]]) -> str:
        """将对话转换为Markdown格式"""
        markdown = f"# 对话记录 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for message in conversation:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                markdown += f"## 用户\n{content}\n\n"
            elif role == "assistant":
                markdown += f"## Agent\n{content}\n\n"
            elif role == "tool":
                markdown += f"## 工具\n{content}\n\n"
            elif role == "system":
                markdown += f"## 系统\n{content}\n\n"
        
        return markdown
    
    def _convert_from_markdown(self, content: str) -> List[Dict[str, Any]]:
        """将Markdown转换回对话格式"""
        conversation = []
        lines = content.strip().split("\n")
        
        current_role = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("## "):
                # 保存上一条消息
                if current_role and current_content:
                    conversation.append({
                        "role": current_role,
                        "content": "\n".join(current_content).strip()
                    })
                # 开始新消息
                role_str = line[3:].strip()
                if role_str == "用户":
                    current_role = "user"
                elif role_str == "Agent":
                    current_role = "assistant"
                elif role_str == "工具":
                    current_role = "tool"
                elif role_str == "系统":
                    current_role = "system"
                else:
                    current_role = None
                current_content = []
            elif current_role and line:
                current_content.append(line)
        
        # 保存最后一条消息
        if current_role and current_content:
            conversation.append({
                "role": current_role,
                "content": "\n".join(current_content).strip()
            })
        
        return conversation
