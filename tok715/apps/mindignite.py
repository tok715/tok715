import re
import time
from typing import List, Optional, Dict

import click

from tok715 import stor
from tok715.ai.client import create_ai_service_client
from tok715.ai.tunning import SYSTEM_HISTORY
from tok715.misc import load_config, USER_ID_TOK715, USER_GROUP_TOK715, USER_DISPLAY_NAME_TOK715


def clean_conversation_text(input_text: str) -> str:
    output = []
    for s in input_text.split('\n'):
        s = s.strip()
        re.sub(r'[\s]+', ' ', s)
        if s:
            output.append(s)
    return '。'.join(output)


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)

    ai_service = create_ai_service_client(conf)

    stor.connect(conf, opt_init_db, ai_service)

    def create_chat_context(messages: List[stor.Message]) -> Optional[Dict]:
        history = []

        input_user = ''
        input_assistant = ''
        for msg in messages:
            if msg.user_id == USER_ID_TOK715:
                # ignore leading messages from tok715
                if not input_user:
                    continue
                input_assistant += msg.content.strip() + '\n'
            else:
                # start new line
                if input_user and input_assistant:
                    history.append([input_user.strip(), input_assistant.strip()])
                    input_user = ''
                    input_assistant = ''
                input_user += msg.content.strip() + '\n'

        if input_user and input_assistant:
            history.append([input_user, input_assistant])
            input_user = ''
            input_assistant = ''

        input_user = input_user.strip()

        if not input_user:
            return None

        return {'input_text': input_user, 'history': SYSTEM_HISTORY + history}

    def on_triggered():
        with stor.create_session() as session:
            messages = stor.fetch_recent_messages(session, 50)

            generation_args = create_chat_context(messages)
            print(generation_args)
            print("==============================")
            if not generation_args:
                return

            response = ai_service.invoke_generation(**generation_args)
            response = clean_conversation_text(response)
            print(response)

            if not response:
                return

            msg = stor.add_message(
                session,
                user_id=USER_ID_TOK715,
                user_group=USER_GROUP_TOK715,
                user_display_name=USER_DISPLAY_NAME_TOK715,
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

            elapsed_milli = int(time.time() * 1000) - previous.ts
            if elapsed_milli < 2000:
                return (2100 - elapsed_milli) / 1000

        on_triggered()

    while True:
        try:
            time.sleep(execute() or 0)
        except Exception as e:
            print("Error:", e)
            time.sleep(10)


if __name__ == "__main__":
    main()
