from django.db import migrations


ABOUT_CARDS = [
    {
        "title": "Абсолютна безпека",
        "text": "Власне облаштоване укриття, закрита територія та медичний супровід 24/7.",
        "icon": "ShieldCheck",
        "color": "rose",
        "order": 0,
    },
    {
        "title": "Творчий розвиток",
        "text": "Щоденні гуртки: малювання, музика, ліплення та LEGO-конструювання.",
        "icon": "Palette",
        "color": "amber",
        "order": 1,
    },
    {
        "title": "М'яка адаптація",
        "text": "Допомагаємо малюкам легко звикнути до садочка за підтримки психолога.",
        "icon": "Smile",
        "color": "teal",
        "order": 2,
    },
]

DIRECTIONS = [
    {
        "title": "Інтелектуальний фундамент",
        "text": "Програма базується на сучасних та доказових методах, що включають заняття з розвитку мовлення для збагачення словникового запасу. Логіко-математичний та сенсорний блоки допомагають малюкам опановувати поняття простору, форми й кількості.",
        "icon": "Brain",
        "color": "blue",
        "order": 0,
    },
    {
        "title": "Творча майстерня",
        "text": "Через малювання, ліплення та конструювання LEGO діти розвивають дрібну моторику та уяву. Музичні заняття додають ритму та допомагають емоційному розкриттю кожної дитини у нашому просторі.",
        "icon": "Palette",
        "color": "amber",
        "order": 1,
    },
    {
        "title": "Пізнання довкілля",
        "text": "Ми вчимо дітей взаємодіяти з соціумом та природою, формуючи перші уявлення про безпеку життєдіяльності. Щоденні прогулянки на власному майданчику інтегровані в освітній процес як активна дослідницька діяльність.",
        "icon": "Leaf",
        "color": "green",
        "order": 2,
    },
    {
        "title": "Здоров'я та активність",
        "text": "Щоденні заняття фізкультурою та елементи валеології допомагають зміцнювати імунітет та формувати правильні звички змалечку. Наша мета — створити безпечне та надихаюче середовище для здорового росту.",
        "icon": "Activity",
        "color": "rose",
        "order": 3,
    },
]

PREMISES = [
    {"title": "Зал групи", "desc": "Світлий та привітний простір для навчання та ігор.", "order": 0},
    {"title": "Роздягальня", "desc": "Зручні індивідуальні шафки та пуфи для комфорту малюків.", "order": 1},
    {"title": "Ігрова зона", "desc": "Безпечні іграшки та екологічні матеріали для вільного розвитку.", "order": 2},
]

SERVICES = [
    {
        "title": "Ясельна група",
        "age": "1.5 - 3 роки",
        "desc": "Особлива увага до м'якої адаптації, базових навичок самообслуговування та сенсорного розвитку.",
        "icon": "Baby",
        "color": "teal",
        "is_popular": False,
        "popular_label": "Найпопулярніша",
        "features": "5-разове харчування\nПрогулянки щодня\nВсі гуртки включено",
        "btn_text": "Обрати групу",
        "order": 0,
    },
    {
        "title": "Молодша та Середня",
        "age": "3 - 5 років",
        "desc": "Активне пізнання світу, розвиток мовлення, соціальна взаємодія та творчі майстер-класи.",
        "icon": "Sun",
        "color": "amber",
        "is_popular": True,
        "popular_label": "Найпопулярніша",
        "features": "5-разове харчування\nПрогулянки щодня\nВсі гуртки включено",
        "btn_text": "Обрати групу",
        "order": 1,
    },
    {
        "title": "Старша група",
        "age": "5 - 7 років",
        "desc": "Комплексна підготовка до школи, розвиток логіки, критичного мислення та емоційного інтелекту.",
        "icon": "BookOpen",
        "color": "rose",
        "is_popular": False,
        "popular_label": "Найпопулярніша",
        "features": "5-разове харчування\nПрогулянки щодня\nВсі гуртки включено",
        "btn_text": "Обрати групу",
        "order": 2,
    },
]

FAQS = [
    {
        "question": "Які документи потрібні для вступу?",
        "answer": "Медична довідка (форма 086-1/о), свідоцтво про народження дитини (копія), заява від батьків та направлення з електронної черги.",
        "order": 0,
    },
    {
        "question": "Як ви дбаєте про здоров'я та чистоту під час епідемій?",
        "answer": "Ми проводимо регулярне провітрювання, вологе прибирання, використовуємо бактерицидні рециркулятори повітря у групах. Щоранку медсестра проводить температурний скринінг.",
        "order": 1,
    },
    {
        "question": "Чи можливе індивідуальне меню при алергіях?",
        "answer": "Так, за наявності відповідної довідки від лікаря, ми розробляємо спеціальне дієтичне меню.",
        "order": 2,
    },
]


def seed(apps, schema_editor):
    AboutCard = apps.get_model("api", "AboutCard")
    DirectionCard = apps.get_model("api", "DirectionCard")
    PremiseSlide = apps.get_model("api", "PremiseSlide")
    ServiceGroup = apps.get_model("api", "ServiceGroup")
    FAQItem = apps.get_model("api", "FAQItem")
    SiteInfo = apps.get_model("api", "SiteInfo")
    PageText = apps.get_model("api", "PageText")

    if not AboutCard.objects.exists():
        for c in ABOUT_CARDS:
            AboutCard.objects.create(**c)

    if not DirectionCard.objects.exists():
        for c in DIRECTIONS:
            DirectionCard.objects.create(**c)

    if not PremiseSlide.objects.exists():
        for c in PREMISES:
            PremiseSlide.objects.create(**c)

    if not ServiceGroup.objects.exists():
        for c in SERVICES:
            ServiceGroup.objects.create(**c)

    if not FAQItem.objects.exists():
        for c in FAQS:
            FAQItem.objects.create(**c)

    if not SiteInfo.objects.exists():
        SiteInfo.objects.create()

    if not PageText.objects.exists():
        PageText.objects.create()


def unseed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_aboutcard_directioncard_premiseslide_servicegroup_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
