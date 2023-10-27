import time

import click
from sqlalchemy import select
from sqlalchemy.orm import Session

from tok715.constants import USER_ID_TOK715, USER_GROUP_TOK715, VECTOR_VERSION
from tok715.database.collection import collection_messages, collection_messages_upsert
from tok715.database.model import Message, message_should_vectorize
from tok715.database.util import initialize_database
from tok715.misc.client import connect_milvus, create_database_client, invoke_ai_service_generation, \
    invoke_ai_service_embeddings
from tok715.misc.config import load_config


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)

    # create sqlalchemy engine
    engine = create_database_client(conf)

    # connect to milvus
    connect_milvus(conf)

    # initialize database
    if opt_init_db:
        initialize_database(engine)
        return

    collection = collection_messages()

    def record_response(response: str):
        with Session(engine) as session:
            msg = Message(
                user_id=USER_ID_TOK715,
                user_group=USER_GROUP_TOK715,
                user_display_name='卡妹',
                content=response,
                ts=int(time.time() * 1000),
                vector_version=VECTOR_VERSION,
            )
            if message_should_vectorize(msg):
                # first stage commit
                msg.vector_status = 0
                session.add(msg)
                session.commit()

                # calculate vector
                vectors = invoke_ai_service_embeddings(conf, [msg.content])
                collection_messages_upsert(collection, [msg], vectors)

                # second stage commit
                msg.vector_status = 1
                session.commit()
            else:
                msg.vector_status = -1
                session.add(msg)
                session.commit()

    def trigger():
        with Session(engine) as session:
            mesages = session.scalars(
                select(
                    Message
                ).order_by(Message.ts.desc()).limit(50)
            ).all()
        context = [{
            'role': 'system',
            'text': '你是一个人工智能女仆，你的名字叫 "卡妹"，你的主人叫 "罐头YK"。我们正在进行日常对话。',
        }]
        for msg in reversed(mesages):
            context.append({
                'role': (
                    'assistant' if msg.user_id == USER_ID_TOK715 else 'user'
                ),
                'text': msg.content,
            })
        response = invoke_ai_service_generation(conf, context)
        print(response)
        record_response(response)

    def execute():
        with Session(engine) as session:
            previous = session.scalars(
                select(Message).
                order_by(Message.ts.desc()).
                limit(1)
            ).first()

            if not previous:
                time.sleep(2)
                return

            if previous.user_id == USER_ID_TOK715:
                time.sleep(2)
                return

            delay = int(time.time() * 1000) - previous.ts
            if delay < 2000:
                time.sleep(1 + (2000 - delay) / 1000)
                return
        trigger()

    while True:
        try:
            execute()
        except Exception as e:
            print("Error:", e)
            time.sleep(10)

        time.sleep(2)


if __name__ == "__main__":
    main()
