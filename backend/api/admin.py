from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ContactMessage, SurveyApplication,
    SiteInfo, PageText, FAQItem,
    AboutCard, DirectionCard, DirectionGalleryImage, DirectionCollageImage,
    PremiseSlide, ServiceGroup,
)


class SingletonAdmin(admin.ModelAdmin):
    """Дозволяє створити лише один запис цього типу."""
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteInfo)
class SiteInfoAdmin(SingletonAdmin):
    fieldsets = (
        ("Контакти", {
            "fields": ("phone", "email", "address", "map_url"),
        }),
        ("Соцмережі", {
            "fields": ("facebook", "instagram", "youtube"),
        }),
        ("Логотипи", {
            "fields": ("logo_navbar", "logo_footer"),
        }),
        ("Шапка сайту (навігація)", {
            "fields": ("nav_brand", "nav_brand_accent", "nav_cta_text"),
        }),
        ("Футер", {
            "fields": ("footer_copyright",),
        }),
    )


@admin.register(PageText)
class PageTextAdmin(SingletonAdmin):
    fieldsets = (
        ("Головна (Hero)", {
            "fields": (
                "hero_badge", "hero_title", "hero_title_accent", "hero_desc",
                "hero_image", "hero_btn_primary", "hero_btn_secondary",
                "hero_ai_btn_text", "hero_badge_value", "hero_badge_label",
            ),
        }),
        ("Про нас", {
            "fields": ("about_kicker", "about_title", "about_desc", "about_highlights"),
        }),
        ("Напрямки розвитку", {
            "fields": ("directions_kicker", "directions_title"),
        }),
        ("Приміщення", {
            "fields": ("premises_title", "premises_subtitle", "premises_desc"),
        }),
        ("Вікові групи", {
            "fields": ("services_kicker", "services_title"),
        }),
        ("FAQ", {
            "fields": ("faq_title",),
        }),
        ("Контакти (форма)", {
            "fields": ("contact_form_title", "contact_form_btn"),
        }),
    )


@admin.register(AboutCard)
class AboutCardAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "icon", "color")
    list_display_links = ("title",)
    list_editable = ("order",)
    ordering = ("order",)


@admin.register(DirectionCard)
class DirectionCardAdmin(admin.ModelAdmin):
    list_display = ("group", "order", "title", "icon", "color")
    list_display_links = ("title",)
    list_editable = ("order", "group")
    list_filter = ("group",)
    ordering = ("group", "order")


@admin.register(DirectionGalleryImage)
class DirectionGalleryImageAdmin(admin.ModelAdmin):
    list_display = ("order", "alt", "image_preview")
    list_display_links = ("alt",)
    list_editable = ("order",)
    ordering = ("order",)
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:60px;border-radius:8px;" />', obj.image.url)
        return "—"
    image_preview.short_description = "Превʼю"


@admin.register(DirectionCollageImage)
class DirectionCollageImageAdmin(admin.ModelAdmin):
    list_display = ("position", "alt", "image_preview")
    list_display_links = ("position",)
    ordering = ("position",)
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:80px;border-radius:8px;" />', obj.image.url)
        return "—"
    image_preview.short_description = "Превʼю"


@admin.register(PremiseSlide)
class PremiseSlideAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "image_preview")
    list_display_links = ("title",)
    list_editable = ("order",)
    ordering = ("order",)
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:60px;border-radius:8px;" />', obj.image.url)
        return "—"
    image_preview.short_description = "Превʼю"


@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "age", "is_popular")
    list_display_links = ("title",)
    list_editable = ("order", "is_popular")
    ordering = ("order",)


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ("order", "question")
    list_display_links = ("question",)
    list_editable = ("order",)
    ordering = ("order",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at")
    readonly_fields = ("created_at",)


@admin.register(SurveyApplication)
class SurveyApplicationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "child_name", "parent_name", "phone", "age_group")
    list_display_links = ("child_name",)
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    search_fields = ("child_name", "parent_name", "phone", "email")
    fieldsets = (
        ("Дата подачі", {"fields": ("created_at",)}),
        ("Контакти", {"fields": ("parent_name", "child_name", "phone", "email")}),
        ("Крок 1: Про дитину", {"fields": ("age_group", "allergies", "formula", "e_queue", "pediatrist")}),
        ("Крок 2: Графік", {"fields": ("format", "time_slots", "days")}),
        ("Крок 3: Очікування", {"fields": ("expectations", "red_flags")}),
        ("Крок 4: Про батьків", {"fields": ("value_in_comm", "challenges", "lectures_interest", "interaction_formats", "parent_questions")}),
        ("Крок 5: Підтримка", {"fields": ("benefits",)}),
    )


admin.site.site_header = "Адмін-панель ЗДО №52"
admin.site.site_title = "ЗДО №52"
admin.site.index_title = "Керування контентом сайту"
