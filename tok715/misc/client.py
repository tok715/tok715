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


class AIServiceClient:
    def __init__(self, conf: Dict):
        self.url = conf['ai_service']['url']

    def _invoke(self, method: str, args: Dict) -> Dict:
        r = requests.post(self.url, json={'method': method, 'args': args})
        if r.status_code != 200:
            raise Exception('failed invoking ai_service: ' + r.text)
        data = r.json()
        return data['result']

    def invoke_embeddings(self, input_texts: List[str]) -> List[List[float]]:
        args = {'input_texts': input_texts}
        result = self._invoke('embeddings', args)
        return result['vectors']

    def invoke_generation(self, context: List[Dict]) -> str:
        args = {'context': context}
        result = self._invoke('generation', args)
        return result['response']
