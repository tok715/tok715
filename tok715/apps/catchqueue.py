import json
import time
from typing import Dict

import click

from tok715 import stor
from tok715.misc import create_redis_client, load_config, KEY_NL_INPUT_ASTERISK


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)

    stor.connect(conf, opt_init_db)

    # handle incoming message
    def handle_message_input(data: Dict):
        with stor.create_session() as session:
            msg = stor.add_message(
                session,
                user_id=data['user']['id'],
                user_group=data['user']['group'],
                user_display_name=data['user']['display_name'],
                content=data['content'],
                ts=data['ts'],
            )
            print(f"message #{msg.id} saved")

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
