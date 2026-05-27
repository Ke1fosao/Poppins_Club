from django.db import migrations


TELEGRAM_URL = "https://t.me/thepoppinsclub?start=|utm_clientid=380396880.1779801058"
THREADS_URL = "https://www.threads.com/@thepoppinsclub?utm_clientid=380396880.1779801058"


def forwards(apps, schema_editor):
    SiteInfo = apps.get_model("api", "SiteInfo")
    site = SiteInfo.objects.first()
    if not site:
        return
    # Заповнюємо тільки якщо порожнє — щоб не затирати, якщо адмін вже щось вписав
    if not site.telegram:
        site.telegram = TELEGRAM_URL
    if not site.threads:
        site.threads = THREADS_URL
    site.save(update_fields=["telegram", "threads"])


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_remove_siteinfo_youtube_siteinfo_telegram_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
