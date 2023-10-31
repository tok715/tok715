import click

from tok715 import cach
from tok715.misc import load_config


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.argument("input_text")
def main(opt_conf: str, input_text: str):
    conf = load_config(opt_conf)

    cach.connect(conf)

    user_conf = conf['user']

    cach.publish_nl_input(
        user_id=user_conf['id'],
        user_group=user_conf['group'],
        user_display_name=user_conf['display_name'],
        content=input_text.strip(),
    )


if __name__ == "__main__":
    main()
