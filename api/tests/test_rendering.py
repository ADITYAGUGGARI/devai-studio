from io import BytesIO

from PIL import Image, ImageDraw

from devai.services import rendering


def test_export_works_without_system_fonts(monkeypatch):
    monkeypatch.setattr(
        rendering, "load_font", lambda size, **kwargs: rendering.ImageFont.load_default(size=size)
    )
    result = rendering.draw_slide(
        "Portable export", "Content remains readable on another operating system.", 1, 8
    )
    with Image.open(BytesIO(result)) as image:
        assert image.size == (1080, 1350)
        assert image.format == "PNG"


def test_wrapping_keeps_all_characters_in_long_tokens():
    draw = ImageDraw.Draw(Image.new("RGB", (1080, 1350)))
    font = rendering.load_font(35)
    token = "https://example.com/" + "long-path" * 40
    lines = rendering.wrap_text(draw, token, font, 815)
    assert "".join(lines) == token
    assert all(draw.textlength(line, font=font) <= 815 for line in lines)
