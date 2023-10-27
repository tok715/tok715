import time

import click

from tok715.database.collection import collection_messages_build, collection_messages
from tok715.misc.client import create_database_client, connect_milvus
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
        # milvus
        collection_messages_build()
        return

    # milvus collection for messages
    collection = collection_messages()

    while True:
        # TODO: fetch data from database and insert into milvus
        time.sleep(3)


if __name__ == "__main__":
    main()
