import json
import re
import time
from typing import Dict, Optional, List, Tuple

import click
from sqlalchemy.orm import Session

from tok715 import stor, cach
from tok715.ai.client import create_ai_service_client
from tok715.ai.tunning import SYSTEM_HISTORY, SYSTEM_PROMPT
from tok715.misc import *
from tok715.stor import Message


def process_save_input(conf: Dict):
    cach.connect(conf)
    stor.connect(conf)

    # handle incoming message
    def handle_message_input(channel: str, raw: str):
        data = json.loads(raw)

        with stor.create_session() as session:
            msg = stor.add_message(
                session,
                user_id=data['user']['id'],
                user_group=data['user']['group'],
                user_display_name=data['user']['display_name'],
                content=data['content'],
                ts=data['ts'],
            )
            print(f"input#{msg.id}: {msg.content}")

    cach.consume_topic_forever(
        [KEY_NL_INPUT_ASTERISK],
        on_data=handle_message_input,
    )


def process_maintenance(conf: Dict):
    stor.connect(conf)

    def execute():
        with stor.create_session() as session:
            stor.update_stale_messages(session)

    while True:
        print("maintenance triggered", time.time())
        try:
            execute()
        except Exception as e:
            print(f'maintenance failed: {e}')
        time.sleep(30)


def clean_conversation_text(input_text: str) -> str:
    output = []
    for s in input_text.split('\n'):
        s = s.strip()
        re.sub(r'[\s]+', ' ', s)
        if s:
            output.append(s)
    return '。'.join(output)


def create_history_from_messages(messages: List[Message]) -> Tuple[Optional[str], List[List[str]]]:
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

    return input_user, history


def process_ignite(conf: Dict):
    ai_service = create_ai_service_client(conf)

    cach.connect(conf)
    stor.connect(conf, ai_service=ai_service)

    def create_chat_args(session: Session) -> Optional[Dict]:
        messages = stor.fetch_recent_messages(session, 50)

        query, history = create_history_from_messages(messages)

        if not query:
            return None

        return {'query': query, 'history': SYSTEM_HISTORY + history, 'system': SYSTEM_PROMPT}

    def on_triggered():
        with stor.create_session() as session:
            chat_args = create_chat_args(session)

            if not chat_args:
                return

            print(chat_args)
            print("==============================")

            response = ai_service.invoke_chat(**chat_args)
            response = clean_conversation_text(response)
            print(response)

            if not response:
                return

            # save message
            msg = stor.add_message(
                session,
                user_id=USER_ID_TOK715,
                user_group=USER_GROUP_TOK715,
                user_display_name=USER_DISPLAY_NAME_TOK715,
                content=response,
                ts=int(time.time() * 1000),
            )
            print(f"saved output#{msg.id}")

            # push to redis
            cach.append_queue(KEY_SPEECH_SYNTHESIZER_INVOCATION, response)

    def execute() -> float | int | None:
        with stor.create_session() as session:
            if cach.is_flag_on(KEY_SPEECH_SYNTHESIZER_WORKING):
                return 2

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


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)
    stor.connect(conf, opt_init_db)

    run_processes([
        (process_save_input, (conf,)),
        (process_maintenance, (conf,)),
        (process_ignite, (conf,)),
    ])
