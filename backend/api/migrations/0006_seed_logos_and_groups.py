import re
from django.db import migrations


LOGO_NAVBAR_PATH = "logo/Логотип з текстом.webp"
LOGO_FOOTER_PATH = "logo/логотип_білий.webp"

# Перші два — у "first" ряд, інші — у "second"
FIRST_ROW_TITLES = {"Інтелектуальний фундамент", "Творча майстерня"}
SECOND_ROW_TITLES = {"Пізнання довкілля", "Здоров'я та активність"}

MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def clean_map(url):
    if not url:
        return ""
    m = MD_LINK_RE.search(url)
    if m:
        return m.group(1).strip()
    return url.strip()


def forwards(apps, schema_editor):
    SiteInfo = apps.get_model("api", "SiteInfo")
    DirectionCard = apps.get_model("api", "DirectionCard")

    # Налаштування логотипів за замовчуванням (вказуємо шлях відносно MEDIA_ROOT)
    site = SiteInfo.objects.first()
    if site:
        if not site.logo_navbar:
            site.logo_navbar.name = LOGO_NAVBAR_PATH
        if not site.logo_footer:
            site.logo_footer.name = LOGO_FOOTER_PATH
        # Очистимо map_url від markdown-обгортки якщо є
        site.map_url = clean_map(site.map_url)
        site.save()

    # Розподіл напрямків по двох рядках
    for card in DirectionCard.objects.all():
        if card.title in FIRST_ROW_TITLES:
            card.group = "first"
        elif card.title in SECOND_ROW_TITLES:
            card.group = "second"
        else:
            # за замовчуванням залишаємо first
            card.group = "first"
        card.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_directioncollageimage_directiongalleryimage_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
