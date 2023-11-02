import click

from tok715 import cach
from tok715.misc import load_config, KEY_USER_INPUT
from tok715.types import UserInput


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.argument("input_text")
def main(opt_conf: str, input_text: str):
    conf = load_config(opt_conf)

    cach.connect(conf)

    user_conf = conf['user']

    cach.append_queue(
        KEY_USER_INPUT,
        UserInput(
            content=input_text.strip(),
            user_id=user_conf['id'],
            user_group=user_conf['group'],
            user_display_name=user_conf['display_name'],
        ).to_json(),
    )

    cach.disconnect()


if __name__ == "__main__":
    main()
