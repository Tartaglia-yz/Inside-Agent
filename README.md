# Inside Agent

基于 MiniMax M2.7 模型构建的智能助手，支持交错思维和工具调用。

## 项目简介

Inside Agent 是一个基于 MiniMax M2.7 模型的智能助手，具有以下功能：
- 智能对话：使用交错思维处理复杂问题
- 文件操作：读写文件、列出目录内容
- Shell命令：执行系统命令获取信息
- 记忆管理：持久化存储对话历史
- 上下文理解：智能处理长对话

## 安装步骤

1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd Inside-Agent
   ```

2. **创建虚拟环境**
   ```bash
   python3 -m venv venv
   ```

3. **激活虚拟环境**
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

## 初次配置

### 1. 配置环境变量文件 (.env)

创建 `.env` 文件，配置以下内容：

```env
# MiniMax API Configuration
ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
ANTHROPIC_API_KEY=your_minimax_api_key
```

- `ANTHROPIC_BASE_URL`：MiniMax 的 Anthropic 兼容 API 端点
- `ANTHROPIC_API_KEY`：MiniMax API 密钥，可从 MiniMax 平台获取

### 2. 配置模型参数文件 (agent.json)

创建或编辑 `agent.json` 文件，配置以下内容：

```json
{
  "model": {
    "model_name": "MiniMax-M2.7",
    "base_url": "https://api.minimax.chat/v1/text/chatcompletion",
    "anthropic_base_url": "https://api.minimax.chat/v1/text/anthropic-compatible",
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
```

- `model_name`：模型名称，使用 "MiniMax-M2.7"
- `anthropic_base_url`：Anthropic 兼容 API 端点
- `max_context_tokens`：全局最大上下文 tokens，推荐设置为 200000

## 运行 Agent

```bash
python3 -m inside_agent.cli
```

## 可用命令

- `/exit`、`/quit`、`/q`：退出 Agent
- `/clear`、`/c`：清空对话历史

## 项目结构

```
Inside-Agent/
├── inside_agent/         # 核心代码
│   ├── agent.py          # 核心 Agent 类
│   ├── models/           # 模型实现
│   │   ├── base.py       # 基础模型类
│   │   ├── minimax.py    # MiniMax 模型实现
│   │   └── interleaved_thinking.py  # 交错思维模型包装器
│   ├── tools/            # 工具实现
│   │   ├── base.py       # 基础工具类
│   │   ├── file_tool.py  # 文件操作工具
│   │   └── shell_tool.py # Shell 命令工具
│   ├── memory/           # 记忆管理
│   │   ├── base.py       # 基础记忆类
│   │   └── file_memory.py # 文件记忆实现
│   ├── utils/            # 工具类
│   │   ├── context_manager.py        # 上下文管理器
│   │   ├── smart_context_manager.py  # 智能上下文管理器
│   │   └── logging_config.py         # 日志配置
│   └── cli.py            # 命令行接口
├── workspace/            # 工作目录
│   ├── core-memory.md    # 核心记忆文件
│   └── memory/           # 对话历史目录
├── agent.json            # 配置文件
├── .env                  # 环境变量文件
├── requirements.txt      # 依赖文件
└── README.md             # 项目说明
```

## 注意事项

1. **API 密钥安全**：不要将 API 密钥提交到版本控制系统
2. **内存管理**：对话历史会保存在 `workspace/memory/` 目录下，定期清理不需要的历史记录
3. **性能优化**：对于复杂任务，建议使用较小的上下文窗口以提高响应速度
4. **错误处理**：如果遇到 API 调用错误，请检查网络连接和 API 密钥是否正确

## 常见问题

### Q: 为什么模型调用失败？
A: 可能的原因包括：
- API 密钥错误或过期
- 网络连接问题
- API 端点配置错误
- 模型权限不足

### Q: 如何清空对话历史？
A: 在对话中输入 `/clear` 或 `/c` 命令

### Q: 如何退出 Agent？
A: 在对话中输入 `/exit`、`/quit` 或 `/q` 命令

## 许可证

MIT License