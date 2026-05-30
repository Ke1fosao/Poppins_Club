"""
Робочий процес обробки звернень + «розумна» структура анкети.

Що робить ця міграція:
  1. Додає до заявок і повідомлень статус, позначку «прочитано», нотатки
     адміністратора та дату оновлення (єдиний робочий процес).
  2. Перетворює «тупі» текстові поля анкети на коректні типи:
       • мультивибір (вік, формати, час, дні, очікування) → JSON-списки;
       • «Так/Ні» (суміш, е-черга, педіатр) → булеві значення.
  3. Безпечно конвертує вже наявні дані (split по ', ' та мапінг Так→True).

Конвертація захищена: порожні значення → [] / None, помилки рядка не валять
всю міграцію.
"""

from django.db import migrations, models
import django.db.models.deletion


def _split_list(value):
    """'a, b, c' → ['a', 'b', 'c'];  '' / None → []."""
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [part.strip() for part in str(value).split(", ") if part.strip()]


def _yes_no_to_bool(value):
    """'Так' → True, 'Ні' → False, інше/порожнє → None."""
    text = (value or "").strip().lower()
    if not text:
        return None
    if text.startswith("так"):
        return True
    # кирилична 'ні' та можлива латинська 'i'
    if text.startswith("ні") or text.startswith("нi"):
        return False
    return None


def convert_survey_data(apps, schema_editor):
    Survey = apps.get_model("api", "SurveyApplication")
    for row in Survey.objects.all().iterator():
        try:
            row.ages = _split_list(row.age_group)
            row.formats = _split_list(row.format)
            row.time_slots_tmp = _split_list(row.time_slots)
            row.days_tmp = _split_list(row.days)
            row.expectations_tmp = _split_list(row.expectations)
            row.has_formula = _yes_no_to_bool(row.formula)
            row.in_e_queue = _yes_no_to_bool(row.e_queue)
            row.needs_pediatrist = _yes_no_to_bool(row.pediatrist)
            row.save(update_fields=[
                "ages", "formats", "time_slots_tmp", "days_tmp",
                "expectations_tmp", "has_formula", "in_e_queue", "needs_pediatrist",
            ])
        except Exception:
            # Жодна окрема пошкоджена заявка не повинна валити деплой.
            continue


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_alter_pagetext_hero_desc"),
    ]

    operations = [
        # ── 1. Робочий процес: нові поля на обох моделях ─────────────────
        migrations.AddField(
            model_name="surveyapplication",
            name="status",
            field=models.CharField(default="new", db_index=True, max_length=20, verbose_name="Статус обробки",
                                   choices=[("new", "🆕 Нова"), ("in_progress", "📞 В роботі"),
                                            ("contacted", "✅ Зв'язались"), ("enrolled", "🎉 Зараховано"),
                                            ("rejected", "🚫 Відмова"), ("archived", "📦 Архів")]),
        ),
        migrations.AddField(
            model_name="surveyapplication",
            name="is_read",
            field=models.BooleanField(default=False, db_index=True, verbose_name="Переглянуто"),
        ),
        migrations.AddField(
            model_name="surveyapplication",
            name="admin_notes",
            field=models.TextField(blank=True, default="", verbose_name="Нотатки адміністратора"),
        ),
        migrations.AddField(
            model_name="surveyapplication",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True, verbose_name="Останнє оновлення"),
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="status",
            field=models.CharField(default="new", db_index=True, max_length=20, verbose_name="Статус обробки",
                                   choices=[("new", "🆕 Нова"), ("in_progress", "📞 В роботі"),
                                            ("contacted", "✅ Зв'язались"), ("enrolled", "🎉 Зараховано"),
                                            ("rejected", "🚫 Відмова"), ("archived", "📦 Архів")]),
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="is_read",
            field=models.BooleanField(default=False, db_index=True, verbose_name="Переглянуто"),
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="admin_notes",
            field=models.TextField(blank=True, default="", verbose_name="Нотатки адміністратора"),
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True, verbose_name="Останнє оновлення"),
        ),

        # ── 2. Нові типізовані поля анкети (тимчасові — де імена збігаються) ─
        migrations.AddField(
            model_name="surveyapplication", name="ages",
            field=models.JSONField(blank=True, default=list, verbose_name="Вік дитини"),
        ),
        migrations.AddField(
            model_name="surveyapplication", name="formats",
            field=models.JSONField(blank=True, default=list, verbose_name="Формат перебування"),
        ),
        migrations.AddField(
            model_name="surveyapplication", name="time_slots_tmp",
            field=models.JSONField(blank=True, default=list, verbose_name="Часові проміжки"),
        ),
        migrations.AddField(
            model_name="surveyapplication", name="days_tmp",
            field=models.JSONField(blank=True, default=list, verbose_name="Дні тижня"),
        ),
        migrations.AddField(
            model_name="surveyapplication", name="expectations_tmp",
            field=models.JSONField(blank=True, default=list, verbose_name="Що найважливіше"),
        ),
        migrations.AddField(
            model_name="surveyapplication", name="has_formula",
            field=models.BooleanField(blank=True, null=True, verbose_name="Є дитяча суміш у раціоні"),
        ),
        migrations.AddField(
            model_name="surveyapplication", name="in_e_queue",
            field=models.BooleanField(blank=True, null=True, verbose_name="Зареєстровані в електронній черзі"),
        ),
        migrations.AddField(
            model_name="surveyapplication", name="needs_pediatrist",
            field=models.BooleanField(blank=True, null=True, verbose_name="Потрібен періодичний педіатр"),
        ),

        # ── 3. Конвертація наявних даних ─────────────────────────────────
        migrations.RunPython(convert_survey_data, noop),

        # ── 4. Прибираємо старі «тупі» поля ──────────────────────────────
        migrations.RemoveField(model_name="surveyapplication", name="age_group"),
        migrations.RemoveField(model_name="surveyapplication", name="format"),
        migrations.RemoveField(model_name="surveyapplication", name="formula"),
        migrations.RemoveField(model_name="surveyapplication", name="e_queue"),
        migrations.RemoveField(model_name="surveyapplication", name="pediatrist"),
        migrations.RemoveField(model_name="surveyapplication", name="time_slots"),
        migrations.RemoveField(model_name="surveyapplication", name="days"),
        migrations.RemoveField(model_name="surveyapplication", name="expectations"),

        # ── 5. Перейменовуємо тимчасові у фінальні імена ─────────────────
        migrations.RenameField(model_name="surveyapplication", old_name="time_slots_tmp", new_name="time_slots"),
        migrations.RenameField(model_name="surveyapplication", old_name="days_tmp", new_name="days"),
        migrations.RenameField(model_name="surveyapplication", old_name="expectations_tmp", new_name="expectations"),

        # ── 6. Індекси та verbose_name для існуючих полів ────────────────
        migrations.AlterField(
            model_name="surveyapplication", name="phone",
            field=models.CharField(db_index=True, max_length=20, verbose_name="Телефон"),
        ),
        migrations.AlterField(
            model_name="surveyapplication", name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Надійшло"),
        ),
        migrations.AlterField(
            model_name="contactmessage", name="phone",
            field=models.CharField(db_index=True, max_length=20, verbose_name="Телефон"),
        ),
        migrations.AlterField(
            model_name="contactmessage", name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Надійшло"),
        ),

        # ── 7. Композитні індекси ────────────────────────────────────────
        migrations.AddIndex(
            model_name="surveyapplication",
            index=models.Index(fields=["status", "-created_at"], name="api_survey_status_created_idx"),
        ),
        migrations.AddIndex(
            model_name="contactmessage",
            index=models.Index(fields=["status", "-created_at"], name="api_msg_status_created_idx"),
        ),

        # ── 8. Оновлення Meta (порядок у списку адмінки, назви) ───────────
        migrations.AlterModelOptions(
            name="surveyapplication",
            options={"ordering": ["-created_at"], "verbose_name": "Заявка з анкети",
                     "verbose_name_plural": "01 · Заявки з анкети"},
        ),
        migrations.AlterModelOptions(
            name="contactmessage",
            options={"ordering": ["-created_at"], "verbose_name": "Повідомлення",
                     "verbose_name_plural": "02 · Повідомлення з форми"},
        ),
        migrations.AlterModelOptions(
            name="siteinfo",
            options={"verbose_name": "Налаштування контактів", "verbose_name_plural": "03 · Контакти та соцмережі"},
        ),
        migrations.AlterModelOptions(
            name="pagetext",
            options={"verbose_name": "Тексти сторінок", "verbose_name_plural": "04 · Тексти розділів"},
        ),
        migrations.AlterModelOptions(
            name="aboutcard",
            options={"ordering": ["order", "id"], "verbose_name": "Картка 'Про нас'",
                     "verbose_name_plural": "05 · Про нас — картки"},
        ),
        migrations.AlterModelOptions(
            name="directioncard",
            options={"ordering": ["group", "order", "id"], "verbose_name": "Напрямок",
                     "verbose_name_plural": "06 · Напрямки розвитку"},
        ),
        migrations.AlterModelOptions(
            name="directiongalleryimage",
            options={"ordering": ["order", "id"], "verbose_name": "Фото каруселі (Напрямки - ряд 1)",
                     "verbose_name_plural": "06а · Напрямки: фото каруселі (ряд 1)"},
        ),
        migrations.AlterModelOptions(
            name="directioncollageimage",
            options={"ordering": ["position"], "verbose_name": "Фото колажу (Напрямки - ряд 2)",
                     "verbose_name_plural": "06б · Напрямки: фото колажу (ряд 2)"},
        ),
        migrations.AlterModelOptions(
            name="premiseslide",
            options={"ordering": ["order", "id"], "verbose_name": "Слайд приміщення",
                     "verbose_name_plural": "07 · Приміщення — слайди (з фото)"},
        ),
        migrations.AlterModelOptions(
            name="servicegroup",
            options={"ordering": ["order", "id"], "verbose_name": "Вікова група",
                     "verbose_name_plural": "08 · Вікові групи"},
        ),
        migrations.AlterModelOptions(
            name="faqitem",
            options={"ordering": ["order", "id"], "verbose_name": "Питання (FAQ)",
                     "verbose_name_plural": "09 · Питання та відповіді"},
        ),
    ]
