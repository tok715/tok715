import sqlalchemy

from tok715.database.collection import collection_messages_build


def initialize_database(engine: sqlalchemy.Engine):
    # sqlalchemy engine
    from tok715.database.model import Base
    engine.echo = True
    Base.metadata.create_all(engine)

    # milvus
    collection_messages_build()
