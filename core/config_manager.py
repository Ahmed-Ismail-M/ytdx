import json
from pathlib import Path
import platform

SYSTEM = platform.system()
root = Path(__file__).parent.parent
CONFIG_PATH = root / '.ytdx_cfg.json'
BIN_PATH = root / 'bin'
DEFAULT_CONFIG = {
    'last_folder': str(Path.home()),
    'dark_mode': False,
    'format_preset': 'Best (video+audio)'
}
FFMPEG_PATH = Path(BIN_PATH) / ('ffmpeg.exe' if SYSTEM == 'Windows' else 'ffmpeg')


def load_config():
    try:
        if Path(CONFIG_PATH).exists():
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(cfg, f)
    except Exception:
        pass
