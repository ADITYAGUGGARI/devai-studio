from io import BytesIO

import pytest
from PIL import Image

from devai.services.artwork import normalize_image
from devai.services.rendering import draw_slide


def test_artwork_is_returned_without_drawing_or_text_overlay(tmp_path):
    path = tmp_path / "model.png"
    path.write_bytes(b"provider-generated-complete-composition")
    assert draw_slide("Ignored", "Ignored", 1, 8, artwork_path=str(path)) == path.read_bytes()
    with pytest.raises(ValueError, match="AI-native"):
        draw_slide("Headline", "Body", 1, 8)


def test_image_conversion_preserves_aspect_and_rejects_bad_dimensions():
    output = BytesIO()
    Image.new("RGB", (1088, 1360), (10, 20, 30)).save(output, format="PNG")
    result = normalize_image(output.getvalue(), output_format="JPEG")
    with Image.open(BytesIO(result)) as image:
        assert image.size == (1080, 1350) and image.format == "JPEG"
    wrong = BytesIO()
    Image.new("RGB", (1024, 1024)).save(wrong, format="PNG")
    with pytest.raises(ValueError, match="4:5"):
        normalize_image(wrong.getvalue())
