# src/tools/chengyu_tools.py

from .databases import chengyu_db  # 导入上面的知识库实例
from src.schemas import GameState
from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model

@tool
def validate_chengyu(chengyu: str, runtime: ToolRuntime[GameState]) -> str:
    """
    检查参数chengyu是否符合规则

    :param chengyu: 用户输入的最新的成语
    :param runtime: 包含游戏状态的运行时上下文
    :return: 将返回值文本发送至validation_message
    """
    used_chengyu = runtime.context.used_chengyu
    last_chengyu = runtime.context.last_chengyu

    # 1. 检查长度
    if len(chengyu) != 4:
        return f"成语'{chengyu}'不是四字成语"

    # 2. 检查是否存在于知识库（关键，杜绝编造）
    if not chengyu_db.contains(chengyu):
        return f"成语'{chengyu}'未被标准知识库收录"

    # 3. 检查接龙规则（如果已经有上一个成语）
    if last_chengyu and chengyu[0] != last_chengyu[-1]:
        return f"需要以'{last_chengyu[-1]}'开头，但收到的是'{chengyu[0]}'"

    # 4. 检查首尾相同
    if chengyu[0] == chengyu[-1]:
        return f"成语'{chengyu}'首尾字相同"

    # 5. 检查是否重复使用
    if chengyu in used_chengyu:
        return f"成语'{chengyu}'已使用过"

    # 所有检查通过
    return "合法"

@tool
def query_available_chengyu(last_char: str, runtime: ToolRuntime[GameState]) -> list:
    """
    查询以last_char开头的未使用成语, last_char是用户最新使用成语的最后一个字
    如果找到了可使用成语则输出，否则回输出”认输信号“开始认输
    Args:
        last_char: 要查询的**首字**，如'睛'
        runtime: 运行时上下文
    """
    used_chengyu = runtime.context.used_chengyu
    available = chengyu_db.query_by_first_char(last_char, used_chengyu)

    if not available:
        return "认输信号"

    import random
    chosen = random.choice(available)
    return {"action": "CONTINUE", "chengyu": chosen}


@tool
def record_used(chengyu: str, runtime: ToolRuntime[GameState]) -> None:
    """
    记录使用过的成语并更新最新成语。
    :param chengyu: 用户输入的最新的成语
    :param runtime: 包含游戏状态的运行时上下文
    :return: "DONE"表示完成该记录和更新操作
    """
    runtime.context.used_chengyu.add(chengyu)
    runtime.context.last_chengyu = chengyu
    return "DONE"


@tool
def agent_defeat(runtime: ToolRuntime[GameState] = None) -> str:
    """
    当得到了“认输信号”时，使用LLM实时生成认输话语。更具创意和上下文相关性。

    :param runtime: 包含游戏状态的运行时上下文，用于获取对战详情。
    :return 于ResponseFormat.defeat_message中输出生成的文本
    """
    llm = init_chat_model(
        model="deepseek:deepseek-chat",
        temperature=0.9,
        max_tokens=50,
    )

    # 可以基于游戏状态丰富提示词
    used_count = len(runtime.context.used_chengyu) if runtime else 0
    prompt = f"""
    我们在进行成语接龙，我已经无词可接，需要认输。
    请生成一句不超过30字的认输话语，要求：
    1. 体现风度和对对手的赞赏。
    2. 可以带一点文言或幽默色彩。
    3. 不要提及“AI”、“程序”等字眼，要像真人玩家。

    当前已对战{used_count}个回合。
    只输出认输话语本身，不要任何其他解释。
    """
    response = llm.invoke(prompt)
    return response.content.strip()


@tool
def user_defeat(runtime: ToolRuntime[GameState]) -> str:
    """
    当用户认输时，使用LLM生成胜利宣言。结合游戏状态，生成得体、有风度的回应。

    :param runtime: 包含游戏状态的运行时上下文，用于获取对战详情。
    :return: 生成的胜利话语文本，用于ResponseFormat.defeat_message。
    """

    # 1. 初始化LLM（使用你项目中已有的deepseek实例或新建一个）
    llm = init_chat_model(
        model="deepseek:deepseek-chat",
        temperature=0.9,  # 创造性稍高，让回答更生动
        max_tokens=50,  # 限制长度，节约Token
    )

    # 2. 从游戏状态中提取信息，让Prompt更具体
    used_count = len(runtime.context.used_chengyu)
    last_chengyu = runtime.context.last_chengyu

    # 3. 构建详细、具体的Prompt
    prompt = f"""
    我们正在进行一场成语接龙游戏。经过 {used_count} 个回合的激烈交锋，对方玩家刚刚主动认输，由我（AI）取得了胜利。

    我最后一个接龙的成语是「{last_chengyu}」。

    请为我生成一段**胜利宣言**，要求如下：
    1.  **体现风度**：谦逊有礼，不炫耀，肯定对方的实力。
    2.  **结合战况**：可以提及“激战多轮”或对方表现出色。
    3.  **风格自然**：像是真人高手间的对话，略带文言或书卷气更佳。
    4.  **字数限制**：严格控制在30个字以内。

    请只输出最终的胜利宣言，不要有任何额外的解释、前缀或引号。
    """

    # 4. 调用LLM并返回结果
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        # 可选：如果LLM调用失败，返回一个优雅的降级话术
        print(f"LLM生成胜利宣言失败，使用备选方案: {e}")
        return "阁下行棋如流水，今日险胜半子，实属侥幸。期待下次切磋！"

tools = [validate_chengyu, query_available_chengyu, record_used, agent_defeat, user_defeat]