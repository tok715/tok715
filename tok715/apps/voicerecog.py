import json
import subprocess
import time

import click

from tok715.misc import *


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
    conf = load_config(opt_conf)

    # sub conf
    user_conf = conf["user"]

    # check ffmpeg
    if not ffmpeg_check():
        return

    # choose microphone device
    if not opt_device:
        opt_device = ffmpeg_choose_device('microphone')

    print(f"using microphone device: {opt_device}")

    # create redis client
    redis_client = create_redis_client(conf)

    def on_sentence_end(s: str, *args):
        content, index = decode_aliyun_nls_data(s)
        if not content or not index:
            return
        print(f"on_sentence_end: {content}")

        result = json.dumps({
            "ts": int(round(time.time() * 1000)),
            "content": content,
            "user": user_conf,
        })

        redis_client.publish(KEY_NL_INPUT(user_conf['group'], user_conf['id']), result)

    def on_result_changed(s: str, *args):
        result, index = decode_aliyun_nls_data(s)
        if not result or not index:
            return
        print(f"on_result_changed: {result}")

    # start speech recognizer
    st = create_aliyun_nls_transcriber(
        conf,
        redis_client,
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
            data = p.stdout.read(512)
            if data:
                st.send_audio(data)
            time.sleep(0.001)


if __name__ == "__main__":
    main()
