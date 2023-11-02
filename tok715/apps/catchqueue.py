import json

import click

from tok715 import stor, cach
from tok715.misc import load_config, KEY_NL_INPUT_ASTERISK


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)

    cach.connect(conf)
    stor.connect(conf, opt_init_db)

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
            print(f"#{msg.id}: {msg.content}")

    cach.consume_topic_forever(
        [KEY_NL_INPUT_ASTERISK],
        on_data=handle_message_input,
    )


if __name__ == "__main__":
    main()
