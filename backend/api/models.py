"""
Моделі бази даних сайту «The Poppins Club».

Структура поділена на три логічні групи:

  ЗВЕРНЕННЯ (те, що приходить від відвідувачів — потребує реакції):
    • SurveyApplication — заявки з 6-крокової анкети /anketa
    • ContactMessage    — повідомлення з контактної форми

  КОНТЕНТ (те, що показується на сайті — редагується адміністратором):
    • SiteInfo, PageText                       — налаштування та тексти (singletons)
    • AboutCard, DirectionCard, ServiceGroup   — картки секцій
    • DirectionGalleryImage, DirectionCollageImage, PremiseSlide — фото
    • FAQItem                                  — питання-відповіді

Обидві групи звернень мають єдиний робочий процес обробки:
статус (status), позначку «прочитано» (is_read) та нотатки адміністратора
(admin_notes) — щоб адмінка була не «звалищем даних», а робочим інструментом.
"""

from django.core.validators import RegexValidator
from django.db import models

from .image_utils import optimize_image_field


class ImageOptimizedModel(models.Model):
    """
    Абстрактна база: після збереження автоматично стискає завантажені
    зображення (поля з IMAGE_FIELDS = {"назва_поля": максимальна_ширина}).
    """
    IMAGE_FIELDS = {}

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for field_name, max_width in self.IMAGE_FIELDS.items():
            optimize_image_field(getattr(self, field_name, None), max_width)


# Валідатор телефону: цифри, пробіли та + ( ) - ; від 7 до 25 символів.
# Не дає ввести літери чи випадковий текст у поле телефону.
PHONE_VALIDATOR = RegexValidator(
    regex=r"^[\d\s()+\-]{7,25}$",
    message="Введіть коректний номер: лише цифри, пробіли та символи + ( ) -. "
            "Наприклад: +38 (097) 123-45-67",
)


# ---------------------------------------------------------------------------
#  Спільні довідники
# ---------------------------------------------------------------------------

# Іконки для карток (співпадають з назвами Lucide React на фронті)
ICON_CHOICES = [
    ("ShieldCheck", "🛡 Щит (безпека)"),
    ("Palette", "🎨 Палітра (творчість)"),
    ("Smile", "🙂 Усмішка"),
    ("Heart", "❤️ Серце"),
    ("Star", "⭐ Зірка"),
    ("Brain", "🧠 Мозок"),
    ("Leaf", "🍃 Листок"),
    ("Activity", "📈 Активність"),
    ("BookOpen", "📖 Книга"),
    ("Baby", "👶 Малюк"),
    ("Sun", "☀️ Сонце"),
    ("Clock", "🕐 Годинник"),
    ("CheckCircle2", "✅ Галочка"),
]

# Кольорові схеми (співпадають з Tailwind-класами на фронті)
COLOR_CHOICES = [
    ("teal", "🩵 Бірюзовий"),
    ("amber", "🟡 Золотий"),
    ("rose", "🌸 Рожевий"),
    ("blue", "🔵 Синій"),
    ("green", "🟢 Зелений"),
    ("emerald", "💚 Смарагдовий"),
    ("slate", "⚪ Сірий"),
]

# Єдиний робочий процес обробки звернень
REQUEST_STATUS_CHOICES = [
    ("new", "🆕 Нова"),
    ("in_progress", "📞 В роботі"),
    ("contacted", "✅ Зв'язались"),
    ("enrolled", "🎉 Зараховано"),
    ("rejected", "🚫 Відмова"),
    ("archived", "📦 Архів"),
]


class RequestWorkflowModel(models.Model):
    """
    Абстрактна база для звернень (анкети, повідомлення).
    Дає однаковий робочий процес: статус, «прочитано», нотатки, дати.
    """
    status = models.CharField(
        "Статус обробки", max_length=20,
        choices=REQUEST_STATUS_CHOICES, default="new", db_index=True,
        help_text="Де зараз ця заявка у вашому процесі. Змінюйте по мірі роботи.",
    )
    is_read = models.BooleanField(
        "Переглянуто", default=False, db_index=True,
        help_text="Автоматично стає «так», коли ви відкриваєте заявку.",
    )
    admin_notes = models.TextField(
        "Нотатки адміністратора", blank=True, default="",
        help_text="Внутрішні нотатки для команди. Відвідувач їх НЕ бачить.",
    )
    created_at = models.DateTimeField("Надійшло", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Останнє оновлення", auto_now=True, null=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    @property
    def is_open(self):
        """Звернення «в роботі» — ще не закрите (не зараховано/відмова/архів)."""
        return self.status in ("new", "in_progress", "contacted")


# ===========================================================================
#  ЗВЕРНЕННЯ — Заявки з анкети
# ===========================================================================
class SurveyApplication(RequestWorkflowModel):
    # --- Контакти ---
    parent_name = models.CharField("Ім'я одного з батьків", max_length=100)
    child_name = models.CharField("Ім'я дитини", max_length=100)
    phone = models.CharField("Телефон", max_length=20, db_index=True)
    email = models.EmailField("Email", blank=True, null=True)

    # --- Крок 1: Про дитину ---
    ages = models.JSONField(
        "Вік дитини", default=list, blank=True,
        help_text="Список обраних вікових діапазонів (може бути кілька — для кількох дітей).",
    )
    allergies = models.TextField("Алергії", blank=True, default="")
    has_formula = models.BooleanField("Є дитяча суміш у раціоні", null=True, blank=True)
    in_e_queue = models.BooleanField("Зареєстровані в електронній черзі", null=True, blank=True)
    needs_pediatrist = models.BooleanField("Потрібен періодичний педіатр", null=True, blank=True)

    # --- Крок 2: Графік відвідування ---
    formats = models.JSONField("Формат перебування", default=list, blank=True)
    time_slots = models.JSONField("Часові проміжки", default=list, blank=True)
    days = models.JSONField("Дні тижня", default=list, blank=True)

    # --- Крок 3: Очікування від простору ---
    expectations = models.JSONField("Що найважливіше", default=list, blank=True)
    red_flags = models.TextField("«Червоні прапорці»", blank=True, default="")

    # --- Крок 4: Про батьків ---
    value_in_comm = models.TextField("Найцінніше у комунікації", blank=True, default="")
    challenges = models.TextField("Виклики у вихованні", blank=True, default="")
    lectures_interest = models.CharField("Інтерес до лекцій/онлайн-сесій", max_length=50, blank=True, default="")
    interaction_formats = models.CharField("Бажані формати взаємодії", max_length=200, blank=True, default="")
    parent_questions = models.TextField("Питання для обговорення", blank=True, default="")

    # --- Крок 5: Про підтримку ---
    benefits = models.CharField("Поінформованість про пільги", max_length=200, blank=True, default="")

    class Meta:
        verbose_name = "Заявка з анкети"
        verbose_name_plural = "Заявки з анкети"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"{self.child_name or '?'} (від {self.parent_name or '?'})"


# ===========================================================================
#  ЗВЕРНЕННЯ — Повідомлення з контактної форми
# ===========================================================================
class ContactMessage(RequestWorkflowModel):
    name = models.CharField("Ім'я", max_length=100)
    phone = models.CharField("Телефон", max_length=20, db_index=True)
    message = models.TextField("Повідомлення")

    class Meta:
        verbose_name = "Повідомлення"
        verbose_name_plural = "Повідомлення з форми"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"{self.name or '?'} — {self.phone or ''}"


# ===========================================================================
#  КОНТЕНТ — Налаштування та тексти
# ===========================================================================
class SiteInfo(models.Model):
    # Логотипи — це брендинг, тому НЕ стискаємо автоматично (на відміну від фото секцій).
    phone = models.CharField("Телефон", max_length=25, default="+38 (0362) 12-34-56",
                             validators=[PHONE_VALIDATOR],
                             help_text="Показується на сайті та клікається для дзвінка. "
                                       "Формат: +38 (097) 123-45-67.")
    email = models.EmailField("Email", default="zdo52@ukr.net",
                              help_text="Клікається для написання листа.")
    address = models.CharField("Адреса", max_length=200, default="м. Рівне, ЗДО №52")
    map_url = models.TextField("Посилання на карту (тільки URL з src iframe Google Maps, без [ ])", blank=True, default="")
    facebook = models.URLField("Посилання на Facebook", blank=True, default="")
    instagram = models.URLField("Посилання на Instagram", blank=True, default="")
    telegram = models.URLField("Посилання на Telegram", blank=True, default="")
    threads = models.URLField("Посилання на Threads", blank=True, default="")

    logo_navbar = models.ImageField("Логотип у шапці", upload_to="logo/", blank=True, null=True,
                                    help_text="Рекомендовано: логотип для світлого фону (з текстом)")
    logo_footer = models.ImageField("Логотип у футері", upload_to="logo/", blank=True, null=True,
                                    help_text="Рекомендовано: білий/світлий логотип для темного фону")

    nav_brand = models.CharField("Навігація: основна назва", max_length=50, default="ЗДО")
    nav_brand_accent = models.CharField("Навігація: виділена частина", max_length=50, default="№52")
    nav_cta_text = models.CharField("Навігація: текст кнопки", max_length=50, default="Заповнити анкету")

    footer_copyright = models.CharField("Футер: текст копірайту",
                                        max_length=300,
                                        default="Заклад дошкільної освіти №52 м. Рівного. Всі права захищено.")

    ga_measurement_id = models.CharField(
        "Google Analytics ID", max_length=20, blank=True, default="",
        help_text="Необов'язково. Вставте ваш GA4 ідентифікатор виду G-XXXXXXXXXX, "
                  "щоб увімкнути аналітику відвідувачів. Порожньо — аналітика вимкнена.",
    )

    class Meta:
        verbose_name = "Контакти та соцмережі"
        verbose_name_plural = "Контакти та соцмережі"

    def __str__(self):
        return "Головні контакти сайту"


class PageText(ImageOptimizedModel):
    IMAGE_FIELDS = {"hero_image": 1920}

    # Hero
    hero_badge = models.CharField("Головна: Тег зверху", max_length=100, default="Набір на 2026/2027 рік відкрито")
    hero_title = models.CharField("Головна: Заголовок", max_length=200, default="Простір де зростає щастя")
    hero_title_accent = models.CharField("Головна: Виділене слово в заголовку (виділяється кольором)",
                                         max_length=50, default="щастя",
                                         help_text="Це слово/фраза з заголовку буде підсвічено кольором")
    hero_desc = models.TextField(
        "Головна: Опис",
        default="Сучасний заклад дошкільної освіти у Рівному. Ми поєднуємо професійний догляд, безпеку та інноваційні методики для гармонійного розвитку вашого малюка.",
        help_text=(
            "Підказки оформлення:\n"
            "• Кожен абзац — з нового рядка (натисніть Enter).\n"
            "• Перший абзац буде великим виділеним 'лідом' з лівою бірюзовою рисочкою.\n"
            "• Щоб підкреслити важливе — обгорніть слово/фразу подвійними зірочками: **ваш текст**. "
            "Воно стане жирним і виділиться кольором.\n"
            "Приклад: «Сучасний заклад **дошкільної освіти** у Рівному»"
        ),
    )
    hero_image = models.ImageField("Головна: Фото", upload_to="hero/", blank=True, null=True)
    hero_btn_primary = models.CharField("Головна: Текст першої кнопки", max_length=50, default="Детальніше про нас")
    hero_btn_secondary = models.CharField("Головна: Текст другої кнопки", max_length=50, default="Контакти")
    hero_ai_btn_text = models.CharField("Головна: Текст кнопки ШІ", max_length=100, default="Є питання? Запитай ШІ-помічника")

    hero_badge_value = models.CharField("Головна: Бейдж - число", max_length=50, default="15+ років")
    hero_badge_label = models.CharField("Головна: Бейдж - підпис", max_length=100, default="Досвіду та любові")

    # About
    about_kicker = models.CharField("Про нас: Маленький заголовок зверху", max_length=100, default="Про наш садок")
    about_title = models.CharField("Про нас: Заголовок", max_length=200, default="Місце, де цікаво рости")
    about_desc = models.TextField("Про нас: Опис (кожен абзац з нового рядка)",
                                  default="ЗДО №52 — це інноваційний простір безпечного розвитку. Наша головна мета — формування умов для гармонійного зростання вихованців та підтримка батьків у адаптації дитини.",
                                  help_text="Розділіть на абзаци натисканням Enter. Кожен абзац буде окремим блоком тексту.")
    about_highlights = models.TextField("Про нас: Тези (необов'язково; кожна з нового рядка)",
                                        blank=True, default="",
                                        help_text="Короткі тези списком (з галочками). Кожна теза з нового рядка.")

    # Directions
    directions_kicker = models.CharField("Напрямки: Маленький заголовок", max_length=100, default="Розвиток")
    directions_title = models.CharField("Напрямки: Заголовок", max_length=200, default="Наші ключові напрямки")

    # Premises
    premises_title = models.CharField("Приміщення: Заголовок", max_length=100, default="Приміщення")
    premises_subtitle = models.CharField("Приміщення: Підзаголовок",
                                         max_length=300,
                                         default="Простір ЗДО №52: безпека та комфорт у кожній деталі.")
    premises_desc = models.TextField("Приміщення: Опис",
                                     default="Ми створили середовище, де сучасний дизайн поєднується з домашнім затишком. Кожне приміщення в нашому садку — це світлий та привітний простір, де малюки почуваються вільно та спокійно. Завдяки розумному плануванню, ігрові зони залишаються відкритими для активного руху.")

    # Services
    services_kicker = models.CharField("Групи: Маленький заголовок", max_length=100, default="Вікові групи")
    services_title = models.CharField("Групи: Заголовок", max_length=200, default="Оберіть свій формат")

    # FAQ
    faq_title = models.CharField("FAQ: Заголовок", max_length=200, default="Відповіді на часті питання")

    # Testimonials
    testimonials_kicker = models.CharField("Відгуки: Маленький заголовок", max_length=100, default="Відгуки")
    testimonials_title = models.CharField("Відгуки: Заголовок", max_length=200, default="Що кажуть батьки")

    # Contact
    contact_form_title = models.CharField("Контакти: Заголовок форми", max_length=100, default="Написати нам")
    contact_form_btn = models.CharField("Контакти: Текст кнопки", max_length=50, default="Відправити")

    class Meta:
        verbose_name = "Тексти розділів"
        verbose_name_plural = "Тексти розділів"

    def __str__(self):
        return "Тексти на сайті"


# ===========================================================================
#  КОНТЕНТ — Картки секцій
# ===========================================================================
class AboutCard(models.Model):
    title = models.CharField("Заголовок", max_length=100)
    text = models.TextField("Опис")
    icon = models.CharField("Іконка", max_length=30, choices=ICON_CHOICES, default="ShieldCheck")
    color = models.CharField("Колір", max_length=20, choices=COLOR_CHOICES, default="rose")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Картка «Про нас»"
        verbose_name_plural = "«Про нас» — картки переваг"

    def __str__(self):
        return self.title


DIRECTION_GROUP_CHOICES = [
    ("first", "Перший ряд (картки зліва, карусель фото 16:9 справа)"),
    ("second", "Другий ряд (колаж 3 фото зліва, картки справа)"),
]


class DirectionCard(models.Model):
    title = models.CharField("Заголовок", max_length=100)
    text = models.TextField("Опис")
    icon = models.CharField("Іконка", max_length=30, choices=ICON_CHOICES, default="Brain")
    color = models.CharField("Колір", max_length=20, choices=COLOR_CHOICES, default="blue")
    group = models.CharField("Ряд", max_length=10, choices=DIRECTION_GROUP_CHOICES, default="first")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["group", "order", "id"]
        verbose_name = "Напрямок розвитку"
        verbose_name_plural = "Напрямки: картки-тези"

    def __str__(self):
        return self.title


class DirectionGalleryImage(ImageOptimizedModel):
    """Фото для каруселі першого ряду 'Напрямки' (формат 16:9)."""
    IMAGE_FIELDS = {"image": 1920}
    image = models.ImageField("Фото (бажано 16:9)", upload_to="directions/")
    alt = models.CharField("Опис (alt)", max_length=200, blank=True, default="")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Фото каруселі (Напрямки, ряд 1)"
        verbose_name_plural = "Напрямки: фото каруселі (ряд 1)"

    def __str__(self):
        return f"Фото №{self.order}"


COLLAGE_POSITION_CHOICES = [
    (1, "Верхнє (портрет 1920×2880)"),
    (2, "Середнє (ландшафт 1920×1280)"),
    (3, "Нижнє (портрет 1920×2880)"),
]


class DirectionCollageImage(ImageOptimizedModel):
    """Фото колажу для другого ряду 'Напрямки' (3 фіксовані позиції)."""
    IMAGE_FIELDS = {"image": 1920}
    position = models.PositiveSmallIntegerField("Позиція", choices=COLLAGE_POSITION_CHOICES, unique=True)
    image = models.ImageField("Фото", upload_to="directions/")
    alt = models.CharField("Опис (alt)", max_length=200, blank=True, default="")

    class Meta:
        ordering = ["position"]
        verbose_name = "Фото колажу (Напрямки, ряд 2)"
        verbose_name_plural = "Напрямки: фото колажу (ряд 2)"

    def __str__(self):
        return self.get_position_display()


class PremiseSlide(ImageOptimizedModel):
    IMAGE_FIELDS = {"image": 1920}
    title = models.CharField("Заголовок слайду", max_length=100)
    desc = models.CharField("Короткий опис", max_length=300)
    image = models.ImageField("Фото", upload_to="premises/", blank=True, null=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Слайд приміщення"
        verbose_name_plural = "Приміщення — слайди (з фото)"

    def __str__(self):
        return self.title


class ServiceGroup(models.Model):
    title = models.CharField("Назва групи", max_length=100)
    age = models.CharField("Вік", max_length=50)
    desc = models.TextField("Опис")
    icon = models.CharField("Іконка", max_length=30, choices=ICON_CHOICES, default="Baby")
    color = models.CharField("Колір", max_length=20, choices=COLOR_CHOICES, default="teal")
    is_popular = models.BooleanField("Найпопулярніша (виділяється)", default=False)
    popular_label = models.CharField("Текст бейджу 'найпопулярніша'", max_length=50, default="Найпопулярніша")
    features = models.TextField("Особливості (кожна з нового рядка)",
                                default="5-разове харчування\nПрогулянки щодня\nВсі гуртки включено")
    btn_text = models.CharField("Текст кнопки", max_length=50, default="Обрати групу")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Вікова група"
        verbose_name_plural = "Вікові групи"

    def __str__(self):
        return self.title


class FAQItem(models.Model):
    question = models.CharField("Питання", max_length=255)
    answer = models.TextField("Відповідь")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Питання (FAQ)"
        verbose_name_plural = "Питання та відповіді (FAQ)"

    def __str__(self):
        return self.question


class Testimonial(ImageOptimizedModel):
    """Відгук батьків — секція соціального доказу на сайті."""
    IMAGE_FIELDS = {"photo": 400}

    author_name = models.CharField("Ім'я автора", max_length=100)
    relation = models.CharField("Хто це (напр. «мама Софійки»)", max_length=100, blank=True, default="")
    text = models.TextField("Текст відгуку")
    photo = models.ImageField("Фото (необов'язково)", upload_to="testimonials/", blank=True, null=True)
    rating = models.PositiveSmallIntegerField(
        "Оцінка", default=5, choices=[(i, "★" * i) for i in range(1, 6)],
    )
    is_published = models.BooleanField("Опубліковано на сайті", default=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "-id"]
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки батьків"

    def __str__(self):
        return f"{self.author_name} ({self.relation})" if self.relation else self.author_name


class TelegramSubscriber(models.Model):
    """
    Хто отримує сповіщення про нові заявки в Telegram.
    Запис створюється автоматично, коли адміністратор надсилає боту /start.
    """
    chat_id = models.CharField("Chat ID", max_length=32, unique=True)
    name = models.CharField("Ім'я у Telegram", max_length=150, blank=True, default="")
    is_active = models.BooleanField("Отримує сповіщення", default=True)
    created_at = models.DateTimeField("Підписався", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Telegram-підписник"
        verbose_name_plural = "Telegram-сповіщення"

    def __str__(self):
        return self.name or self.chat_id
