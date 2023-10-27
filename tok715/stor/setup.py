from typing import Dict, Optional

import pymilvus
import sqlalchemy
from pymilvus import DataType
from sqlalchemy.orm import Session

from tok715.ai.client import AIServiceClient, create_ai_service_client

VECTOR_VERSION = 1


class State:
    def __init__(self):
        self.engine: Optional[sqlalchemy.Engine] = None
        self.ai_service: Optional[AIServiceClient] = None
        self.collection_messages: Optional[pymilvus.Collection] = None


_state = State()


def connect(
        conf: Dict,
        init_store: bool = False,
        ai_service: Optional[AIServiceClient] = None,
):
    """
    initialize database connections
    :param conf:
    :param init_store:
    :param ai_service:
    :return:
    """
    # sqlalchemy
    kwargs: Dict = conf['database']
    url = kwargs.pop('url')
    _state.engine = sqlalchemy.create_engine(url, **kwargs)

    if init_store:
        from .model import Base
        _state.engine.echo = True
        Base.metadata.create_all(_state.engine)

    # milvus
    kwargs = {'alias': 'default'}
    if 'milvus' in conf:
        kwargs.update(conf['milvus'])
    pymilvus.connections.connect(**kwargs)
    if init_store:
        _state.collection_messages = _define_collection_messages()
    else:
        _state.collection_messages = pymilvus.Collection(name="messages")

    # ai service
    if ai_service is None:
        ai_service = create_ai_service_client(conf)
    _state.ai_service = ai_service


def _define_collection_messages():
    # milvus
    collection = pymilvus.Collection(
        name="messages",
        schema=pymilvus.CollectionSchema(
            fields=[
                pymilvus.FieldSchema("id", dtype=DataType.INT64, is_primary=True, auto_id=False),
                pymilvus.FieldSchema("user_group", dtype=DataType.VARCHAR, max_length=64),
                pymilvus.FieldSchema("ts", dtype=DataType.INT64),
                pymilvus.FieldSchema("content", dtype=DataType.FLOAT_VECTOR, dim=1024)
            ],
            description="message collection",
        ),
    )
    collection.create_index(
        field_name="content",
        index_name="idx_content",
        index_params={
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {
                "nlist": 1024
            }
        },
    )
    collection.create_index(
        field_name="user_group",
        index_name="idx_user_group",
    )
    collection.create_index(
        field_name="ts",
        index_name="idx_ts",
    )

    return collection


def create_session() -> Session:
    return Session(_state.engine)
