from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    ContactMessage, SurveyApplication,
    SiteInfo, PageText, FAQItem,
    AboutCard, DirectionCard, DirectionGalleryImage, DirectionCollageImage,
    PremiseSlide, ServiceGroup,
)


# ============================================================================
#  Хелпери
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


class SingletonAdmin(admin.ModelAdmin):
    """Не дає створити більше одного запису або видалити його."""
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================================
#  📞 КОНТАКТИ ТА СОЦМЕРЕЖІ
# ============================================================================
@admin.register(SiteInfo)
class SiteInfoAdmin(SingletonAdmin):
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

    def logo_navbar_preview(self, obj):
        return _img_preview(obj.logo_navbar, max_h=60)
    logo_navbar_preview.short_description = "Превʼю логотипу шапки"

    def logo_footer_preview(self, obj):
        return _img_preview(obj.logo_footer, max_h=60)
    logo_footer_preview.short_description = "Превʼю логотипу футера"


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
                "Лише заголовки секції. Самі картки напрямків редагуються у пункті «Напрямки розвитку — картки»."
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
                "Заголовок секції з частими запитаннями. Самі питання — у пункті «Питання та Відповіді»."
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

    def hero_image_preview(self, obj):
        return _img_preview(obj.hero_image, max_h=180)
    hero_image_preview.short_description = "Превʼю Hero-фото"


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

    def image_preview(self, obj):
        return _img_preview(obj.image, max_h=60)
    image_preview.short_description = "Превʼю"

    def image_preview_large(self, obj):
        return _img_preview(obj.image, max_h=180)
    image_preview_large.short_description = "Превʼю"


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

    def image_preview(self, obj):
        return _img_preview(obj.image, max_h=80)
    image_preview.short_description = "Превʼю"

    def image_preview_large(self, obj):
        return _img_preview(obj.image, max_h=240)
    image_preview_large.short_description = "Превʼю"


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

    def image_preview(self, obj):
        return _img_preview(obj.image, max_h=60)
    image_preview.short_description = "Превʼю"

    def image_preview_large(self, obj):
        return _img_preview(obj.image, max_h=200)
    image_preview_large.short_description = "Превʼю"


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

    def is_popular_badge(self, obj):
        if obj.is_popular:
            return mark_safe('<span style="background:#fbbf24;color:#78350f;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;">★ ПОПУЛЯРНА</span>')
        return mark_safe('<span style="color:#94a3b8;">—</span>')
    is_popular_badge.short_description = "Виділена?"


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


# ============================================================================
#  📨 ПОВІДОМЛЕННЯ З САЙТУ
# ============================================================================
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "phone", "message_short")
    list_display_links = ("name",)
    readonly_fields = ("name", "phone", "message", "created_at")
    date_hierarchy = "created_at"
    search_fields = ("name", "phone", "message")
    ordering = ("-created_at",)

    fieldsets = (
        ("Повідомлення", {
            "description": _section_desc(
                "Запити з контактної форми сайту. Дані тільки для перегляду — редагувати їх немає сенсу."
            ),
            "fields": ("created_at", "name", "phone", "message"),
        }),
    )

    def message_short(self, obj):
        text = obj.message or ""
        return (text[:60] + "…") if len(text) > 60 else text
    message_short.short_description = "Повідомлення"

    def has_add_permission(self, request):
        return False


# ============================================================================
#  📋 АНКЕТИ
# ============================================================================
@admin.register(SurveyApplication)
class SurveyApplicationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "child_name", "parent_name", "phone", "age_group")
    list_display_links = ("child_name",)
    readonly_fields = (
        "created_at",
        "child_name", "parent_name", "phone", "email",
        "age_group", "allergies", "formula", "e_queue", "pediatrist",
        "format", "time_slots", "days",
        "expectations", "red_flags",
        "value_in_comm", "challenges", "lectures_interest", "interaction_formats", "parent_questions",
        "benefits",
    )
    date_hierarchy = "created_at"
    search_fields = ("child_name", "parent_name", "phone", "email")
    ordering = ("-created_at",)

    fieldsets = (
        ("Дата подачі", {
            "description": _section_desc("Час, коли батьки відправили анкету."),
            "fields": ("created_at",),
        }),
        ("📞 Контакти", {
            "fields": ("parent_name", "child_name", "phone", "email"),
        }),
        ("Крок 1: Про дитину", {
            "fields": ("age_group", "allergies", "formula", "e_queue", "pediatrist"),
        }),
        ("Крок 2: Графік", {
            "fields": ("format", "time_slots", "days"),
        }),
        ("Крок 3: Очікування", {
            "fields": ("expectations", "red_flags"),
        }),
        ("Крок 4: Про батьків", {
            "fields": ("value_in_comm", "challenges", "lectures_interest", "interaction_formats", "parent_questions"),
        }),
        ("Крок 5: Підтримка", {
            "fields": ("benefits",),
        }),
    )

    def has_add_permission(self, request):
        return False


# ============================================================================
#  Заголовки адмінки (динамічно — підтягують назву з налаштувань)
# ============================================================================
def _get_brand_title():
    try:
        info = SiteInfo.objects.first()
        if info:
            return f"{info.nav_brand} {info.nav_brand_accent}".strip()
    except Exception:
        pass
    return "Сайт садочка"


admin.site.site_header = "🌱 Адмін-панель сайту"
admin.site.site_title = "Адмінка"
admin.site.index_title = "Керування контентом сайту"
admin.site.empty_value_display = "—"
