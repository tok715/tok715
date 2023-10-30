import subprocess

import click

from tok715.misc import load_config, create_redis_client, ffmpeg_check, create_aliyun_nls_synthesizer, \
    KEY_SPEECH_SYNTHESIZER_INVOCATION, KEY_SPEECH_SYNTHESIZER_WORKING


@click.command()
@click.option("--conf", "-c", "opt_conf", default="tok715.yml", help="config file")
@click.option("--device", "-d", "opt_device", default="", help="microphone device id")
def main(opt_conf: str, opt_device: str):
    conf = load_config(opt_conf)

    redis_client = create_redis_client(conf)

    # check ffmpeg
    if not ffmpeg_check('ffplay'):
        return

    audio_data = bytearray()

    def on_tts_data(data: any, *args):
        audio_data.extend(data)

    def on_tts_completed(*args, **kwargs):
        with open('audio.mp3', 'wb') as f:
            f.write(audio_data)
        audio_data.clear()

        subprocess.run([
            'ffplay',
            '-hide_banner',
            '-autoexit',
            '-vn',
            'audio.mp3',
        ])

    ss = create_aliyun_nls_synthesizer(conf, redis_client, on_data=on_tts_data, on_completed=on_tts_completed)

    redis_client.delete(KEY_SPEECH_SYNTHESIZER_INVOCATION)

    while True:
        key, content = redis_client.blpop(KEY_SPEECH_SYNTHESIZER_INVOCATION)

        if not content:
            continue

        print("response:", content)

        redis_client.set(KEY_SPEECH_SYNTHESIZER_WORKING, 'true')

        ss.start(
            text=content,
            voice='zhixiaomei',
            aformat='mp3',
            wait_complete=True,
        )

        redis_client.set(KEY_SPEECH_SYNTHESIZER_WORKING, '')


if __name__ == "__main__":
    main()
