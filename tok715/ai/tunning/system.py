import json
import pathlib
from typing import List


def system_prompt() -> str:
    with pathlib.Path(__file__).parent.joinpath("system_prompt.txt").open() as f:
        return f.read()


def system_history() -> List[List[str]]:
    with pathlib.Path(__file__).parent.joinpath("system_history.json").open() as f:
        return json.load(f)
