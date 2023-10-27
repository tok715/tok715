import json
import time
from typing import Dict

import click
from sqlalchemy.orm import Session

from tok715.constants import KEY_NL_INPUT_ASTERISK, VECTOR_VERSION
from tok715.database.collection import collection_messages, collection_messages_upsert
from tok715.database.model import Message, message_should_vectorize
from tok715.database.util import initialize_database
from tok715.misc.client import create_redis_client, create_database_client, connect_milvus, \
    AIServiceClient
from tok715.misc.config import load_config


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)

    ai_service = AIServiceClient(conf)

    # create sqlalchemy engine
    engine = create_database_client(conf)

    # connect to milvus
    connect_milvus(conf)

    # initialize database
    if opt_init_db:
        initialize_database(engine)
        return

    collection = collection_messages()

    # handle incoming message
    def handle_message_input(data: Dict):
        with Session(engine) as session:
            msg = Message(
                user_id=data['user']['id'],
                user_group=data['user']['group'],
                user_display_name=data['user']['display_name'],
                content=data['content'],
                ts=data['ts'],
                vector_version=VECTOR_VERSION,
            )

            if message_should_vectorize(msg):
                # first stage commit
                msg.vector_status = 0
                session.add(msg)
                session.commit()

                # calculate vector
                vectors = ai_service.invoke_embeddings([msg.content])
                collection_messages_upsert(collection, [msg], vectors)

                # second stage commit
                msg.vector_status = 1
                session.commit()
            else:
                msg.vector_status = -1
                session.add(msg)
                session.commit()

            print(f"message {msg.id} saved")

    # create redis client
    redis_client = create_redis_client(conf)

    # start redis subscribe
    ps = redis_client.pubsub()
    ps.psubscribe(KEY_NL_INPUT_ASTERISK)

    while True:
        message = ps.get_message()
        if message and message['type'] == 'pmessage':
            try:
                handle_message_input(json.loads(message['data']))
            except Exception as e:
                print("failed to handle message input", e)
        time.sleep(0.001)


if __name__ == "__main__":
    main()
