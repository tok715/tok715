from typing import Dict

import redis


def create_redis_client(conf: Dict) -> redis.Redis:
    kwargs = {"decode_responses": True}
    if 'redis' in conf:
        kwargs.update(conf['redis'])
    return redis.Redis(**kwargs)
