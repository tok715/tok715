from typing import Dict

import yaml


def load_config(opt_conf) -> Dict:
    with open(opt_conf, "r") as f:
        conf = yaml.safe_load(f)
    return conf
