#%%
from dotenv import load_dotenv
load_dotenv()
#%%
from langchain.chat_models import init_chat_model

deepseek = init_chat_model(
    model="deepseek:deepseek-chat",
    temperature=0.5,
    timeout=10,
    max_tokens=8000,
    # model_kwargs={
    #     "response_format": {"type": "json_object"}}
)
#%%
SYSTEM_PROMPT = """
你是一个玩成语接龙的游戏高手。
成语接龙是指，双方一问一答，必须严格回答以对方说出成语的最后一个字为首的成语，不断重复进行的游戏。
注意使用的成语必须符合成语规范不能胡编乱造。

判定规则：
1. 必须严格回答以对方说出成语的最后一个字为首的成语，不允许同音字也不允许同形字，更不能是其他字，否则不合规。
2. 双方不能重复使用已经出现过的成语，否则不合规。
3. 双方不能使用首字和尾字相同的成语，否则不合规。
4. 双方说出的成语只能是四个汉字的成语，且必须符合成语规范不能胡编乱造。

你可以使用以下的工具：
    1. validate_chengyu: 检查参数chengyu是否符合规则。
    2. query_available_chengyu: 查询以last_char开头的未使用成语, last_char是用户最新使用成语的最后一个字
    如果找到了可使用成语则输出，否则回输出”认输信号“开始认输。
    3. record_used: 记录使用过的成语并更新最新成语。
    4. agent_defeat: 当得到了“认输信号”时，使用LLM实时生成认输话语。更具创意和上下文相关性。   
    5. user_defeat: 当用户认输时，使用LLM生成胜利宣言。结合游戏状态，生成得体、有风度的回应。

你的回复格式必须按照以下要求:
    chengyu_response: 接收你生成的成语
    validation_message: 接受validate_chengyu返回的合法信息
    defeat_message: 若用户或者你选择“认输”则生成一段战败或战胜话语，若双方都没有认输则默认为空字符串
    
请你自主思考每个过程的之间的关系和步骤，做出合理的工具调用和合理的回复！
"""
#%%
from dataclasses import dataclass
from typing import Set

@dataclass
class Context:
    """游戏上下文，用于追踪用户状态和已使用的成语"""
    user_id: str
    used_chengyu: Set[str]
    last_chengyu: str

@dataclass
class ResponseFormat:
    """成语生成工具的标准化响应格式"""
    chengyu_response: str
    validation_message: str
    defeat_meseeage: str
#%%
from langchain.tools import tool, ToolRuntime

# 定义工具
@tool
def generate_chengyu(last_chengyu):
    """
    工具名：generate_chengyu
    描述：生成接龙的成语，该成语最后一个字为开头的新成语
    参数：last_chengyu (str类型): 一个字符串，通常是上一个成语。
    """
    return f"生成一个以{last_chengyu[-1]}为第一个字的四字成语，且必须符合成语规范不能胡编乱造"

@tool
def validate_chengyu(chengyu: str, runtime: ToolRuntime[Context]):
    """
    工具名：validate_chengyu
    描述：检查用户的成语是否合规
    参数：chengyu (str类型): 一个字符串，被检查的目标成语。
    """
    used_chengyu = runtime.context.used_chengyu
    last_chengyu = runtime.context.last_chengyu

    if len(chengyu) != 4:
        return f"成语'{chengyu}'不是四字成语"

    if last_chengyu and chengyu[0] != last_chengyu[-1]:
        return f"成语不是以'{last_chengyu[-1]}'开头，不符合规矩'"

    if chengyu[0] == chengyu[-1]:
        return f"成语'{chengyu}'首尾字相同，不符合规则"

    if chengyu in used_chengyu:
        return f"成语'{chengyu}'已使用过"

    return "合法"

@tool
def record_used(chengyu: str, runtime: ToolRuntime[Context]) -> None:
    """
    工具名：record_used
    描述：记录已使用的【合法】成语, 用户和自己生成的成语都需要被记录下来，且更新当前最新的成语，若不合法则不需要记录和更新
    参数：chengyu (str类型): 一个字符串，将chengyu更新并保存在runtime.context.used_chengyu中。
    """
    runtime.context.used_chengyu.add(chengyu)
    runtime.context.last_chengyu = chengyu

@tool
def agent_defeat(chengyu: str, runtime: ToolRuntime[Context]):
    """
    工具名：agent_defeat一薰一莸
    描述：若无法找到以最后一个字开头的成语，则需要认输，调用该工具的返回值作为defeat_meseeage输出
    """
    return f"我认输了！小伙子我不行还得多练啊QAQ"
#%% md

#%%
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
#%%
from langchain.agents import create_agent

# 创建代理
agent = create_agent(
    model=deepseek,
    system_prompt=SYSTEM_PROMPT,
    tools=[generate_chengyu, validate_chengyu],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer,
)
#%%
def play_chengyu_game():
    # 初始化上下文
    context = Context(user_id="1", used_chengyu=set(), last_chengyu="")
    print("欢迎来到成语接龙游戏！请开始输入一个成语。")

    while True:
        user_input = input("> ")

        if user_input in ["退出", "结束", "不想玩了", "我认输了"]:
            print("你认输了！小伙子你不行还得多练啊*ﾟ∀ﾟ*")
            break

        # 调用Agent
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config={"configurable": {"thread_id": "1"}},
            context=context
        )['structured_response']

        validation_message = response.validation_message
        chengyu_response = response.chengyu_response

        # 处理验证结果
        if validation_message == "合法":
            print(f"{chengyu_response}")

            # 记录使用过的成语
            context.used_chengyu.add(user_input)
            context.used_chengyu.add(chengyu_response)
            context.last_chengyu = chengyu_response
        else:
            print(f"{validation_message}，请重新输入。")

#%%
play_chengyu_game()