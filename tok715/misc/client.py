from typing import Dict, List

import pymilvus
import redis
import requests
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


def invoke_ai_service(conf: Dict, method: str, args: Dict) -> Dict:
    url = conf['ai_service']['url']
    r = requests.post(url, json={'method': method, 'args': args})
    if r.status_code != 200:
        raise Exception('failed invoking ai_service: ' + r.text)
    data = r.json()
    return data['result']


def invoke_ai_service_embeddings(conf: Dict, input_texts: List[str]) -> List[List[float]]:
    args = {'input_texts': input_texts}
    result = invoke_ai_service(conf, 'embeddings', args)
    return result['vectors']


def invoke_ai_service_generation(conf: Dict, context: List[Dict]) -> str:
    args = {'context': context}
    result = invoke_ai_service(conf, 'generation', args)
    return result['response']
