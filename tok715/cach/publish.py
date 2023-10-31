import json
import time

from .setup import _state
from ..misc import KEY_NL_INPUT


def publish_nl_input(
        user_id: str,
        user_group: str,
        user_display_name: str,
        content: str,
):
    _state.redis_client.publish(
        KEY_NL_INPUT(user_group, user_id),
        json.dumps({
            "ts": int(round(time.time() * 1000)),
            "content": content,
            "user": {
                "id": user_id,
                "group": user_group,
                "display_name": user_display_name,
            },
        }))
