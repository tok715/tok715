import redis

from .setup import _state

ON = 'ON'


class _flagger:
    def __init__(self, redis_client: redis.Redis, flag_key: str):
        self.redis_client = redis_client
        self.flag_key = flag_key

    def __enter__(self):
        self.redis_client.set(self.flag_key, 'ON')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.redis_client.set(self.flag_key, '')


def flagging(key: str) -> any:
    return _flagger(_state.redis_client, key)


def is_flag_on(key: str) -> bool:
    return _state.redis_client.get(key) == ON
