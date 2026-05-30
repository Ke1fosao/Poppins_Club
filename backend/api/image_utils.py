"""
Автоматичне стиснення завантажених зображень.

Коли в адмінці заливають велике фото (часто 3–6 МБ із телефона), воно
зменшується до розумної ширини й переекодовується з оптимізацією — щоб сайт
не гальмував. Маленькі фото не чіпаються (без втрати якості).

Працює для локального сховища (FileSystemStorage) — і локально, і на
PythonAnywhere. Якщо щось піде не так — мовчки пропускаємо (фото лишається як є).
"""

import os


def optimize_image_field(field, max_width=1920, jpeg_quality=82):
    """
    Стискає файл зображення поля «на місці», якщо він ширший за max_width.
    Повертає True, якщо зображення було змінено.
    """
    if not field:
        return False
    try:
        path = field.path  # лише для файлового сховища
    except (NotImplementedError, ValueError, AttributeError):
        return False
    if not path or not os.path.exists(path):
        return False

    try:
        from PIL import Image, ImageOps
    except Exception:
        return False

    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)  # врахувати орієнтацію з EXIF
    except Exception:
        return False

    if img.width <= max_width:
        return False  # вже невелике — не чіпаємо (без повторного переекодування)

    ratio = max_width / float(img.width)
    new_size = (max_width, max(1, round(img.height * ratio)))
    try:
        img = img.resize(new_size, Image.LANCZOS)
    except Exception:
        return False

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in (".jpg", ".jpeg"):
            img.convert("RGB").save(path, "JPEG", quality=jpeg_quality, optimize=True, progressive=True)
        elif ext == ".png":
            img.save(path, "PNG", optimize=True)
        elif ext == ".webp":
            img.save(path, "WEBP", quality=jpeg_quality, method=6)
        else:
            img.save(path)
    except Exception:
        return False

    return True
