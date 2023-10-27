from typing import List

import pymilvus
from pymilvus import DataType

from tok715.database.model import Message


def collection_messages_build() -> pymilvus.Collection:
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


def collection_messages() -> pymilvus.Collection:
    return pymilvus.Collection(name="messages")


def collection_messages_upsert(
        collection: pymilvus.Collection,
        items: List[Message],
        vectors: List[List[float]]):
    collection.upsert([
        [item.id for item in items],
        [item.user_group for item in items],
        [item.ts for item in items],
        vectors,
    ])
