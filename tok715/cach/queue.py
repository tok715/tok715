import time
from typing import Callable, List

from .setup import _state


def consume_queue_forever(
        keys: List[str],
        on_data: Callable[[str, str], None],
        clean_on_start: bool = False,
):
    if clean_on_start:
        for key in keys:
            _state.redis_client.delete(key)
    while True:
        key, content = _state.redis_client.blpop(keys)
        try:
            on_data(key, content)
        except Exception as e:
            print(f'failed to handle queue data {key}: {e}')
            time.sleep(3)


def append_queue(key: str, content: str):
    _state.redis_client.rpush(key, content)
