import copy
from typing import Optional, Dict

import redis


class State:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None


_state = State()


def connect(conf: Dict):
    kwargs = {"decode_responses": True}
    if 'redis' in conf:
        kwargs.update(
            copy.deepcopy(conf['redis'])
        )
    _state.redis_client = redis.Redis(**kwargs)


def redis_client() -> redis.Redis:
    return _state.redis_client
