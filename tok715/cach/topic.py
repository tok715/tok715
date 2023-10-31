import time
from typing import List, Callable

from .setup import _state


def consume_topic_forever(
        keys: List[str],
        on_data: Callable[[str, str], None],
):
    # start redis subscribe
    ps = _state.redis_client.pubsub()
    ps.psubscribe(*keys)

    while True:
        message = ps.get_message()
        if message and message['type'] == 'pmessage':
            try:
                on_data(message['channel'], message['data'])
            except Exception as e:
                print("failed to handle topic data", e)
                time.sleep(3)
        time.sleep(0.001)
