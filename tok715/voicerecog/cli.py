import json
import subprocess
import time

import click
import redis
import yaml

from tok715.constants import *
from tok715.vendor import nls


def decode_aliyun_nls_data(s: str) -> (str, int):
    data = json.loads(s)
    if "payload" not in data:
        return "", 0
    payload = data["payload"]
    if "result" not in payload or "index" not in payload:
        return "", 0
    return payload["result"], payload["index"]


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--device", "-d", "opt_device", default="", help="microphone device id")
def main(opt_conf: str, opt_device: str):
    with open(opt_conf, "r") as f:
        conf = yaml.safe_load(f)

    # sub conf
    user_conf = {
        "id": "owner",
        "name": "主人",
        "group": "owner",
    }
    user_conf.update(conf["user"])

    # check ffmpeg
    print(">>>>> checking ffmpeg")
    try:
        subprocess.run(["ffmpeg", "-version"], check=True)
    except Exception as e:
        print(f"failed checking ffmpeg: {e}")

    # choose microphone device
    if not opt_device:
        subprocess.run([
            "ffmpeg",
            "-hide_banner",
            "-f",
            "avfoundation",
            "-list_devices",
            "true",
            "-i",
            "",
        ])
        opt_device = input("choose microphone device: ").strip()

    print(f"using microphone device: {opt_device}")

    # create redis client
    redis_cfg = {"decode_responses": True}
    redis_cfg.update(conf["redis"])

    redis_client = redis.Redis(**redis_cfg)

    # retrieve aliyun_nls_token
    nls_conf = conf['aliyun']['nls']
    aliyun_nls_token = redis_client.get(KEY_ALIYUN_NLS_TOKEN)

    if not aliyun_nls_token:
        print(">>>>> retrieving aliyun_nls_token")
        aliyun_nls_token, expires_at = nls.get_token(
            nls_conf['access_key_id'],
            nls_conf['access_key_secret'],
        )
        redis_client.setex(KEY_ALIYUN_NLS_TOKEN, expires_at - int(time.time()), aliyun_nls_token)
        print(f"aliyun_nls_token fetched")
    else:
        print(f"aliyun_nls_token found")

    def on_sentence_end(s: str, *args):
        text, index = decode_aliyun_nls_data(s)
        if not text or not index:
            return
        print(f"on_sentence_end: {text}")

        result = json.dumps({
            "ts": int(round(time.time() * 1000)),
            "text": text,
            "user": user_conf,
        })

        redis_client.publish(KEY_NL_INPUT(user_conf['group'], user_conf['id']), result)

    def on_result_changed(s: str, *args):
        result, index = decode_aliyun_nls_data(s)
        if not result or not index:
            return
        print(f"on_result_changed: {result}")

    # start speech recognizer
    st = nls.NlsSpeechTranscriber(
        url=nls_conf['endpoint'],
        token=aliyun_nls_token,
        appkey=nls_conf['app_key'],
        on_sentence_end=on_sentence_end,
        on_result_changed=on_result_changed,
    )

    print(">>>>> starting speech recognizer")

    st.start(
        aformat="pcm",
        sample_rate=16000,
        ch=1,
        enable_intermediate_result=True,
        enable_punctuation_prediction=True,
        enable_inverse_text_normalization=True,
    )

    print(">>>>> starting ffmpeg to capture audio")

    # start ffmpeg
    with subprocess.Popen([
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "avfoundation",
        "-i",
        ":" + opt_device,
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-f",
        "s16le",
        "pipe:1",
    ], stdout=subprocess.PIPE, universal_newlines=False) as p:
        while True:
            data = p.stdout.read(1024)
            if data:
                st.send_audio(data)

    print(">>>>> ffmpeg started")

    while True:
        try:
            data, _ = p.communicate(timeout=10)
            print(f"ffmpeg read {len(data)} bytes")
            st.send_audio(data)
        except subprocess.TimeoutExpired:
            pass


if __name__ == "__main__":
    main()
