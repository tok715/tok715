import time

import click
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session

from tok715.constants import VECTOR_VERSION
from tok715.database.collection import collection_messages
from tok715.database.model import Message, message_should_vectorize
from tok715.database.util import initialize_database
from tok715.misc.client import create_database_client, connect_milvus, invoke_ai_service_embeddings
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

    # milvus collection for messages
    collection = collection_messages()

    def execute():
        now_ts = int(time.time() * 1000)

        with Session(engine) as session:
            # select messages desc
            messages = session.scalars(
                select(Message).where(
                    or_(
                        # previous vector version
                        Message.vector_version != VECTOR_VERSION,
                        and_(
                            # current vector version
                            Message.vector_version == VECTOR_VERSION,
                            # not vectorized for 10 minutes
                            Message.vector_status == 0,
                            Message.ts < now_ts - 600 * 1000,
                        ),
                    )
                ).order_by(Message.ts.desc()).limit(10)
            ).all()

            # filter out for vectorize
            to_vectorize = []

            for message in messages:
                if message_should_vectorize(message):
                    to_vectorize.append(message)
                else:
                    # update vector_status = -1 for ignored
                    message.vector_status = -1

            if to_vectorize:
                ids = [item.id for item in to_vectorize]

                print(f'calculating embeddings for {ids}')

                embeddings = invoke_ai_service_embeddings(
                    conf,
                    [item.content for item in to_vectorize],
                )

                collection.upsert([
                    ids,
                    [item.user_group for item in to_vectorize],
                    [item.ts for item in to_vectorize],
                    embeddings,
                ])

                print(f"vectorized {len(to_vectorize)} messages")

                # update vector_status for to_vectorize
                for message in to_vectorize:
                    message.vector_status = 1

            # update all vector_version
            for message in messages:
                message.vector_status = VECTOR_VERSION

            session.commit()

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
