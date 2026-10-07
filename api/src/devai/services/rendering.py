"""Portable, deterministic 1080 × 1350 carousel rendering."""

import os
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

WIDTH, HEIGHT = 1080, 1350


def load_font(size: int, *, bold: bool = False):
    configured = os.getenv("CAROUSEL_FONT_BOLD" if bold else "CAROUSEL_FONT_REGULAR")
    candidates = [
        configured,
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/System/Library/Fonts/Supplemental/Arial{' Bold' if bold else ''}.ttf",
        f"C:/Windows/Fonts/arial{'bd' if bold else ''}.ttf",
    ]
    for path in candidates:
        if path:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def wrap_text(draw, text: str, font, width: int) -> list[str]:
    """Keep paragraph breaks and wrap long URLs/tokens inside the content width."""
    result = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if draw.textlength(candidate, font=font) <= width:
                current = candidate
                continue
            if current:
                result.append(current)
            current = ""
            for character in word:
                if current and draw.textlength(current + character, font=font) > width:
                    result.append(current)
                    current = ""
                current += character
        result.append(current)
    return result


def _artwork_background(path):
    if not path:
        return None
    try:
        with Image.open(Path(path)) as artwork:
            image = ImageOps.fit(
                artwork.convert("RGB"), (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS
            ).convert("RGBA")
    except (OSError, ValueError):
        return None
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for y in range(430, HEIGHT, 4):
        alpha = min(190, 24 + int((y - 430) * 0.23))
        overlay_draw.rectangle((0, y, WIDTH, y + 3), fill=(8, 12, 27, alpha))
    return Image.alpha_composite(image, overlay).convert("RGB")


def draw_slide(headline: str, body: str, index: int, total: int, artwork_path=None) -> bytes:
    image = _artwork_background(artwork_path)
    has_artwork = image is not None
    if image is None:
        image = Image.new("RGB", (WIDTH, HEIGHT), (13, 17, 34))
    draw = ImageDraw.Draw(image)
    if not has_artwork:
        draw.ellipse((450, 100, 1450, 1100), fill=(35, 28, 82))
        draw.rounded_rectangle((66, 70, 1014, 1280), radius=36, outline=(88, 82, 144), width=3)
    label_font = load_font(24, bold=True)
    draw.text(
        (115, 133), "DEVAISTUDIO  /  ENGINEERING NOTES", font=label_font, fill=(124, 216, 247)
    )

    # Fit all copy between the brand header and footer instead of discarding lines.
    for title_size in range(66, 21, -2):
        body_size = max(18, round(title_size * 0.53))
        title_font = load_font(title_size, bold=True)
        body_font = load_font(body_size)
        title_lines = wrap_text(draw, headline, title_font, 815)
        body_lines = wrap_text(draw, body, body_font, 815)
        title_step, body_step = int(title_size * 1.3), int(body_size * 1.5)
        content_height = len(title_lines) * title_step + 45 + len(body_lines) * body_step
        if content_height <= 870:
            break
    else:
        raise ValueError("Slide copy is too long to fit; shorten the headline or body")

    y = 260 + max(0, (870 - content_height) // 3)
    for line in title_lines:
        draw.text((115, y), line, font=title_font, fill="white")
        y += title_step
    y += 45
    for line in body_lines:
        draw.text((115, y), line, font=body_font, fill=(198, 205, 228))
        y += body_step

    draw.line((115, 1170, 960, 1170), fill=(94, 96, 157), width=3)
    draw.text((115, 1200), "BUILD SMARTER. SHIP BETTER.", font=label_font, fill=(147, 153, 205))
    draw.text((875, 1200), f"{index:02d} / {total:02d}", font=label_font, fill=(147, 216, 247))
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
