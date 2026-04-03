import argparse
import os
import sys
import json
import datetime
import threading
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from .agent import Agent
from .models.minimax import MiniMaxModel
from .models.interleaved_thinking import InterleavedThinkingModel
from .tools.file_tool import FileTool
from .tools.shell_tool import ShellTool
from .memory.file_memory import FileMemory
from .utils.smart_context_manager import SmartContextManager
from .utils.logging_config import LoggingConfig

load_dotenv()

SPINNER_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
spinner_running = False
spinner_thread = None

def spinner_animation(stop_event, prefix=""):
    idx = 0
    prefix_plain = "Agent: "
    while not stop_event.is_set() and spinner_running:
        char = SPINNER_CHARS[idx % len(SPINNER_CHARS)]
        spinner_text = f"{prefix_plain}{char} "
        sys.stdout.write(f"\r{spinner_text}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * len(spinner_text) + "\r")
    sys.stdout.flush()

def start_spinner(prefix=""):
    global spinner_running, spinner_thread
    spinner_running = True
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner_animation, args=(stop_event, prefix))
    spinner_thread.daemon = True
    spinner_thread.start()
    return stop_event

def stop_spinner(stop_event):
    global spinner_running
    spinner_running = False
    if stop_event:
        stop_event.set()
    if spinner_thread:
        spinner_thread.join(timeout=0.3)

console = Console()

def load_config():
    config_file = "agent.json"
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # 默认配置
        return {
            "model": {
                "model_name": "MiniMax-M2.7",
                "base_url": "https://api.minimax.chat/v1/text/chatcompletion",
                "anthropic_base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic"),
                "temperature": 0.7,
                "max_tokens": 10240
            },
            "agent": {
                "name": "Inside Agent",
                "max_context_tokens": 200000,
                "token_ratio": 0.7
            },
            "memory": {
                "workspace_dir": "workspace"
            },
            "logging": {
                "log_level": "INFO"
            }
        }

# 初始化控制台
console = Console()

def check_and_create_dirs():
    """检查并创建必要的目录"""
    # 创建logs目录
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        console.print(f"[green]创建了logs目录: {logs_dir}[/green]")
    
    # 创建workspace/memory目录
    memory_dir = os.path.join("workspace", "memory")
    if not os.path.exists(memory_dir):
        os.makedirs(memory_dir, exist_ok=True)
        console.print(f"[green]创建了memory目录: {memory_dir}[/green]")

def clean_old_logs():
    """清理超过三天的日志文件"""
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        return
    
    # 获取当前日期
    current_date = datetime.datetime.now()
    
    # 遍历logs目录中的文件
    for filename in os.listdir(logs_dir):
        file_path = os.path.join(logs_dir, filename)
        
        # 检查是否是文件
        if os.path.isfile(file_path):
            # 获取文件的修改时间
            file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # 计算文件年龄（天数）
            age_days = (current_date - file_mtime).days
            
            # 删除超过三天的日志文件
            if age_days > 3:
                os.remove(file_path)
                console.print(f"[yellow]删除了过期的日志文件: {filename}[/yellow]")

def main():
    """命令行入口"""
    # 检查并创建必要的目录
    check_and_create_dirs()
    
    # 清理过期的日志文件
    clean_old_logs()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Inside Agent - A minimal Agent using MiniMax M2.7 model")
    parser.add_argument("--api-key", help="MiniMax API密钥")
    parser.add_argument("--model", help="模型名称")
    parser.add_argument("--max-tokens", type=int, help="最大上下文token数")
    parser.add_argument("--log-level", help="日志级别")
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 命令行参数优先级高于环境变量
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    model_name = args.model or config["model"]["model_name"]
    base_url = os.getenv("ANTHROPIC_BASE_URL") or config["model"].get("anthropic_base_url", config["model"]["base_url"])
    max_tokens = args.max_tokens or config["agent"]["max_context_tokens"]
    log_level = args.log_level or config["logging"]["log_level"]
    
    # 设置日志
    LoggingConfig.setup_logging(log_level)
    
    # 检查API密钥
    if not api_key:
        console.print(Panel("错误: 未提供MiniMax API密钥", style="red"))
        sys.exit(1)
    
    # 初始化组件
    try:
        # 初始化工具
        tools = [
            FileTool(),
            ShellTool()
        ]

        # 初始化模型
        base_model = MiniMaxModel(
            api_key=api_key, 
            model=model_name,
            base_url=base_url,
            temperature=config["model"]["temperature"],
            max_tokens=config["model"]["max_tokens"]
        )
        model = InterleavedThinkingModel(base_model=base_model, tools=tools)
        
        # 初始化记忆
        memory = FileMemory(workspace_dir=config["memory"]["workspace_dir"])
        
        # 初始化上下文管理器
        context_manager = SmartContextManager(max_tokens=max_tokens)
        
        # 加载历史对话
        history = memory.load_conversation()
        for message in history:
            context_manager.add_message(message["role"], message["content"])
        
        # 初始化Agent
        agent = Agent(
            model=model,
            tools=tools,
            memory=memory,
            context_manager=context_manager,
            name=config["agent"]["name"]
        )
        
        # 显示欢迎信息
        console.print(Panel(
            Text("欢迎使用 Inside Agent!\n基于 MiniMax M2.7 模型构建\n支持交错思维和工具调用", justify="center"),
            title="Inside Agent",
            border_style="green"
        ))
        
        # 显示引导信息
        console.print(Panel(
            Text("首次使用引导:\n\n" +
                 "【基本信息】\n" +
                 "我是 Inside Agent，基于 MiniMax M2.7 模型构建的智能助手\n" +
                 "我的核心记忆存储在 workspace/core-memory.md 文件中\n" +
                 "日常对话历史会保存在 workspace/memory/ 目录下\n\n" +
                 "【主要功能】\n" +
                 "1. 智能对话: 使用交错思维处理复杂问题\n" +
                 "2. 文件操作: 读写文件、列出目录内容\n" +
                 "3. Shell命令: 执行系统命令获取信息\n" +
                 "4. 记忆管理: 持久化存储对话历史\n" +
                 "5. 上下文理解: 智能处理长对话\n\n" +
                 "【我能帮助您】\n" +
                 "- 管理和编辑文件\n" +
                 "- 执行系统操作\n" +
                 "- 回答各种问题\n" +
                 "- 提供技术支持\n" +
                 "- 辅助开发工作\n\n" +
                 "【创建用户】\n" +
                 "- 您可以直接告诉我的名字和需求，我会自动识别并记住您\n" +
                 "- 例如: '你好，我是张三，我需要帮助管理文件'\n\n" +
                 "【可用命令】\n" +
                 "- /exit;/quit;/q: 退出Agent\n" +
                 "- /clear;/c: 清空对话历史\n\n" +
                 "下面开始提问吧！", justify="left"),
            title="使用指南",
            border_style="blue"
        ))
        
        # 主循环
        while True:
            try:
                # 获取用户输入
                user_input = console.input("\n[bold cyan]用户:[/bold cyan] ")
                
                # 处理退出命令 - 只识别带/前缀的命令
                if user_input.lower() in ["/exit", "/quit", "/q"]:
                    console.print(Panel("再见!", style="yellow"))
                    break
                
                # 处理清空命令 - 只识别带/前缀的命令
                if user_input.lower() in ["/clear", "/c"]:
                    context_manager.clear()
                    memory.clear()
                    console.print(Panel("对话历史已清空", style="yellow"))
                    continue
                
                # 执行Agent
                stop_event = start_spinner("Agent: ")
                try:
                    response = agent.run_stream(user_input)
                finally:
                    stop_spinner(stop_event)
                console.print(f"[bold blue]Agent:[/bold blue] {response}", markup=False)
                
            except KeyboardInterrupt:
                stop_spinner(None)
                console.print("\n[yellow]操作已取消[/yellow]")
                continue
            except Exception as e:
                stop_spinner(None)
                console.print(f"[red]错误: {str(e)}[/red]")
                continue
                
    except Exception as e:
        console.print(f"[red]初始化失败: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
