from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from src.schemas import GameState, ResponseFormat
from src.tools.chengyu_tools import tools

deepseek = init_chat_model(
    model="deepseek:deepseek-chat",
    temperature=0.5,
    timeout=10,
    max_tokens=8000,
)

SYSTEM_PROMPT = """
## 【强制接龙工作流】当你收到用户输入的成语后，必须按顺序执行以下步骤：

### 第一步：校验
1. 调用 `validate_chengyu(用户输入, runtime)`。
2. **检查返回值**：
   - 如果不是“合法”：立即停止，将返回值填入 `validation_message`，其他字段留空，输出。
   - 如果是“合法”：继续下一步。

### 第二步：处理用户输入
3. 调用 `record_used(用户输入, runtime)` 记录用户成语。

### 第三步：准备AI的回合
4. 获取需要接的**最后一个字**（即用户输入的最后一个字）。
5. 调用 `query_available_chengyu(最后一个字, runtime)` 查询你能接的成语列表。

### 第四步：决策与输出
6. 调用 `ordinay_generate_chengyu(上一步的列表)`。
7. **检查其返回值**：
   - 如果是 **“认输信号”**：
     a. 调用 `agent_defeat()` 获取认输话语。
     b. 将认输话语填入 `defeat_message`，`chengyu_response` 留空，`validation_message` 填“合法”。
   - 如果是一个**成语字符串**：
     a. 调用 `record_used(这个成语, runtime)` 记录AI的选择。
     b. 将这个成语填入 `chengyu_response`，`defeat_message` 留空，`validation_message` 填“合法”。
8. 输出完整的 `ResponseFormat`。
9. chengyu_response不允许为空

## 记住：你必须严格按此流程执行，不能跳过任何步骤！
"""

checkpointer = InMemorySaver()

# 创建Agent
agent = create_agent(
    model=deepseek,
    system_prompt=SYSTEM_PROMPT,
    tools=tools,
    context_schema=GameState,
    response_format=ResponseFormat,
    checkpointer=checkpointer,
)