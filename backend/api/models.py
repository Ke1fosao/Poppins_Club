from django.db import models


# --- Іконки для карток (співпадають з назвами Lucide React на фронті) ---
ICON_CHOICES = [
    ("ShieldCheck", "Щит (безпека)"),
    ("Palette", "Палітра (творчість)"),
    ("Smile", "Усмішка"),
    ("Heart", "Серце"),
    ("Star", "Зірка"),
    ("Brain", "Мозок"),
    ("Leaf", "Листок"),
    ("Activity", "Активність"),
    ("BookOpen", "Книга"),
    ("Baby", "Малюк"),
    ("Sun", "Сонце"),
    ("Clock", "Годинник"),
    ("CheckCircle2", "Галочка"),
]

# --- Кольорові схеми (співпадають з Tailwind класами на фронті) ---
COLOR_CHOICES = [
    ("teal", "Бірюзовий"),
    ("amber", "Золотий"),
    ("rose", "Рожевий"),
    ("blue", "Синій"),
    ("green", "Зелений"),
    ("emerald", "Смарагдовий"),
    ("slate", "Сірий"),
]


class SiteInfo(models.Model):
    phone = models.CharField("Телефон", max_length=20, default="+38 (0362) 12-34-56")
    email = models.EmailField("Email", default="zdo52@ukr.net")
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

    class Meta:
        verbose_name = "Налаштування контактів"
        verbose_name_plural = "1. Контакти та Соцмережі"

    def __str__(self):
        return "Головні контакти сайту"


class PageText(models.Model):
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

    # Contact
    contact_form_title = models.CharField("Контакти: Заголовок форми", max_length=100, default="Написати нам")
    contact_form_btn = models.CharField("Контакти: Текст кнопки", max_length=50, default="Відправити")

    class Meta:
        verbose_name = "Тексти сторінок"
        verbose_name_plural = "2. Тексти розділів"

    def __str__(self):
        return "Тексти на сайті"


class AboutCard(models.Model):
    title = models.CharField("Заголовок", max_length=100)
    text = models.TextField("Опис")
    icon = models.CharField("Іконка", max_length=30, choices=ICON_CHOICES, default="ShieldCheck")
    color = models.CharField("Колір", max_length=20, choices=COLOR_CHOICES, default="rose")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Картка 'Про нас'"
        verbose_name_plural = "3. Про нас - картки (3 шт)"

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
        verbose_name = "Напрямок"
        verbose_name_plural = "4. Напрямки розвитку"

    def __str__(self):
        return self.title


class DirectionGalleryImage(models.Model):
    """Фото для каруселі першого ряду 'Напрямки' (формат 16:9)."""
    image = models.ImageField("Фото (бажано 16:9)", upload_to="directions/")
    alt = models.CharField("Опис (alt)", max_length=200, blank=True, default="")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Фото каруселі (Напрямки - ряд 1)"
        verbose_name_plural = "4а. Напрямки: фото каруселі (ряд 1)"

    def __str__(self):
        return f"Фото №{self.order}"


COLLAGE_POSITION_CHOICES = [
    (1, "Верхнє (портрет 1920×2880)"),
    (2, "Середнє (ландшафт 1920×1280)"),
    (3, "Нижнє (портрет 1920×2880)"),
]


class DirectionCollageImage(models.Model):
    """Фото колажу для другого ряду 'Напрямки' (3 фіксовані позиції)."""
    position = models.PositiveSmallIntegerField("Позиція", choices=COLLAGE_POSITION_CHOICES, unique=True)
    image = models.ImageField("Фото", upload_to="directions/")
    alt = models.CharField("Опис (alt)", max_length=200, blank=True, default="")

    class Meta:
        ordering = ["position"]
        verbose_name = "Фото колажу (Напрямки - ряд 2)"
        verbose_name_plural = "4б. Напрямки: фото колажу (ряд 2)"

    def __str__(self):
        return self.get_position_display()


class PremiseSlide(models.Model):
    title = models.CharField("Заголовок слайду", max_length=100)
    desc = models.CharField("Короткий опис", max_length=300)
    image = models.ImageField("Фото", upload_to="premises/", blank=True, null=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Слайд приміщення"
        verbose_name_plural = "5. Приміщення - слайди (з фото)"

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
        verbose_name_plural = "6. Вікові групи"

    def __str__(self):
        return self.title


class FAQItem(models.Model):
    question = models.CharField("Питання", max_length=255)
    answer = models.TextField("Відповідь")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Питання (FAQ)"
        verbose_name_plural = "7. Питання та Відповіді"

    def __str__(self):
        return self.question


# --- Старі моделі для Анкет та Повідомлень ---

class ContactMessage(models.Model):
    name = models.CharField("Ім'я", max_length=100)
    phone = models.CharField("Телефон", max_length=20)
    message = models.TextField("Повідомлення")
    created_at = models.DateTimeField("Дата відправки", auto_now_add=True)

    class Meta:
        verbose_name = "Повідомлення"
        verbose_name_plural = "Повідомлення з сайту"


class SurveyApplication(models.Model):
    # --- Контакти ---
    child_name = models.CharField("Ім'я дитини", max_length=100)
    parent_name = models.CharField("Ім'я одного з батьків", max_length=100)
    phone = models.CharField("Телефон", max_length=20)
    email = models.EmailField("Email", blank=True, null=True)

    # --- Крок 1: Про дитину ---
    age_group = models.CharField("Вік дитини (може бути декілька)", max_length=300, blank=True, default="")
    allergies = models.TextField("Алергії", blank=True, default="")
    formula = models.CharField("Чи є у раціоні дитяча суміш", max_length=10, blank=True, default="")
    e_queue = models.CharField("Електронна черга", max_length=10, blank=True, default="")
    pediatrist = models.CharField("Потреба у періодичному педіатрі", max_length=10, blank=True, default="")

    # --- Крок 2: Про графік відвідування ---
    format = models.CharField("Формат перебування (може бути декілька)", max_length=300, blank=True, default="")
    time_slots = models.CharField("Часові проміжки", max_length=500, blank=True, default="")
    days = models.CharField("Дні тижня", max_length=200, blank=True, default="")

    # --- Крок 3: Очікування від простору ---
    expectations = models.CharField("Що найважливіше", max_length=500, blank=True, default="")
    red_flags = models.TextField("«Червоні прапорці»", blank=True, default="")

    # --- Крок 4: Про вас ---
    value_in_comm = models.TextField("Найцінніше у комунікації з простором", blank=True, default="")
    challenges = models.TextField("Виклики у вихованні", blank=True, default="")
    lectures_interest = models.CharField("Інтерес до лекцій/онлайн-сесій", max_length=50, blank=True, default="")
    interaction_formats = models.CharField("Бажані формати взаємодії", max_length=200, blank=True, default="")
    parent_questions = models.TextField("Питання, які хочуть обговорити", blank=True, default="")

    # --- Крок 5: Про підтримку (legacy) ---
    benefits = models.CharField("Пільги (інформованість)", max_length=200, blank=True, default="")

    created_at = models.DateTimeField("Дата заявки", auto_now_add=True)

    class Meta:
        verbose_name = "Анкета"
        verbose_name_plural = "Анкети (Заявки)"
        ordering = ["-created_at"]
