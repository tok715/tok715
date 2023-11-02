import json
import time


class UserInput:
    def __init__(
            self,
            ts: int = None,
            content: str = None,
            user_id: str = None,
            user_group: str = None,
            user_display_name: str = None,
    ):
        if ts is None:
            ts = int(round(time.time() * 1000))
        self.ts = ts
        self.content = content
        self.user_id = user_id
        self.user_group = user_group
        self.user_display_name = user_display_name

    @staticmethod
    def from_json(s: str) -> 'UserInput':
        return UserInput(**json.loads(s))

    def to_json(self):
        return json.dumps(self.__dict__)
