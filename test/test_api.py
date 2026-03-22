import anthropic
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取API密钥和base_url
api_key = os.getenv("MINIMAX_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.minimax.chat/v1/text/anthropic-compatible")

if not api_key:
    print("错误: 未提供API密钥")
    exit(1)

# 初始化Anthropic客户端
client = anthropic.Anthropic(
    api_key=api_key,
    base_url=base_url
)

print("测试MiniMax API连接...")
print(f"使用的API端点: {base_url}")

# 发送测试请求
message = client.messages.create(
    model="MiniMax-M2.7",
    max_tokens=1000,
    system="You are a helpful assistant.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hi, how are you?"
                }
            ]
        }
    ]
)

# 输出响应结果
print("\n响应结果:")
print("=" * 60)

for block in message.content:
    if block.type == "thinking":
        print(f"Thinking:\n{block.thinking}\n")
    elif block.type == "text":
        print(f"Text:\n{block.text}\n")

print("=" * 60)
print("API测试完成！")