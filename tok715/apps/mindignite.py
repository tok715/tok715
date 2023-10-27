import time

import click

from tok715 import store
from tok715.ai.client import create_ai_service_client
from tok715.constants import USER_ID_TOK715, USER_GROUP_TOK715
from tok715.misc import load_config


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)

    ai_service = create_ai_service_client(conf)

    store.connect(conf, opt_init_db, ai_service)

    def record_response(response: str):
        msg = store.add_message(
            user_id=USER_ID_TOK715,
            user_group=USER_GROUP_TOK715,
            user_display_name='卡妹',
            content=response,
            ts=int(time.time() * 1000),
        )
        print('recorded:', msg.id)

    def on_triggered():
        messages = store.fetch_recent_messages()

        context = [{
            'role': 'system',
            'content': '你是一个人工智能女仆，你的名字叫 "卡妹"，你的主人叫 "罐头YK"。我们正在进行日常对话。',
        }] + [{
            'role': msg.chatml_role(),
            'content': msg.content,
        } for msg in reversed(messages)]

        response = ai_service.invoke_generation(context)
        print(response)
        record_response(response)

    def execute() -> float | int:
        messages = store.fetch_recent_messages(1)
        if not messages:
            return 2

        previous = messages[0]

        if previous.user_id == USER_ID_TOK715:
            return 2

        elapsed = int(time.time() * 1000) - previous.ts
        if elapsed < 2000:
            return 2000 - elapsed / 1000

        on_triggered()
        return 0

    while True:
        try:
            time.sleep(execute())
        except Exception as e:
            print("Error:", e)
            time.sleep(10)


if __name__ == "__main__":
    main()
