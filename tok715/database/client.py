from typing import Dict

import redis


def create_redis(conf: Dict) -> redis.Redis:
    kwargs = {"decode_responses": True}
    kwargs.update(conf['redis'])
    return redis.Redis(**kwargs)
