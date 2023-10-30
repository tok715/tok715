import json
import time
from typing import Callable, Dict, List

import redis


def redis_queue_consume(
        redis_client: redis.Redis,
        on_message_data: Callable[[Dict], None],
        key_patterns: List[str],
):
    # start redis subscribe
    ps = redis_client.pubsub()
    ps.psubscribe(*key_patterns)

    while True:
        message = ps.get_message()
        if message and message['type'] == 'pmessage':
            try:
                on_message_data(json.loads(message['data']))
            except Exception as e:
                print("failed to handle message input", e)
        time.sleep(0.001)
