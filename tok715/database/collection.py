import pymilvus
from pymilvus import DataType


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
