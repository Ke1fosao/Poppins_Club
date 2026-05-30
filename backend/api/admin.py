"""
Адмін-панель сайту «The Poppins Club».

Принципи організації:
  • Звернення (заявки, повідомлення) — угорі списку, бо це щоденна робота.
    Кожне має робочий процес: статус, «прочитано», нотатки, масові дії.
  • Контент — нижче, згрупований по секціях сайту з підказками.
  • Візуальний стиль — теплий бірюзово-золотий, як на самому сайті
    (див. templates/admin/ та статичний CSS теми).
"""

import csv

from django import forms
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from .models import (
    ContactMessage, SurveyApplication,
    SiteInfo, PageText, FAQItem,
    AboutCard, DirectionCard, DirectionGalleryImage, DirectionCollageImage,
    PremiseSlide, ServiceGroup,
)


# ============================================================================
#  Хелпери відображення
# ============================================================================
def _img_preview(image_field, max_h=80):
    """HTML-превʼю зображення з округленими кутами."""
    if image_field:
        return format_html(
            '<img src="{}" style="max-height:{}px;max-width:200px;border-radius:8px;border:1px solid #e5e7eb;" />',
            image_field.url, max_h,
        )
    return mark_safe('<span style="color:#94a3b8;">— фото ще не завантажено —</span>')


def _section_desc(text):
    """Стилізована «панель допомоги» зверху групи полів."""
    return mark_safe(
        f'<div style="padding:12px 16px;background:#f0fdfa;border-left:4px solid #14b8a6;border-radius:8px;color:#0f766e;font-size:13px;line-height:1.5;margin:0 0 8px 0;">'
        f'{text}'
        f'</div>'
    )


# Кольори статусів: (текст, фон) — узгоджені з палітрою сайту
_STATUS_STYLE = {
    "new":         ("#0f766e", "#ccfbf1"),
    "in_progress": ("#92400e", "#fef3c7"),
    "contacted":   ("#1e40af", "#dbeafe"),
    "enrolled":    ("#166534", "#dcfce7"),
    "rejected":    ("#9f1239", "#ffe4e6"),
    "archived":    ("#475569", "#f1f5f9"),
}


def _status_badge(obj):
    fg, bg = _STATUS_STYLE.get(obj.status, ("#475569", "#f1f5f9"))
    return format_html(
        '<span style="background:{};color:{};padding:3px 11px;border-radius:999px;'
        'font-size:12px;font-weight:700;white-space:nowrap;">{}</span>',
        bg, fg, obj.get_status_display(),
    )


def _yesno_display(val):
    if val is True:
        return mark_safe('<span style="color:#166534;font-weight:600;">✅ Так</span>')
    if val is False:
        return mark_safe('<span style="color:#9f1239;font-weight:600;">❌ Ні</span>')
    return mark_safe('<span style="color:#94a3b8;">— не вказано —</span>')


def _bool_uk(val):
    """True → 'Так', False → 'Ні', None → '' (для CSV)."""
    if val is True:
        return "Так"
    if val is False:
        return "Ні"
    return ""


def _list_display(items, empty="— не вказано —"):
    items = [str(i).strip() for i in (items or []) if str(i).strip()]
    if not items:
        return mark_safe(f'<span style="color:#94a3b8;">{empty}</span>')
    lis = "".join(
        f'<li style="margin:2px 0;">{escape(i)}</li>' for i in items
    )
    return mark_safe(
        f'<ul style="margin:0;padding-left:18px;color:#1e293b;list-style:disc;">{lis}</ul>'
    )


class SingletonAdmin(admin.ModelAdmin):
    """
    Налаштування, що існують в одному екземплярі (контакти, тексти).
    • Не дає створити більше одного запису або видалити його.
    • Клік по пункту меню веде ОДРАЗУ у форму редагування
      (без проміжного списку з одним незрозумілим рядком).
    """
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.objects.first()
        if obj is not None:
            meta = self.model._meta
            url = reverse(
                f"admin:{meta.app_label}_{meta.model_name}_change",
                args=[obj.pk], current_app=self.admin_site.name,
            )
            return redirect(url)
        return super().changelist_view(request, extra_context)


# ============================================================================
#  Базовий клас для ЗВЕРНЕНЬ (заявки + повідомлення) з робочим процесом
# ============================================================================
class RequestAdminBase(admin.ModelAdmin):
    """Спільна логіка: статуси, фільтри, масові дії, авто-«прочитано»."""
    date_hierarchy = "created_at"
    list_filter = ("status", "is_read", "created_at")
    list_editable = ("status",)
    list_per_page = 30
    save_on_top = True
    actions = (
        "export_csv",
        "mark_in_progress", "mark_contacted", "mark_enrolled",
        "mark_rejected", "mark_archived", "mark_read", "mark_unread",
    )

    # Підкласи задають: ім'я файлу та колонки [(заголовок, callable(obj)->str)]
    csv_filename = "export.csv"
    csv_columns = ()

    # --- Звернення не створюються вручну (надходять із сайту) ---
    def has_add_permission(self, request):
        return False

    # --- Експорт у CSV (Excel-сумісний, з BOM) ---
    @admin.action(description="⬇️ Експортувати вибрані у CSV (Excel)")
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{self.csv_filename}"'
        response.write("﻿")  # BOM — щоб Excel коректно показав кирилицю
        writer = csv.writer(response)
        writer.writerow([header for header, _ in self.csv_columns])
        for obj in queryset:
            writer.writerow([accessor(obj) for _, accessor in self.csv_columns])
        return response

    # --- Авто-позначка «прочитано» при відкритті картки ---
    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, unquote(object_id))
        if obj is not None and not obj.is_read:
            type(obj).objects.filter(pk=obj.pk).update(is_read=True)
        return super().change_view(request, object_id, form_url, extra_context)

    # --- Колонки-індикатори ---
    @admin.display(description="", ordering="status")
    def unread_dot(self, obj):
        # «Нове» = статус «Нова» (єдине джерело правди). Зникає, щойно змінено статус.
        if obj.status == "new":
            return mark_safe('<span title="Нова — потребує уваги" style="color:#14b8a6;font-size:16px;">●</span>')
        return mark_safe('<span style="color:#e2e8f0;font-size:16px;">○</span>')

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        return _status_badge(obj)

    # --- Масові дії ---
    def _bulk(self, request, queryset, status, label):
        n = queryset.update(status=status)
        self.message_user(request, f"Оновлено заявок: {n} → «{label}».")

    @admin.action(description="📞 Позначити: В роботі")
    def mark_in_progress(self, request, queryset):
        self._bulk(request, queryset, "in_progress", "В роботі")

    @admin.action(description="✅ Позначити: Зв'язались")
    def mark_contacted(self, request, queryset):
        self._bulk(request, queryset, "contacted", "Зв'язались")

    @admin.action(description="🎉 Позначити: Зараховано")
    def mark_enrolled(self, request, queryset):
        self._bulk(request, queryset, "enrolled", "Зараховано")

    @admin.action(description="🚫 Позначити: Відмова")
    def mark_rejected(self, request, queryset):
        self._bulk(request, queryset, "rejected", "Відмова")

    @admin.action(description="📦 Перенести в Архів")
    def mark_archived(self, request, queryset):
        self._bulk(request, queryset, "archived", "Архів")

    @admin.action(description="👁 Позначити як переглянуті")
    def mark_read(self, request, queryset):
        n = queryset.update(is_read=True)
        self.message_user(request, f"Позначено переглянутими: {n}.")

    @admin.action(description="🔵 Позначити як нові (не переглянуті)")
    def mark_unread(self, request, queryset):
        n = queryset.update(is_read=False)
        self.message_user(request, f"Позначено новими: {n}.")


# ============================================================================
#  📋 ЗАЯВКИ З АНКЕТИ
# ============================================================================
@admin.register(SurveyApplication)
class SurveyApplicationAdmin(RequestAdminBase):
    list_display = ("unread_dot", "child_name", "parent_name", "phone",
                    "ages_short", "status", "created_at")
    list_display_links = ("child_name",)
    search_fields = ("child_name", "parent_name", "phone", "email")
    ordering = ("-created_at",)

    csv_filename = "zayavky_poppins.csv"
    csv_columns = (
        ("Надійшло", lambda o: o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else ""),
        ("Статус", lambda o: o.get_status_display()),
        ("Дитина", lambda o: o.child_name or ""),
        ("Батьки", lambda o: o.parent_name or ""),
        ("Телефон", lambda o: o.phone or ""),
        ("Email", lambda o: o.email or ""),
        ("Вік дитини", lambda o: "; ".join(o.ages or [])),
        ("Алергії", lambda o: o.allergies or ""),
        ("Дитяча суміш", lambda o: _bool_uk(o.has_formula)),
        ("В е-черзі", lambda o: _bool_uk(o.in_e_queue)),
        ("Потрібен педіатр", lambda o: _bool_uk(o.needs_pediatrist)),
        ("Формат перебування", lambda o: "; ".join(o.formats or [])),
        ("Часові проміжки", lambda o: "; ".join(o.time_slots or [])),
        ("Дні тижня", lambda o: "; ".join(o.days or [])),
        ("Що найважливіше", lambda o: "; ".join(o.expectations or [])),
        ("Червоні прапорці", lambda o: o.red_flags or ""),
        ("Цінність комунікації", lambda o: o.value_in_comm or ""),
        ("Виклики", lambda o: o.challenges or ""),
        ("Інтерес до лекцій", lambda o: o.lectures_interest or ""),
        ("Формат взаємодії", lambda o: o.interaction_formats or ""),
        ("Питання батьків", lambda o: o.parent_questions or ""),
        ("Пільги", lambda o: o.benefits or ""),
        ("Нотатки адміністратора", lambda o: o.admin_notes or ""),
    )

    readonly_fields = (
        "summary_card", "created_at", "updated_at",
        "parent_name", "child_name", "phone", "email",
        "ages_display", "allergies",
        "has_formula_display", "in_e_queue_display", "needs_pediatrist_display",
        "formats_display", "time_slots_display", "days_display",
        "expectations_display", "red_flags",
        "value_in_comm", "challenges", "lectures_interest",
        "interaction_formats", "parent_questions", "benefits",
    )

    fieldsets = (
        ("🗂 Обробка заявки", {
            "description": _section_desc(
                "Тут ви ведете заявку у роботі: змінюйте <b>статус</b>, лишайте "
                "<b>нотатки</b> для команди. Заявка автоматично позначається переглянутою, "
                "коли ви її відкриваєте."
            ),
            "fields": ("summary_card", "status", "is_read", "admin_notes",
                       ("created_at", "updated_at")),
        }),
        ("📞 Контакти", {
            "fields": (("parent_name", "child_name"), ("phone", "email")),
        }),
        ("1️⃣ Про дитину", {
            "fields": ("ages_display", "allergies",
                       "has_formula_display", "in_e_queue_display", "needs_pediatrist_display"),
        }),
        ("2️⃣ Графік відвідування", {
            "fields": ("formats_display", "time_slots_display", "days_display"),
        }),
        ("3️⃣ Очікування від простору", {
            "fields": ("expectations_display", "red_flags"),
        }),
        ("4️⃣ Про батьків", {
            "fields": ("value_in_comm", "challenges", "lectures_interest",
                       "interaction_formats", "parent_questions"),
        }),
        ("5️⃣ Про підтримку", {
            "fields": ("benefits",),
        }),
    )

    # --- Колонки списку ---
    @admin.display(description="Вік дитини")
    def ages_short(self, obj):
        ages = obj.ages or []
        return ", ".join(ages) if ages else "—"

    # --- Поля-відображення (детальна картка) ---
    @admin.display(description="Вік дитини")
    def ages_display(self, obj):
        return _list_display(obj.ages)

    @admin.display(description="Формат перебування")
    def formats_display(self, obj):
        return _list_display(obj.formats)

    @admin.display(description="Часові проміжки")
    def time_slots_display(self, obj):
        return _list_display(obj.time_slots)

    @admin.display(description="Дні тижня")
    def days_display(self, obj):
        return _list_display(obj.days)

    @admin.display(description="Що найважливіше")
    def expectations_display(self, obj):
        return _list_display(obj.expectations)

    @admin.display(description="Дитяча суміш у раціоні")
    def has_formula_display(self, obj):
        return _yesno_display(obj.has_formula)

    @admin.display(description="Зареєстровані в е-черзі")
    def in_e_queue_display(self, obj):
        return _yesno_display(obj.in_e_queue)

    @admin.display(description="Потрібен періодичний педіатр")
    def needs_pediatrist_display(self, obj):
        return _yesno_display(obj.needs_pediatrist)

    @admin.display(description="Зведення")
    def summary_card(self, obj):
        if obj.pk is None:
            return "—"
        rows = [
            ("Статус", _status_badge(obj)),
            ("Дитина", escape(obj.child_name or "—")),
            ("Батьки", escape(obj.parent_name or "—")),
            ("Телефон", format_html('<a href="tel:{}">{}</a>', obj.phone or "", obj.phone or "—")),
            ("Вік", escape(", ".join(obj.ages or []) or "—")),
            ("Графік", escape(", ".join(obj.formats or []) or "—")),
        ]
        body = "".join(
            format_html(
                '<tr><td style="padding:4px 14px 4px 0;color:#64748b;white-space:nowrap;vertical-align:top;">{}</td>'
                '<td style="padding:4px 0;color:#0f172a;font-weight:600;">{}</td></tr>',
                label, value,
            )
            for label, value in rows
        )
        return mark_safe(
            '<div style="background:linear-gradient(135deg,#f0fdfa,#fef9ec);border:1px solid #99f6e4;'
            'border-radius:14px;padding:16px 20px;max-width:560px;">'
            f'<table style="border-collapse:collapse;font-size:14px;">{body}</table>'
            '</div>'
        )


# ============================================================================
#  📨 ПОВІДОМЛЕННЯ З КОНТАКТНОЇ ФОРМИ
# ============================================================================
@admin.register(ContactMessage)
class ContactMessageAdmin(RequestAdminBase):
    list_display = ("unread_dot", "name", "phone", "message_short", "status", "created_at")
    list_display_links = ("name",)
    search_fields = ("name", "phone", "message")
    ordering = ("-created_at",)

    csv_filename = "povidomlennya_poppins.csv"
    csv_columns = (
        ("Надійшло", lambda o: o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else ""),
        ("Статус", lambda o: o.get_status_display()),
        ("Ім'я", lambda o: o.name or ""),
        ("Телефон", lambda o: o.phone or ""),
        ("Повідомлення", lambda o: o.message or ""),
        ("Нотатки адміністратора", lambda o: o.admin_notes or ""),
    )

    readonly_fields = ("summary_card", "name", "phone", "message", "created_at", "updated_at")

    fieldsets = (
        ("🗂 Обробка повідомлення", {
            "description": _section_desc(
                "Запити з контактної форми сайту. Контактні дані лише для перегляду; "
                "ведіть статус і нотатки для команди."
            ),
            "fields": ("summary_card", "status", "is_read", "admin_notes",
                       ("created_at", "updated_at")),
        }),
        ("✉️ Повідомлення", {
            "fields": (("name", "phone"), "message"),
        }),
    )

    @admin.display(description="Повідомлення")
    def message_short(self, obj):
        text = obj.message or ""
        return (text[:60] + "…") if len(text) > 60 else text

    @admin.display(description="Зведення")
    def summary_card(self, obj):
        if obj.pk is None:
            return "—"
        return mark_safe(
            '<div style="background:linear-gradient(135deg,#f0fdfa,#fef9ec);border:1px solid #99f6e4;'
            'border-radius:14px;padding:16px 20px;max-width:560px;font-size:14px;">'
            f'<div style="margin-bottom:8px;">{_status_badge(obj)}</div>'
            f'<div style="color:#0f172a;font-weight:600;">{escape(obj.name or "—")} · '
            f'<a href="tel:{escape(obj.phone or "")}">{escape(obj.phone or "—")}</a></div>'
            f'<div style="color:#334155;margin-top:8px;white-space:pre-wrap;">{escape(obj.message or "")}</div>'
            '</div>'
        )


# ============================================================================
#  📞 КОНТАКТИ ТА СОЦМЕРЕЖІ
# ============================================================================
class SiteInfoForm(forms.ModelForm):
    """Форма контактів з «нормальним» полем телефону (tel + підказка-маска)."""
    class Meta:
        model = SiteInfo
        fields = "__all__"
        widgets = {
            "phone": forms.TextInput(attrs={
                "type": "tel",
                "inputmode": "tel",
                "placeholder": "+38 (097) 123-45-67",
                "pattern": r"[\d\s()+\-]{7,25}",
                "title": "Лише цифри, пробіли та + ( ) -",
                "style": "max-width:280px;",
            }),
        }


@admin.register(SiteInfo)
class SiteInfoAdmin(SingletonAdmin):
    form = SiteInfoForm
    readonly_fields = ("logo_navbar_preview", "logo_footer_preview")

    fieldsets = (
        ("📞 Контактні дані", {
            "description": _section_desc(
                "Це інформація, яку бачать відвідувачі сайту: телефон, email, адреса. "
                "При натисканні на телефон — буде дзвінок. На email — відкриється поштова програма. "
                "На адресу — Google Maps.<br><br>"
                "У поле «Посилання на карту» вставте код <b>src</b> з iframe Google Maps "
                "(або повний &lt;iframe …&gt; — система сама витягне URL)."
            ),
            "fields": ("phone", "email", "address", "map_url"),
        }),
        ("🌐 Соціальні мережі", {
            "description": _section_desc(
                "Залиште поле порожнім, якщо немає сторінки в цій соцмережі — і іконка не з'явиться на сайті. "
                "Введіть повне посилання, що починається з <code>https://</code>."
            ),
            "fields": ("facebook", "instagram", "telegram", "threads"),
        }),
        ("🖼 Логотипи", {
            "description": _section_desc(
                "<b>Логотип у шапці</b> — для світлого фону (з текстом, кольоровий).<br>"
                "<b>Логотип у футері</b> — для темного фону (бажано білий).<br>"
                "Підтримуються формати: PNG, JPG, WebP, SVG."
            ),
            "fields": ("logo_navbar", "logo_navbar_preview", "logo_footer", "logo_footer_preview"),
        }),
        ("🧭 Назва у шапці та кнопка", {
            "description": _section_desc(
                "Якщо логотип у шапці завантажений — назва текстом не показується (логотип вже містить її). "
                "Якщо логотипу немає — показується текст «Назва» з виділеним «Акцентом» іншим кольором."
            ),
            "fields": ("nav_brand", "nav_brand_accent", "nav_cta_text"),
        }),
        ("📄 Футер (низ сайту)", {
            "description": _section_desc(
                "Текст копірайту, що показується внизу сайту. Рік автоматично оновлюється."
            ),
            "fields": ("footer_copyright",),
        }),
    )

    @admin.display(description="Превʼю логотипу шапки")
    def logo_navbar_preview(self, obj):
        return _img_preview(obj.logo_navbar, max_h=60)

    @admin.display(description="Превʼю логотипу футера")
    def logo_footer_preview(self, obj):
        return _img_preview(obj.logo_footer, max_h=60)


# ============================================================================
#  📝 ТЕКСТИ РОЗДІЛІВ
# ============================================================================
@admin.register(PageText)
class PageTextAdmin(SingletonAdmin):
    readonly_fields = ("hero_image_preview",)

    fieldsets = (
        ("🏠 Головна сторінка (Hero)", {
            "description": _section_desc(
                "Це найперше що бачить відвідувач. Зверху — невеликий бейдж, потім великий заголовок з виділеним словом, "
                "потім опис.<br><br>"
                "У полі <b>«Виділене слово»</b> вкажіть слово з заголовку, яке буде підсвічено градієнтом. "
                "Наприклад: заголовок «Простір де зростає щастя», виділене — «щастя». Слово має бути в заголовку.<br><br>"
                "В описі можна писати кілька абзаців — розділяйте їх натисканням Enter."
            ),
            "fields": (
                "hero_badge", "hero_title", "hero_title_accent", "hero_desc",
                "hero_image", "hero_image_preview",
                "hero_btn_primary", "hero_btn_secondary", "hero_ai_btn_text",
                "hero_badge_value", "hero_badge_label",
            ),
        }),
        ("💡 Про нас", {
            "description": _section_desc(
                "Маленький заголовок зверху → великий заголовок → опис.<br>"
                "В <b>описі</b> розділяйте абзаци Enter'ом — перший виглядатиме як «цитата» з акцентом.<br>"
                "В <b>тезах</b> кожен пункт з нового рядка — вони з'являться у блоці справа з галочками "
                "(якщо порожньо — блок не показується)."
            ),
            "fields": ("about_kicker", "about_title", "about_desc", "about_highlights"),
        }),
        ("🎯 Напрямки розвитку — заголовки", {
            "description": _section_desc(
                "Лише заголовки секції. Самі картки напрямків редагуються у пункті «Напрямки розвитку»."
            ),
            "fields": ("directions_kicker", "directions_title"),
        }),
        ("🏛 Приміщення", {
            "description": _section_desc(
                "Текст ліворуч від каруселі фото приміщень. Підзаголовок виглядає як акцентна цитата. "
                "Опис розділяйте на абзаци Enter'ом.<br>"
                "Самі фото приміщень додаються окремо у пункті «Приміщення — слайди»."
            ),
            "fields": ("premises_title", "premises_subtitle", "premises_desc"),
        }),
        ("👶 Вікові групи — заголовки", {
            "description": _section_desc(
                "Лише заголовки секції. Самі групи редагуються у пункті «Вікові групи»."
            ),
            "fields": ("services_kicker", "services_title"),
        }),
        ("❓ FAQ — заголовок", {
            "description": _section_desc(
                "Заголовок секції з частими запитаннями. Самі питання — у пункті «Питання та відповіді»."
            ),
            "fields": ("faq_title",),
        }),
        ("✉️ Контактна форма — підписи", {
            "description": _section_desc(
                "Текст над контактною формою і напис на кнопці відправки."
            ),
            "fields": ("contact_form_title", "contact_form_btn"),
        }),
    )

    @admin.display(description="Превʼю Hero-фото")
    def hero_image_preview(self, obj):
        return _img_preview(obj.hero_image, max_h=180)


# ============================================================================
#  💡 ПРО НАС — КАРТКИ
# ============================================================================
@admin.register(AboutCard)
class AboutCardAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "icon", "color")
    list_display_links = ("title",)
    list_editable = ("order",)
    ordering = ("order",)

    fieldsets = (
        (None, {
            "description": _section_desc(
                "Три картки переваг у секції «Про нас». Можна додати ще або видалити. "
                "<b>Порядок</b> керує черговістю зліва направо (менше число — лівіше).<br>"
                "<b>Іконка</b> вибирається зі списку, <b>колір</b> задає тон фону картки."
            ),
            "fields": ("title", "text", "icon", "color", "order"),
        }),
    )


# ============================================================================
#  🎯 НАПРЯМКИ
# ============================================================================
@admin.register(DirectionCard)
class DirectionCardAdmin(admin.ModelAdmin):
    list_display = ("group", "order", "title", "icon", "color")
    list_display_links = ("title",)
    list_editable = ("order", "group")
    list_filter = ("group",)
    ordering = ("group", "order")

    fieldsets = (
        (None, {
            "description": _section_desc(
                "Картки напрямків розвитку. Розподілені на <b>2 ряди</b>:<br>"
                "• <b>Перший ряд</b>: картки зліва, карусель фото справа.<br>"
                "• <b>Другий ряд</b>: колаж 3 фото зліва, картки справа.<br>"
                "Можна додати кілька карток у кожен ряд (типово по 2)."
            ),
            "fields": ("title", "text", "icon", "color", "group", "order"),
        }),
    )


@admin.register(DirectionGalleryImage)
class DirectionGalleryImageAdmin(admin.ModelAdmin):
    list_display = ("order", "alt", "image_preview")
    list_display_links = ("alt",)
    list_editable = ("order",)
    ordering = ("order",)
    readonly_fields = ("image_preview_large",)

    fieldsets = (
        (None, {
            "description": _section_desc(
                "Фото для каруселі у <b>першому ряді</b> «Напрямків» (справа). "
                "Рекомендований формат — <b>16:9</b> (наприклад 1920×1080 px).<br>"
                "Можна додати скільки завгодно фото — вони циклічно прокручуватимуться."
            ),
            "fields": ("image", "image_preview_large", "alt", "order"),
        }),
    )

    @admin.display(description="Превʼю")
    def image_preview(self, obj):
        return _img_preview(obj.image, max_h=60)

    @admin.display(description="Превʼю")
    def image_preview_large(self, obj):
        return _img_preview(obj.image, max_h=180)


@admin.register(DirectionCollageImage)
class DirectionCollageImageAdmin(admin.ModelAdmin):
    list_display = ("position", "alt", "image_preview")
    list_display_links = ("position",)
    ordering = ("position",)
    readonly_fields = ("image_preview_large",)

    fieldsets = (
        (None, {
            "description": _section_desc(
                "Три фото колажу у <b>другому ряді</b> «Напрямків» (зліва).<br>"
                "• <b>Верхнє ліве велике</b> — портрет 1920×2880 (співвідношення 2:3, вертикальне)<br>"
                "• <b>Верхнє праве</b> — ландшафт 1920×1280 (співвідношення 3:2, горизонтальне)<br>"
                "• <b>Нижнє праве</b> — портрет 1920×2880<br>"
                "Завантажте всі 3 — інакше з'являться сірі плейсхолдери."
            ),
            "fields": ("position", "image", "image_preview_large", "alt"),
        }),
    )

    @admin.display(description="Превʼю")
    def image_preview(self, obj):
        return _img_preview(obj.image, max_h=80)

    @admin.display(description="Превʼю")
    def image_preview_large(self, obj):
        return _img_preview(obj.image, max_h=240)


# ============================================================================
#  🏛 ПРИМІЩЕННЯ — СЛАЙДИ
# ============================================================================
@admin.register(PremiseSlide)
class PremiseSlideAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "image_preview")
    list_display_links = ("title",)
    list_editable = ("order",)
    ordering = ("order",)
    readonly_fields = ("image_preview_large",)

    fieldsets = (
        (None, {
            "description": _section_desc(
                "Фотографії приміщень для каруселі у секції «Приміщення».<br>"
                "Рекомендований формат — <b>16:9</b> (відеоформат). Назва і опис показуються знизу на затемненому фоні.<br>"
                "Карусель автоматично прокручується кожні 5 секунд, користувач може смикати фото мишею/пальцем."
            ),
            "fields": ("title", "desc", "image", "image_preview_large", "order"),
        }),
    )

    @admin.display(description="Превʼю")
    def image_preview(self, obj):
        return _img_preview(obj.image, max_h=60)

    @admin.display(description="Превʼю")
    def image_preview_large(self, obj):
        return _img_preview(obj.image, max_h=200)


# ============================================================================
#  👶 ВІКОВІ ГРУПИ
# ============================================================================
@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "age", "is_popular_badge")
    list_display_links = ("title",)
    list_editable = ("order",)
    ordering = ("order",)

    fieldsets = (
        ("Основне", {
            "description": _section_desc(
                "Вікова група (наприклад «Ясельна група»). Поле <b>«Особливості»</b> — це маркований список: "
                "кожен пункт з нового рядка (наприклад: <code>5-разове харчування</code> Enter <code>Прогулянки щодня</code>)."
            ),
            "fields": ("title", "age", "desc", "features", "btn_text", "order"),
        }),
        ("Стиль", {
            "description": _section_desc(
                "Іконка зі списку та колір (бажано різні для кожної групи). Іконка показується у круглому блоці зверху картки."
            ),
            "fields": ("icon", "color"),
        }),
        ("Виділення «найпопулярніша»", {
            "description": _section_desc(
                "Якщо ввімкнено — картка отримає золоту обведення, бейдж зверху і трохи більший масштаб. "
                "Рекомендується вмикати тільки для однієї групи."
            ),
            "fields": ("is_popular", "popular_label"),
        }),
    )

    @admin.display(description="Виділена?")
    def is_popular_badge(self, obj):
        if obj.is_popular:
            return mark_safe('<span style="background:#fbbf24;color:#78350f;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;">★ ПОПУЛЯРНА</span>')
        return mark_safe('<span style="color:#94a3b8;">—</span>')


# ============================================================================
#  ❓ FAQ
# ============================================================================
@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ("order", "question")
    list_display_links = ("question",)
    list_editable = ("order",)
    ordering = ("order",)

    fieldsets = (
        (None, {
            "description": _section_desc(
                "Питання-відповіді показуються у 2 колонки. Відповідь розгортається при кліку на питання.<br>"
                "Можна додати скільки завгодно — головне сортуйте за допомогою поля <b>«Порядок»</b>."
            ),
            "fields": ("question", "answer", "order"),
        }),
    )


# Заголовки/брендинг адмінки задаються у PoppinsAdminSite (api/admin_site.py).
