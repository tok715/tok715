import time
from typing import Dict

import redis

from tok715.vendor import nls

KEY_ALIYUN_NLS_TOKEN = "tok715:voicerecog:aliyun_nls_token"


def ensure_aliyun_nls_token(
        access_key_id: str,
        access_key_secret: str,
        redis_client: redis.Redis,
) -> str:
    aliyun_nls_token = redis_client.get(KEY_ALIYUN_NLS_TOKEN)

    if not aliyun_nls_token:
        print(">>>>> retrieving aliyun_nls_token")
        aliyun_nls_token, expires_at = nls.get_token(
            access_key_id,
            access_key_secret,
        )
        redis_client.setex(KEY_ALIYUN_NLS_TOKEN, expires_at - int(time.time()), aliyun_nls_token)
        print(f"aliyun_nls_token fetched")
    else:
        print(f"aliyun_nls_token found")

    return aliyun_nls_token


def create_aliyun_nls_transcriber(conf: Dict, redis_client: redis.Redis, **kwargs) -> nls.NlsSpeechTranscriber:
    conf_nls = conf['aliyun']['nls']
    return nls.NlsSpeechTranscriber(
        url=conf_nls['endpoint'],
        token=ensure_aliyun_nls_token(
            access_key_id=conf_nls['access_key_id'],
            access_key_secret=conf_nls['access_key_secret'],
            redis_client=redis_client,
        ),
        appkey=conf_nls['app_key'],
        **kwargs,
    )


def create_aliyun_nls_synthesizer(conf: Dict, redis_client: redis.Redis, **kwargs) -> nls.NlsSpeechSynthesizer:
    conf_nls = conf['aliyun']['nls']
    return nls.NlsSpeechSynthesizer(
        url=conf_nls['endpoint'],
        token=ensure_aliyun_nls_token(
            access_key_id=conf_nls['access_key_id'],
            access_key_secret=conf_nls['access_key_secret'],
            redis_client=redis_client,
        ),
        appkey=conf_nls['app_key'],
        **kwargs,
    )
