import subprocess


def ffmpeg_check(cmd: str = 'ffmpeg') -> bool:
    # check ffmpeg
    print(f">>>>> checking {cmd}")
    try:
        subprocess.run([cmd, "-version"], check=True)
        return True
    except Exception as e:
        print(f"failed checking {cmd}: {e}")
        return False


def ffmpeg_choose_device(t: str) -> str:
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
    return input(f"choose {t} device: ").strip()
