from typing import List, Dict, Any
import logging
import re

class SmartContextManager:
    """智能上下文管理器，支持基于token数量的管理和对话摘要"""
    
    def __init__(self, max_tokens: int = 200000, token_ratio: float = 0.7):
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_tokens = max_tokens
        self.token_ratio = token_ratio  # 保留的token比例
        self.logger = logging.getLogger(__name__)
    
    def add_message(self, role: str, content: Any):
        """添加消息到对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        
        # 检查是否需要清理上下文
        self._manage_context()
    
    def get_context(self) -> List[Dict[str, Any]]:
        """获取当前上下文，只保留最近的相关消息，并添加消息类型标注"""
        # 保留系统消息
        system_messages = [msg for msg in self.conversation_history if msg["role"] == "system"]
        
        # 只保留最近的几条消息（最近的5条非系统消息）
        recent_messages = []
        message_count = 0
        
        # 从最近的消息开始往前找
        for msg in reversed(self.conversation_history):
            if msg["role"] != "system":
                recent_messages.insert(0, msg)
                message_count += 1
                # 只保留最近的5条非系统消息
                if message_count >= 5:
                    break
        
        # 对所有消息添加标注，明确区分历史对话和当前问题
        annotated_messages = []
        for i, msg in enumerate(recent_messages):
            if len(recent_messages) == 1:
                # 只有一条消息，标记为当前问题
                if msg["role"] == "user":
                    annotated_content = f"[当前问题]\n{msg['content']}"
                else:
                    annotated_content = f"[历史对话]\n{msg['content']}"
            else:
                # 多条消息，最后一条用户消息标记为当前问题，其他标记为历史对话
                if i == len(recent_messages) - 1 and msg["role"] == "user":
                    annotated_content = f"[当前问题]\n{msg['content']}"
                else:
                    annotated_content = f"[历史对话]\n{msg['content']}"
            
            annotated_messages.append({
                "role": msg["role"],
                "content": annotated_content
            })
        
        # 组合系统消息和标注后的消息
        context = system_messages + annotated_messages
        self.logger.info(f"返回上下文: {len(system_messages)} 条系统消息, {len(annotated_messages)} 条最近消息")
        return context
    
    def get_full_history(self) -> List[Dict[str, Any]]:
        """获取完整的对话历史"""
        return self.conversation_history.copy()
    
    def _manage_context(self):
        """管理上下文，确保不超过token限制"""
        # 计算当前token数量
        current_tokens = self._count_tokens()
        
        # 如果超过限制，进行清理
        if current_tokens > self.max_tokens:
            self.logger.info(f"对话历史过长（{current_tokens} tokens），开始清理")
            
            # 计算需要保留的token数量
            target_tokens = int(self.max_tokens * self.token_ratio)
            
            # 保留系统消息
            system_messages = [msg for msg in self.conversation_history if msg["role"] == "system"]
            system_tokens = self._count_tokens(system_messages)
            
            # 计算剩余可分配的token数量
            remaining_tokens = target_tokens - system_tokens
            
            if remaining_tokens <= 0:
                # 如果系统消息就占满了，只保留系统消息
                self.conversation_history = system_messages
                self.logger.warning("系统消息占用了所有token空间")
                return
            
            # 从最近的消息开始保留，直到达到token限制
            recent_messages = []
            recent_tokens = 0
            
            for msg in reversed(self.conversation_history):
                if msg["role"] == "system":
                    continue
                
                msg_tokens = self._count_tokens([msg])
                if recent_tokens + msg_tokens <= remaining_tokens:
                    recent_messages.insert(0, msg)
                    recent_tokens += msg_tokens
                else:
                    # 对最后一条消息进行摘要
                    if recent_tokens < remaining_tokens:
                        summarized_msg = self._summarize_message(msg, remaining_tokens - recent_tokens)
                        if summarized_msg:
                            recent_messages.insert(0, summarized_msg)
                    break
            
            # 重新构建对话历史
            self.conversation_history = system_messages + recent_messages
            self.logger.info(f"清理后对话历史长度：{len(self.conversation_history)} 条消息")
    
    def _count_tokens(self, messages: List[Dict[str, Any]] = None) -> int:
        """计算token数量（简化实现）"""
        if messages is None:
            messages = self.conversation_history
        
        total_tokens = 0
        for msg in messages:
            content = str(msg.get("content", ""))
            # 简单估算：每个字符算0.25个token
            total_tokens += len(content) // 4
        return total_tokens
    
    def _summarize_message(self, message: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """对消息进行摘要"""
        content = str(message.get("content", ""))
        
        # 简单实现：截断内容
        max_chars = max_tokens * 4
        if len(content) <= max_chars:
            return message
        
        # 截断并添加摘要标记
        summarized_content = content[:max_chars] + "... [摘要]"
        
        return {
            "role": message["role"],
            "content": summarized_content
        }
    
    def clear(self):
        """清空对话历史"""
        self.conversation_history = []
