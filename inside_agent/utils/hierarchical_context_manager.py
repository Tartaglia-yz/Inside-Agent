"""
分层上下文管理器 - Hierarchical Context Manager
实现5层架构的上下文管理机制
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging


class LayerType:
    """层级类型定义"""
    SYSTEM = "system"           # 系统层
    MEMORY = "memory"          # 记忆层
    HISTORY = "history"        # 会话历史层
    TASK = "task"              # 任务层
    FEEDBACK = "feedback"      # 反馈层


class LayerConfig:
    """层级配置"""
    def __init__(self, name: str, max_tokens: int = 10000, priority: int = 0):
        self.name = name
        self.max_tokens = max_tokens
        self.priority = priority
        self.messages: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: Any, metadata: Dict[str, Any] = None):
        """添加消息到层级"""
        message = {
            "role": role,
            "content": content,
            "layer": self.name,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            message["metadata"] = metadata
        self.messages.append(message)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """获取该层级的所有消息"""
        return self.messages.copy()
    
    def clear(self):
        """清空该层级"""
        self.messages = []
    
    def count_tokens(self) -> int:
        """估算token数量（简化实现：每4个字符约1个token）"""
        total = 0
        for msg in self.messages:
            content = str(msg.get("content", ""))
            total += len(content) // 4
        return total


class SystemLayer:
    """第1层：系统层 - 角色定义、工具定义、OS信息"""
    
    def __init__(self):
        self.config = LayerConfig("system", max_tokens=8000, priority=100)
        self.logger = logging.getLogger(__name__)
    
    def set_role_definition(self, role_name: str, role_description: str):
        """设置角色定义"""
        self.config.add_message(
            "system",
            f"你是 {role_name}，{role_description}",
            {"type": "role_definition"}
        )
    
    def set_os_info(self, os_type: str, shell: str, list_dir: str, current_dir: str):
        """设置操作系统信息"""
        os_content = f"""当前操作系统信息：
- OS 类型: {os_type}
- Shell: {shell}
- 列出目录命令: {list_dir}
- 当前目录命令: {current_dir}

**重要：执行系统命令时必须使用适用于当前操作系统的命令格式！**"""
        
        self.config.add_message(
            "system",
            os_content,
            {"type": "os_info"}
        )
    
    def set_tools_definition(self, tools_description: str):
        """设置工具定义"""
        self.config.add_message(
            "system",
            tools_description,
            {"type": "tools_definition"}
        )
    
    def get_context(self) -> List[Dict[str, Any]]:
        """获取系统层上下文"""
        return self.config.get_messages()
    
    def clear(self):
        """清空系统层"""
        self.config.clear()


class MemoryLayer:
    """第2层：记忆层 - 长期记忆、历史任务摘要"""
    
    def __init__(self, max_tokens: int = 6000):
        self.config = LayerConfig("memory", max_tokens=max_tokens, priority=90)
        self.long_term_memory: List[Dict[str, Any]] = []
        self.task_summaries: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def add_long_term_memory(self, content: str, category: str = "general"):
        """添加长期记忆"""
        memory = {
            "role": "system",
            "content": f"[长期记忆 - {category}]\n{content}",
            "layer": "memory",
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        self.long_term_memory.append(memory)
    
    def add_task_summary(self, task: str, result: str, key_points: List[str]):
        """添加任务摘要"""
        summary = f"""[任务摘要]
任务: {task}
结果: {result}
关键要点: {', '.join(key_points)}"""
        
        self.task_summaries.append({
            "role": "system",
            "content": summary,
            "layer": "memory",
            "type": "task_summary",
            "timestamp": datetime.now().isoformat()
        })
    
    def get_context(self) -> List[Dict[str, Any]]:
        """获取记忆层上下文"""
        context = self.long_term_memory.copy()
        
        # 添加任务摘要（最近5条）
        for summary in self.task_summaries[-5:]:
            context.append(summary)
        
        # 估算token并裁剪
        total_tokens = sum(len(str(m.get("content", ""))) // 4 for m in context)
        if total_tokens > self.config.max_tokens:
            context = self._trim_context(context, self.config.max_tokens)
        
        return context
    
    def _trim_context(self, context: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
        """裁剪上下文到指定token数量"""
        trimmed = []
        current_tokens = 0
        
        for msg in reversed(context):
            msg_tokens = len(str(msg.get("content", ""))) // 4
            if current_tokens + msg_tokens <= max_tokens:
                trimmed.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        return trimmed
    
    def clear(self):
        """清空记忆层"""
        self.long_term_memory.clear()
        self.task_summaries.clear()


class HistoryLayer:
    """第3层：会话历史层 - 当前会话的对话记录，带标注区分"""
    
    def __init__(self, max_messages: int = 10, max_tokens: int = 10000):
        self.max_messages = max_messages
        self.config = LayerConfig("history", max_tokens=max_tokens, priority=80)
        self.messages: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def _clean_content(self, content: str) -> str:
        """清理内容中的标注"""
        result = content.replace('[历史对话]\n', '').replace('[当前问题]\n', '')
        return result
    
    def add_message(self, role: str, content: str, is_current_question: bool = False):
        """添加历史消息"""
        # 根据是历史还是当前问题添加不同标注
        if is_current_question:
            annotated_content = f"[当前问题]\n{content}"
        else:
            annotated_content = f"[历史对话]\n{content}"
        
        message = {
            "role": role,
            "content": annotated_content,
            "layer": "history",
            "is_current_question": is_current_question,
            "timestamp": datetime.now().isoformat()
        }
        
        self.messages.append(message)
        
        # 保持消息数量限制
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_context(self) -> List[Dict[str, Any]]:
        """获取历史层上下文"""
        # 确保最后一条用户消息被标记为当前问题
        context = []
        for i, msg in enumerate(self.messages):
            msg_copy = msg.copy()
            
            # 清理已有标注
            clean_content = self._clean_content(msg['content'])
            
            # 如果是最后一条用户消息，强制标记为当前问题
            if i == len(self.messages) - 1 and msg["role"] == "user":
                if not msg.get("is_current_question", False):
                    msg_copy["content"] = f"[当前问题]\n{clean_content}"
            # 其他消息标记为历史对话
            elif msg.get("is_current_question", False):
                msg_copy["content"] = f"[历史对话]\n{clean_content}"
            
            context.append(msg_copy)
        
        return context
    
    def mark_last_as_current_question(self):
        """将最后一条消息标记为当前问题"""
        if self.messages and self.messages[-1]["role"] == "user":
            last_msg = self.messages[-1]
            if not last_msg.get("is_current_question", False):
                clean_content = self._clean_content(last_msg['content'])
                last_msg["content"] = f"[当前问题]\n{clean_content}"
                last_msg["is_current_question"] = True
    
    def clear(self):
        """清空历史层"""
        self.messages.clear()


class TaskLayer:
    """第4层：任务层 - 当前用户问题和相关背景"""
    
    def __init__(self):
        self.current_task: Optional[Dict[str, Any]] = None
        self.background_info: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def set_current_task(self, question: str, context: str = ""):
        """设置当前任务"""
        self.current_task = {
            "role": "user",
            "content": f"[当前任务]\n问题: {question}\n背景: {context if context else '无'}",
            "layer": "task",
            "timestamp": datetime.now().isoformat()
        }
    
    def add_background(self, info: str, source: str = "user"):
        """添加背景信息"""
        background = {
            "role": "system",
            "content": f"[背景信息 - {source}]\n{info}",
            "layer": "task",
            "timestamp": datetime.now().isoformat()
        }
        self.background_info.append(background)
    
    def get_context(self) -> List[Dict[str, Any]]:
        """获取任务层上下文"""
        context = []
        
        # 先添加背景信息
        context.extend(self.background_info)
        
        # 添加当前任务
        if self.current_task:
            context.append(self.current_task)
        
        return context
    
    def clear(self):
        """清空任务层"""
        self.current_task = None
        self.background_info.clear()


class FeedbackLayer:
    """第5层：反馈层 - 工具执行结果、错误信息、执行状态"""
    
    def __init__(self, max_feedbacks: int = 20):
        self.max_feedbacks = max_feedbacks
        self.feedbacks: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def add_tool_result(self, tool_name: str, command: str, return_code: int, 
                       stdout: str = "", stderr: str = "", success: bool = True):
        """添加工具执行结果"""
        status = "成功" if success else "失败"
        content = f"""[工具执行结果 - {tool_name}]
命令: {command}
状态: {status}
返回码: {return_code}"""
        
        if stdout:
            content += f"\n标准输出:\n{stdout}"
        if stderr:
            content += f"\n标准错误:\n{stderr}"
        
        feedback = {
            "role": "system",
            "content": content,
            "layer": "feedback",
            "tool_name": tool_name,
            "command": command,
            "return_code": return_code,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedbacks.append(feedback)
        
        # 保持反馈数量限制
        if len(self.feedbacks) > self.max_feedbacks:
            self.feedbacks = self.feedbacks[-self.max_feedbacks:]
    
    def add_error_feedback(self, error_type: str, error_message: str, 
                          suggestion: str = ""):
        """添加错误反馈"""
        content = f"""[错误反馈 - {error_type}]
错误信息: {error_message}"""
        
        if suggestion:
            content += f"\n建议: {suggestion}"
        
        feedback = {
            "role": "system",
            "content": content,
            "layer": "feedback",
            "type": "error",
            "error_type": error_type,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedbacks.append(feedback)
    
    def add_model_correction(self, original_command: str, corrected_command: str, 
                            reason: str):
        """添加模型自纠正记录"""
        content = f"""[模型自纠正]
原始命令: {original_command}
纠正后: {corrected_command}
原因: {reason}"""
        
        feedback = {
            "role": "system",
            "content": content,
            "layer": "feedback",
            "type": "correction",
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedbacks.append(feedback)
    
    def get_context(self) -> List[Dict[str, Any]]:
        """获取反馈层上下文（只返回最近的结果）"""
        # 只返回最近的5条反馈，避免上下文过长
        return self.feedbacks[-5:] if len(self.feedbacks) > 5 else self.feedbacks.copy()
    
    def clear(self):
        """清空反馈层"""
        self.feedbacks.clear()


class HierarchicalContextManager:
    """
    分层上下文管理器
    
    实现5层架构：
    1. System Layer（系统层）- 角色定义、工具定义、OS信息
    2. Memory Layer（记忆层）- 长期记忆、历史任务摘要
    3. History Layer（会话历史层）- 当前会话对话记录，带标注区分
    4. Task Layer（任务层）- 当前用户问题
    5. Feedback Layer（反馈层）- 工具执行结果、错误信息
    
    支持 FileMemory 集成：
    - load_from_file_memory(): 从 FileMemory 加载记忆
    - save_to_file_memory(): 保存记忆到 FileMemory
    """
    
    def __init__(self, config: Dict[str, Any] = None, file_memory=None):
        self.logger = logging.getLogger(__name__)
        
        # 初始化5个层级
        self.system_layer = SystemLayer()
        self.memory_layer = MemoryLayer()
        self.history_layer = HistoryLayer()
        self.task_layer = TaskLayer()
        self.feedback_layer = FeedbackLayer()
        
        # FileMemory 实例
        self.file_memory = file_memory
        
        # 配置
        self.config = config or {}
        
    def initialize(self, 
                   role_name: str = "Inside Agent",
                   role_description: str = "一个智能助手",
                   os_info: Dict[str, Any] = None,
                   tools_description: str = ""):
        """初始化系统层"""
        self.system_layer.set_role_definition(role_name, role_description)
        
        if os_info:
            self.system_layer.set_os_info(
                os_type=os_info.get("os_type", "unknown"),
                shell=os_info.get("shell", "unknown"),
                list_dir=os_info.get("list_dir", "unknown"),
                current_dir=os_info.get("current_dir", "unknown")
            )
        
        if tools_description:
            self.system_layer.set_tools_definition(tools_description)
        
        self.logger.info("分层上下文管理器初始化完成")
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.history_layer.add_message("user", content, is_current_question=True)
    
    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.history_layer.add_message("assistant", content, is_current_question=False)
    
    def set_current_task(self, question: str, context: str = ""):
        """设置当前任务"""
        self.task_layer.set_current_task(question, context)
    
    def add_tool_result(self, tool_name: str, command: str, return_code: int,
                       stdout: str = "", stderr: str = "", success: bool = True):
        """添加工具执行结果"""
        self.feedback_layer.add_tool_result(
            tool_name, command, return_code, stdout, stderr, success
        )
    
    def add_memory(self, content: str, category: str = "general"):
        """添加长期记忆"""
        self.memory_layer.add_long_term_memory(content, category)
    
    def add_task_summary(self, task: str, result: str, key_points: List[str]):
        """添加任务摘要"""
        self.memory_layer.add_task_summary(task, result, key_points)
    
    def add_background(self, info: str, source: str = "user"):
        """添加背景信息"""
        self.task_layer.add_background(info, source)
    
    def get_context(self) -> List[Dict[str, Any]]:
        """
        获取完整上下文（按层级顺序组合）
        
        返回顺序：
        1. 系统层（最高优先级）
        2. 记忆层
        3. 会话历史层（带标注）
        4. 任务层
        5. 反馈层
        """
        context = []
        
        # 1. 系统层
        context.extend(self.system_layer.get_context())
        
        # 2. 记忆层
        context.extend(self.memory_layer.get_context())
        
        # 3. 会话历史层
        context.extend(self.history_layer.get_context())
        
        # 4. 任务层
        context.extend(self.task_layer.get_context())
        
        # 5. 反馈层
        context.extend(self.feedback_layer.get_context())
        
        self.logger.info(
            f"上下文组成: 系统层={len(self.system_layer.get_context())}条, "
            f"记忆层={len(self.memory_layer.get_context())}条, "
            f"历史层={len(self.history_layer.get_context())}条, "
            f"任务层={len(self.task_layer.get_context())}条, "
            f"反馈层={len(self.feedback_layer.get_context())}条"
        )
        
        return context
    
    def clear_history(self):
        """清空会话历史层"""
        self.history_layer.clear()
    
    def clear_feedback(self):
        """清空反馈层"""
        self.feedback_layer.clear()
    
    def clear_task(self):
        """清空任务层"""
        self.task_layer.clear()
    
    def clear_all(self):
        """清空所有层级"""
        self.system_layer.clear()
        self.memory_layer.clear()
        self.history_layer.clear()
        self.task_layer.clear()
        self.feedback_layer.clear()
        self.logger.info("所有层级已清空")
    
    def set_file_memory(self, file_memory):
        """设置 FileMemory 实例"""
        self.file_memory = file_memory
        self.logger.info(f"FileMemory 已设置: {file_memory}")
    
    def load_from_file_memory(self, include_conversation: bool = True) -> int:
        """
        从 FileMemory 加载记忆到分层上下文管理器
        
        Args:
            include_conversation: 是否同时加载对话历史到历史层
        
        Returns:
            加载的记忆条数
        """
        if not self.file_memory:
            self.logger.warning("FileMemory 未设置，无法加载记忆")
            return 0
        
        loaded_count = 0
        
        try:
            # 加载对话（包括核心记忆和今日记忆）
            conversation = self.file_memory.load_conversation()
            
            for msg in conversation:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if not content:
                    continue
                
                if role == "system":
                    # 系统消息：如果是核心记忆，添加到系统层
                    if "核心记忆" in content or "# Agent 核心记忆" in content:
                        # 提取核心记忆内容（去除标题）
                        core_content = content.replace("# 核心记忆\n", "").strip()
                        self.system_layer.set_role_definition(
                            "Inside Agent",
                            f"核心记忆：\n{core_content}"
                        )
                        loaded_count += 1
                    else:
                        # 其他系统消息添加到系统层
                        self.system_layer.config.add_message(role, content, {"source": "file_memory"})
                        loaded_count += 1
                        
                elif role == "user":
                    # 用户消息：添加到历史层
                    if include_conversation:
                        self.history_layer.add_message(role, content, is_current_question=False)
                        loaded_count += 1
                        
                elif role == "assistant":
                    # 助手消息：添加到历史层
                    if include_conversation:
                        self.history_layer.add_message(role, content, is_current_question=False)
                        loaded_count += 1
            
            self.logger.info(f"从 FileMemory 加载了 {loaded_count} 条记忆")
            
        except Exception as e:
            self.logger.error(f"从 FileMemory 加载记忆失败: {e}")
        
        return loaded_count
    
    def save_to_file_memory(self, conversation: List[Dict[str, Any]] = None):
        """
        保存当前对话/记忆到 FileMemory
        
        Args:
            conversation: 可选的对话列表，如果为 None，则使用历史层和任务层的消息
        """
        if not self.file_memory:
            self.logger.warning("FileMemory 未设置，无法保存记忆")
            return
        
        try:
            if conversation is None:
                # 从当前层级构建对话
                conversation = []
                
                # 添加记忆层的内容
                for memory in self.memory_layer.long_term_memory:
                    conversation.append({
                        "role": "system",
                        "content": memory.get("content", "")
                    })
                
                # 添加任务摘要
                for summary in self.memory_layer.task_summaries:
                    conversation.append({
                        "role": "system",
                        "content": summary.get("content", "")
                    })
                
                # 添加历史层的内容
                for msg in self.history_layer.messages:
                    conversation.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "").replace("[历史对话]\n", "").replace("[当前问题]\n", "")
                    })
                
                # 添加任务层的内容
                if self.task_layer.current_task:
                    conversation.append({
                        "role": "user",
                        "content": self.task_layer.current_task.get("content", "").replace("[当前任务]\n", "")
                    })
            
            # 保存到 FileMemory
            self.file_memory.save_conversation(conversation)
            self.logger.info(f"已保存 {len(conversation)} 条消息到 FileMemory")
            
        except Exception as e:
            self.logger.error(f"保存记忆到 FileMemory 失败: {e}")
    
    def auto_save_memory(self, role: str, content: str, is_important: bool = True):
        """
        自动保存重要记忆到分层上下文管理器
        
        适用于在对话过程中自动捕获重要信息
        
        Args:
            role: 消息角色（user/assistant）
            content: 消息内容
            is_important: 是否重要（会被添加到记忆层）
        """
        # 添加到历史层
        self.history_layer.add_message(role, content, is_current_question=False)
        
        if is_important:
            # 判断内容类型并添加到相应层级
            if self._is_task_related(content):
                # 任务相关信息添加到任务摘要
                self.add_task_summary(
                    task=content[:100],
                    result="进行中",
                    key_points=[]
                )
            else:
                # 其他重要信息添加到长期记忆
                category = self._detect_memory_category(content)
                self.add_memory(content, category)
    
    def _is_task_related(self, content: str) -> bool:
        """判断内容是否与任务相关"""
        task_keywords = ["完成", "任务", "执行", "解决", "创建", "修改", "删除", 
                        "完成", "成功", "失败", "错误"]
        content_lower = content.lower()
        return any(keyword in content for keyword in task_keywords)
    
    def _detect_memory_category(self, content: str) -> str:
        """检测记忆类别"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["偏好", "喜欢", "习惯", " preference", "like", "prefer"]):
            return "preference"
        elif any(word in content_lower for word in ["项目", "代码", "技术", "project", "code", "tech"]):
            return "project"
        elif any(word in content_lower for word in ["环境", "配置", "setup", "config", "environment"]):
            return "environment"
        else:
            return "general"
