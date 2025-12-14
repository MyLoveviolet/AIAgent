from src.Agent import agent
from src.schemas import GameState


def play_chengyu_game():
    # 初始化上下文
    context = GameState(used_chengyu=set(), last_chengyu="")
    print("欢迎来到成语接龙游戏！请开始输入一个成语。")

    while True:
        user_input = input("> ")

        # 调用Agent
        response = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config={"configurable": {"thread_id": "1"}},
            context=context,
            verbose=True
        )['structured_response']

        print(response)

        defeat_message = response.defeat_message
        chengyu_response = response.chengyu_response
        validation_message = response.validation_message
        # chat_with_user = response.chat_with_user

        if defeat_message:
            print(defeat_message)
            break

        # if chat_with_user:
        #     print(chat_with_user)
        #     continue

        # 处理验证结果
        if validation_message == "合法":
            print(f"{chengyu_response}")

            # 记录使用过的成语
            context.used_chengyu.add(user_input)
            context.used_chengyu.add(chengyu_response)
            context.last_chengyu = chengyu_response
        else:
            print(f"{validation_message}，请重新输入。")





