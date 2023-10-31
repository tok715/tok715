import json
import time
from typing import Dict

import click

from tok715 import cach
from tok715.misc import *


def decode_aliyun_nls_data(s: str) -> (str, int):
    data = json.loads(s)
    if "payload" not in data:
        return "", 0
    payload = data["payload"]
    if "result" not in payload or "index" not in payload:
        return "", 0
    return payload["result"], payload["index"]


def process_in(conf: Dict, opt_device: str):
    cach.connect(conf)

    user_conf = conf["user"]

    def on_sentence_end(s: str, *args):
        content, index = decode_aliyun_nls_data(s)
        if not content or not index:
            return
        print(f"on_sentence_end: {content}")

        cach.publish_nl_input(
            user_id=user_conf['id'],
            user_group=user_conf['group'],
            user_display_name=user_conf['display_name'],
            content=content,
        )

    def on_result_changed(s: str, *args):
        result, index = decode_aliyun_nls_data(s)
        if not result or not index:
            return
        print(f"on_result_changed: {result}")

    # start speech recognizer
    st = create_aliyun_nls_transcriber(
        conf,
        cach.redis_client(),
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

    print(">>>>> starting ffmpeg to capture audio input")

    # start ffmpeg
    with ffmpeg_stream_audio_input(opt_device) as p:
        while True:
            data = p.stdout.read(512)
            if data:
                st.send_audio(data)
            time.sleep(0.001)


def process_out(conf: Dict):
    cach.connect(conf)

    audio_data = bytearray()

    def on_tts_data(data: any, *args):
        audio_data.extend(data)

    def on_tts_completed(*args, **kwargs):
        ffmpeg_playback(audio_data)
        audio_data.clear()

    ss = create_aliyun_nls_synthesizer(
        conf,
        cach.redis_client(),
        on_data=on_tts_data,
        on_completed=on_tts_completed,
    )

    def on_speech_synthesizer_invocation(key, content):
        if not content:
            return
        print("synthesize:", content)

        with cach.flagging(KEY_SPEECH_SYNTHESIZER_WORKING):
            ss.start(
                text=content,
                voice='zhixiaomei',
                aformat='mp3',
                wait_complete=True,
            )

    cach.consume_queue_forever(
        [KEY_SPEECH_SYNTHESIZER_INVOCATION],
        on_data=on_speech_synthesizer_invocation,
        clean_on_start=True,
    )


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--device", "-d", "opt_device", default="", help="audio input device id")
def main(opt_conf: str, opt_device: str):
    conf = load_config(opt_conf)

    if not ffmpeg_check():
        return

    if not opt_device:
        opt_device = ffmpeg_choose_input_device()

    print(f'using audio input device: {opt_device}')

    run_processes([
        (process_in, (conf, opt_device)),
        (process_out, (conf,)),
    ])
