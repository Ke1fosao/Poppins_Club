import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import (
    ContactMessage, SurveyApplication,
    SiteInfo, PageText, FAQItem,
    AboutCard, DirectionCard, DirectionGalleryImage, DirectionCollageImage,
    PremiseSlide, ServiceGroup,
)


def _abs_url(request, fieldfile):
    if not fieldfile:
        return ""
    try:
        return request.build_absolute_uri(fieldfile.url)
    except Exception:
        return ""


# Дістає коректний URL з різних форматів, що могли потрапити з адмінки:
#   - повний <iframe src="..."> ... </iframe>
#   - markdown-посилання [text](url)
#   - чистий URL
_IFRAME_SRC_RE = re.compile(r'''src\s*=\s*["']([^"']+)["']''', re.IGNORECASE)
_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _clean_url(url):
    if not url:
        return ""
    url = url.strip()
    # 1) Якщо це HTML-фрагмент із iframe — дістаємо src
    if "<iframe" in url.lower():
        m = _IFRAME_SRC_RE.search(url)
        if m:
            return m.group(1).strip()
    # 2) Markdown-посилання
    m = _MD_LINK_RE.search(url)
    if m:
        return m.group(1).strip()
    return url


@api_view(['GET'])
def get_site_content(request):
    info = SiteInfo.objects.first() or SiteInfo.objects.create()
    text = PageText.objects.first() or PageText.objects.create()

    about_cards = AboutCard.objects.all()
    directions = DirectionCard.objects.all()
    directions_first = [d for d in directions if d.group == "first"]
    directions_second = [d for d in directions if d.group == "second"]
    gallery_images = DirectionGalleryImage.objects.all()
    collage_images = DirectionCollageImage.objects.all().order_by("position")
    premises = PremiseSlide.objects.all()
    services = ServiceGroup.objects.all()
    faqs = FAQItem.objects.all()

    def card_dict(c):
        return {"title": c.title, "text": c.text, "icon": c.icon, "color": c.color}

    data = {
        "settings": {
            "phone": info.phone,
            "email": info.email,
            "address": info.address,
            "map_url": _clean_url(info.map_url),
            "facebook": info.facebook,
            "instagram": info.instagram,
            "youtube": info.youtube,
            "logo_navbar": _abs_url(request, info.logo_navbar),
            "logo_footer": _abs_url(request, info.logo_footer),
            "nav_brand": info.nav_brand,
            "nav_brand_accent": info.nav_brand_accent,
            "nav_cta_text": info.nav_cta_text,
            "footer_copyright": info.footer_copyright,
        },
        "content": {
            "hero_badge": text.hero_badge,
            "hero_title": text.hero_title,
            "hero_title_accent": text.hero_title_accent,
            "hero_desc": text.hero_desc,
            "hero_image": _abs_url(request, text.hero_image),
            "hero_btn_primary": text.hero_btn_primary,
            "hero_btn_secondary": text.hero_btn_secondary,
            "hero_ai_btn_text": text.hero_ai_btn_text,
            "hero_badge_value": text.hero_badge_value,
            "hero_badge_label": text.hero_badge_label,

            "about_kicker": text.about_kicker,
            "about_title": text.about_title,
            "about_desc": text.about_desc,
            "about_highlights": [h.strip() for h in (text.about_highlights or "").splitlines() if h.strip()],

            "directions_kicker": text.directions_kicker,
            "directions_title": text.directions_title,

            "premises_title": text.premises_title,
            "premises_subtitle": text.premises_subtitle,
            "premises_desc": text.premises_desc,

            "services_kicker": text.services_kicker,
            "services_title": text.services_title,

            "faq_title": text.faq_title,

            "contact_form_title": text.contact_form_title,
            "contact_form_btn": text.contact_form_btn,
        },
        "about_cards": [
            {"title": c.title, "text": c.text, "icon": c.icon, "color": c.color}
            for c in about_cards
        ],
        "directions_first": [card_dict(d) for d in directions_first],
        "directions_second": [card_dict(d) for d in directions_second],
        "directions_gallery": [
            {"url": _abs_url(request, g.image), "alt": g.alt}
            for g in gallery_images if g.image
        ],
        "directions_collage": [
            {"position": c.position, "url": _abs_url(request, c.image), "alt": c.alt}
            for c in collage_images if c.image
        ],
        "premises": [
            {
                "title": p.title,
                "desc": p.desc,
                "image": _abs_url(request, p.image),
            }
            for p in premises
        ],
        "services": [
            {
                "title": s.title,
                "age": s.age,
                "desc": s.desc,
                "icon": s.icon,
                "color": s.color,
                "is_popular": s.is_popular,
                "popular_label": s.popular_label,
                "features": [f.strip() for f in s.features.splitlines() if f.strip()],
                "btn_text": s.btn_text,
            }
            for s in services
        ],
        "faqs": [{"q": f.question, "a": f.answer} for f in faqs],
    }
    return Response(data)


import time as _time
from rest_framework import status as _http

# Простий in-memory rate-limit по IP: не більше N відправок за TTL секунд
_RL_TTL = 60          # вікно, сек
_RL_LIMIT = 3         # максимум подач у вікні
_rate_log = {}        # {ip: [timestamps]}


def _rate_limited(ip):
    now = _time.time()
    log = [t for t in _rate_log.get(ip, []) if now - t < _RL_TTL]
    if len(log) >= _RL_LIMIT:
        _rate_log[ip] = log
        return True
    log.append(now)
    _rate_log[ip] = log
    return False


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


@api_view(['POST'])
def submit_contact(request):
    data = request.data

    # 1) Ханіпот: бот заповнить це поле — людина ні
    if (data.get('website') or '').strip():
        # Тихо «успіх», щоб бот не дізнався
        return Response({'status': 'ok'})

    # 2) Час заповнення: якщо < 2 сек, це не людина
    started_at = data.get('startedAt')
    if started_at:
        try:
            elapsed_ms = int(_time.time() * 1000) - int(started_at)
            if elapsed_ms < 2000:
                return Response({'status': 'ok'})
        except (TypeError, ValueError):
            pass

    # 3) Rate-limit по IP
    ip = _client_ip(request)
    if ip and _rate_limited(ip):
        return Response(
            {'error': 'Забагато спроб. Спробуйте через хвилину.'},
            status=_http.HTTP_429_TOO_MANY_REQUESTS,
        )

    # 4) Жорстка валідація обовʼязкових полів (на випадок, якщо фронт обійшов)
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    message = (data.get('message') or '').strip()
    consent = bool(data.get('consent'))

    errors = {}
    if len(name) < 2:
        errors['name'] = "Вкажіть імʼя (мінімум 2 символи)."
    elif len(name) > 100:
        errors['name'] = "Імʼя занадто довге."

    phone_digits = ''.join(ch for ch in phone if ch.isdigit())
    if len(phone_digits) < 7:
        errors['phone'] = "Вкажіть коректний телефон."
    elif len(phone_digits) > 20:
        errors['phone'] = "Телефон занадто довгий."

    if len(message) < 5:
        errors['message'] = "Опишіть запитання детальніше (мін. 5 символів)."
    elif len(message) > 2000:
        errors['message'] = "Повідомлення занадто довге (макс. 2000 символів)."

    # Грубий фільтр спаму: купа посилань / однотипний символ
    msg_lower = message.lower()
    if msg_lower.count("http") > 2 or "viagra" in msg_lower or "casino" in msg_lower:
        return Response({'error': 'Повідомлення розпізнано як спам.'}, status=_http.HTTP_400_BAD_REQUEST)

    if not consent:
        errors['consent'] = "Потрібна згода на обробку персональних даних."

    if errors:
        return Response({'errors': errors}, status=_http.HTTP_400_BAD_REQUEST)

    ContactMessage.objects.create(name=name, phone=phone, message=message)
    return Response({'status': 'Успішно відправлено'})


def _join(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v if str(x).strip())
    return str(v or "").strip()


@api_view(['POST'])
def submit_survey(request):
    data = request.data

    SurveyApplication.objects.create(
        # Контакти
        child_name=_join(data.get('childName'))[:100],
        parent_name=_join(data.get('parentName'))[:100],
        phone=_join(data.get('phone'))[:20],
        email=(data.get('email') or '').strip()[:254] or None,

        # Крок 1
        age_group=_join(data.get('ages') or data.get('age')),
        allergies=_join(data.get('allergies')),
        formula=_join(data.get('formula'))[:10],
        e_queue=_join(data.get('eQueue'))[:10],
        pediatrist=_join(data.get('pediatrist'))[:10],

        # Крок 2
        format=_join(data.get('formats') or data.get('format')),
        time_slots=_join(data.get('timeSlots')),
        days=_join(data.get('days')),

        # Крок 3
        expectations=_join(data.get('expectations')),
        red_flags=_join(data.get('redFlags')),

        # Крок 4
        value_in_comm=_join(data.get('valueInComm')),
        challenges=_join(data.get('challenges')),
        lectures_interest=_join(data.get('lecturesInterest'))[:50],
        interaction_formats=_join(data.get('interactionFormats'))[:200],
        parent_questions=_join(data.get('parentQuestions')),

        # Крок 5
        benefits=_join(data.get('benefits'))[:200],
    )
    return Response({'status': 'Анкету збережено'})
