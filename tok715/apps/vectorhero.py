import time

import click

from tok715 import store
from tok715.ai.client import create_ai_service_client
from tok715.misc import load_config


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--init-db", "-i", "opt_init_db", is_flag=True, help="initialize database")
def main(opt_conf, opt_init_db):
    conf = load_config(opt_conf)

    ai_service = create_ai_service_client(conf)

    store.connect(conf, opt_init_db, ai_service)

    def execute():
        store.update_stale_messages()

    while True:
        print("triggered at", time.time())
        try:
            execute()
        except Exception as e:
            print(f'execution failed: {e}')
            time.sleep(10)
        time.sleep(3)


if __name__ == "__main__":
    main()
