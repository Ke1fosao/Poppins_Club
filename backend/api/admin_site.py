"""
Кастомний AdminSite для «The Poppins Club».

Django типово показує ВСІ моделі застосунку одним безликим блоком (тут — «API»).
Цей клас перегруповує їх у зрозумілі тематичні секції бічного меню:

    📥 Звернення від батьків   — заявки й повідомлення (щоденна робота)
    ⚙️ Налаштування та тексти  — контакти, соцмережі, тексти всіх секцій
    🏠 Секції головної сторінки — картки, напрямки, фото, групи, FAQ

Порядок секцій і моделей у них — фіксований (не алфавітний), тож усе завжди
«на своїх місцях».
"""

from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


# (Назва секції, [object_name моделей у потрібному порядку])
ADMIN_SECTIONS = [
    ("📥 Звернення від батьків", [
        "SurveyApplication",
        "ContactMessage",
    ]),
    ("⚙️ Налаштування та тексти", [
        "SiteInfo",
        "PageText",
    ]),
    ("🏠 Секції головної сторінки", [
        "AboutCard",
        "DirectionCard",
        "DirectionGalleryImage",
        "DirectionCollageImage",
        "PremiseSlide",
        "ServiceGroup",
        "FAQItem",
    ]),
]


class PoppinsAdminSite(AdminSite):
    site_header = "🌿 The Poppins Club — панель керування"
    site_title = "Адмінка The Poppins Club"
    index_title = "Що змінюємо сьогодні?"
    empty_value_display = "—"
    site_url = "/"

    def get_app_list(self, request, app_label=None):
        """Перегруповуємо моделі застосунку `api` у тематичні секції."""
        app_list = super().get_app_list(request, app_label)

        # Сторінка конкретного застосунку (/admin/api/) — лишаємо як є.
        if app_label:
            return app_list

        api_models = {}
        api_url = "/admin/"
        other_apps = []
        for app in app_list:
            if app["app_label"] == "api":
                api_url = app.get("app_url", api_url)
                for model in app["models"]:
                    api_models[model["object_name"]] = model
            else:
                other_apps.append(app)

        # Нічого не перегруповуємо, якщо застосунку api немає (напр. бракує прав).
        if not api_models:
            return app_list

        sections = []
        placed = set()
        for name, object_names in ADMIN_SECTIONS:
            models = [api_models[o] for o in object_names if o in api_models]
            if not models:
                continue
            placed.update(o for o in object_names if o in api_models)
            sections.append({
                "name": name,
                "app_label": "api",
                "app_url": api_url,
                "has_module_perms": True,
                "models": models,
            })

        # Будь-яка модель, яку забули внести в секцію, не зникне.
        leftovers = [m for o, m in api_models.items() if o not in placed]
        if leftovers:
            sections.append({
                "name": "Інше",
                "app_label": "api",
                "app_url": api_url,
                "has_module_perms": True,
                "models": leftovers,
            })

        # Спершу наші секції, потім решта (Користувачі/Групи Django).
        return sections + other_apps


class PoppinsAdminConfig(AdminConfig):
    """Робить PoppinsAdminSite типовим admin-сайтом проєкту."""
    default_site = "api.admin_site.PoppinsAdminSite"
