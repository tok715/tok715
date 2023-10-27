import json
import time

import click

from tok715.misc import create_redis_client, load_config, KEY_NL_INPUT


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
def main(opt_conf: str):
    conf = load_config(opt_conf)

    # sub conf
    user_conf = {
        "id": "owner",
        "name": "主人",
        "group": "owner",
    }
    user_conf.update(conf["user"])

    redis_client = create_redis_client(conf)

    while True:
        content = input("input text:").strip()
        result = json.dumps({
            "ts": int(round(time.time() * 1000)),
            "content": content,
            "user": user_conf,
        })

        redis_client.publish(KEY_NL_INPUT(user_conf['group'], user_conf['id']), result)


if __name__ == "__main__":
    main()
