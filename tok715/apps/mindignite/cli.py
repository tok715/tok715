import time

import click
from sqlalchemy import select
from sqlalchemy.orm import Session

from tok715.constants import USER_ID_OWNER
from tok715.database.collection import collection_messages
from tok715.database.model import Message
from tok715.database.util import initialize_database
from tok715.misc.client import connect_milvus, create_database_client
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

    while True:
        with Session(engine) as session:
            latest = session.scalars(
                select(Message).
                where(Message.user_id == USER_ID_OWNER).
                order_by(Message.ts.desc()).
                limit(1)
            ).first()
            if not latest:
                time.sleep(2)
                continue
            delay = int(time.time() * 1000) - latest.ts
            if delay < 2000:
                time.sleep(1 + (2000 - delay) / 1000)
                continue

        print("triggered")
        time.sleep(2)


if __name__ == "__main__":
    main()
