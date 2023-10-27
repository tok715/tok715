import json
import time
from typing import Dict

import click
from sqlalchemy.orm import Session

from tok715.constants import KEY_NL_INPUT_ASTERISK
from tok715.database.model import Message
from tok715.misc.client import create_redis_client, create_database_client
from tok715.misc.config import load_config


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)

    # create sqlalchemy engine
    engine = create_database_client(conf)

    # initialize database
    if opt_init_db:
        # sqlalchemy engine
        from tok715.database.model import Base
        engine.echo = True
        Base.metadata.create_all(engine)
        return

    # handle incoming message
    def handle_message_input(data: Dict):
        with Session(engine) as session:
            msg = Message(
                user_id=data['user']['id'],
                user_group=data['user']['group'],
                user_display_name=data['user']['display_name'],
                content=data['content'],
                ts=data['ts'],
                vector_status=0,
            )
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
            handle_message_input(json.loads(message['data']))
        time.sleep(0.001)


if __name__ == "__main__":
    main()
