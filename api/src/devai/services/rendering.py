"""Read model-composed slides; never draw or overlay Instagram artwork."""

from pathlib import Path


def draw_slide(headline, body, index, total, *, artwork_path=None):
    if not artwork_path or not Path(artwork_path).is_file():
        raise ValueError("Generate an AI-native image for this slide before preview or export")
    return Path(artwork_path).read_bytes()
