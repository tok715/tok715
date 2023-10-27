import time

import click

from tok715 import stor
from tok715.ai.client import create_ai_service_client
from tok715.misc import load_config, USER_ID_TOK715, USER_GROUP_TOK715


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)

    ai_service = create_ai_service_client(conf)

    stor.connect(conf, opt_init_db, ai_service)

    def on_triggered():
        with stor.create_session() as session:
            messages = stor.fetch_recent_messages(session)

            context = [{
                'role': 'system',
                'content': '你是一个人工智能女仆，你的名字叫 "卡妹"，你的主人叫 "罐头YK"。我们正在进行日常对话。',
            }] + [{
                'role': msg.chatml_role(),
                'content': msg.content,
            } for msg in reversed(messages)]

            response = ai_service.invoke_generation(context)
            print(response)

            msg = stor.add_message(
                session,
                user_id=USER_ID_TOK715,
                user_group=USER_GROUP_TOK715,
                user_display_name='卡妹',
                content=response,
                ts=int(time.time() * 1000),
            )
            print(f"message #{msg.id} saved")

    def execute() -> float | int | None:
        with stor.create_session() as session:
            messages = stor.fetch_recent_messages(session, 1)
            if not messages:
                return 2

            previous = messages[0]

            if previous.user_id == USER_ID_TOK715:
                return 2

            elapsed = int(time.time() * 1000) - previous.ts
            if elapsed < 2000:
                return 2000 - elapsed / 1000

        on_triggered()

    while True:
        try:
            time.sleep(execute() or 0)
        except Exception as e:
            print("Error:", e)
            time.sleep(10)


if __name__ == "__main__":
    main()
