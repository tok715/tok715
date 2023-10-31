import subprocess


def ffmpeg_check() -> bool:
    print('>>>>>> checking ffmpeg/ffplay')
    try:
        subprocess.run([
            'ffmpeg',
            '-version',
        ], check=True)
    except Exception as e:
        print(f'failed checking ffmpeg: {e}')
        return False
    try:
        subprocess.run([
            'ffplay',
            '-version',
        ], check=True)
    except Exception as e:
        print(f'failed checking ffplay: {e}')
        return False
    return True


def ffmpeg_choose_input_device() -> str:
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
    return input(f"choose input device: ").strip()


def ffmpeg_stream_audio_input(opt_device: str) -> subprocess.Popen:
    return subprocess.Popen([
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
    ], stdout=subprocess.PIPE, universal_newlines=False)


def ffmpeg_playback(audio_data: any, ext: str = 'mp3'):
    filename = 'audio.' + ext

    with open(filename, 'wb') as f:
        f.write(audio_data)

    subprocess.run([
        'ffplay',
        '-hide_banner',
        '-autoexit',
        '-vn',
        filename
    ])
