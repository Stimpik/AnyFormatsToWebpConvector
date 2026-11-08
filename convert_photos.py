from pathlib import Path
import argparse
from statistics import median

from PIL import Image, ImageOps


SIZE = (800, 800)
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def background_color(image):
    """Выбрать белый или чёрный цвет по краям фотографии."""
    sample = image.convert("RGB")
    sample.thumbnail((200, 200))

    width, height = sample.size
    pixels = sample.load()
    brightness = []

    for x in range(width):
        for y in (0, height - 1):
            r, g, b = pixels[x, y]
            brightness.append((r + g + b) / 3)

    for y in range(height):
        for x in (0, width - 1):
            r, g, b = pixels[x, y]
            brightness.append((r + g + b) / 3)

    return "white" if median(brightness) >= 128 else "black"


def convert(source, destination, background):
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert("RGBA")

        color = background_color(image) if background == "auto" else background
        image = ImageOps.contain(image, SIZE, Image.Resampling.LANCZOS)

        if color == "transparent":
            result = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        else:
            result = Image.new("RGBA", SIZE, color)

        position = (
            (SIZE[0] - image.width) // 2,
            (SIZE[1] - image.height) // 2,
        )
        result.alpha_composite(image, position)

        if color != "transparent":
            result = result.convert("RGB")

        destination.parent.mkdir(parents=True, exist_ok=True)
        result.save(destination, "WEBP", quality=85, method=6)


def main():
    parser = argparse.ArgumentParser(
        description="Преобразовать фотографии в WebP размером 800×800."
    )
    parser.add_argument("input_folder", type=Path, help="Папка с фотографиями")
    parser.add_argument("output_folder", type=Path, help="Папка для результатов")
    parser.add_argument(
        "--background",
        choices=("auto", "white", "black", "transparent"),
        default="auto",
        help="Цвет добавленных полей (по умолчанию: auto)",
    )
    args = parser.parse_args()

    input_folder = args.input_folder.resolve()
    output_folder = args.output_folder.resolve()

    if not input_folder.is_dir():
        parser.error("Исходная папка не найдена")

    if output_folder == input_folder or output_folder.is_relative_to(input_folder):
        parser.error("Папка результатов должна находиться вне исходной папки")

    count = 0

    for source in input_folder.rglob("*"):
        if not source.is_file() or source.suffix.lower() not in EXTENSIONS:
            continue

        relative = source.relative_to(input_folder)
        destination = output_folder / relative.parent / f"{source.name}.webp"

        try:
            convert(source, destination, args.background)
            count += 1
            print(f"Готово: {source} → {destination}")
        except Exception as error:
            print(f"Ошибка: {source}: {error}")

    print(f"Обработано фотографий: {count}")


if __name__ == "__main__":
    main()