from typing import Dict

import pymilvus
import redis
import sqlalchemy
from sqlalchemy import create_engine


def create_redis_client(conf: Dict) -> redis.Redis:
    kwargs = {"decode_responses": True}
    if 'redis' in conf:
        kwargs.update(conf['redis'])
    return redis.Redis(**kwargs)


def create_database_client(conf: Dict) -> sqlalchemy.Engine:
    kwargs: Dict = conf['database']
    url = kwargs.pop('url')
    return create_engine(url, **kwargs)


def connect_milvus(conf: Dict) -> None:
    kwargs = {'alias': 'default'}
    if 'milvus' in conf:
        kwargs.update(conf['milvus'])
    pymilvus.connections.connect(**kwargs)
