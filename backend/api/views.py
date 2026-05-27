import os
import re
import requests as gemini_http
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as _http_status
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
            "telegram": info.telegram,
            "threads": info.threads,
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


# ============================================================================
#  AI Chat Proxy — фронт нічого не знає про Gemini, ключ живе тут у env var
# ============================================================================

# Free-tier-friendly моделі. Послідовність: спершу найвища квота, потім fallback.
# Жодних preview/experimental — вони непостійні.
GEMINI_MODELS = [
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash",
    "models/gemini-flash-latest",
]

# Якщо помилка від Gemini містить одне з цих слів — пробуємо наступну модель
_RETRYABLE_PATTERNS = re.compile(
    r"quota|resource_exhausted|exceeded|limit:\s*0|not[_ ]found|"
    r"no longer available|not supported|deprecated|unavailable",
    re.IGNORECASE,
)


def _build_ai_context():
    """Збирає повний контекст про садочок із БД для системної інструкції."""
    info = SiteInfo.objects.first()
    text = PageText.objects.first()
    if not info or not text:
        return "Ти — віртуальний помічник дитячого садочка."

    brand = f"{info.nav_brand or ''} {info.nav_brand_accent or ''}".strip() or "садочок"

    lines = [
        f'Ти — привітний віртуальний помічник дитячого садочка "{brand}" у м. Рівне, Україна.',
        "",
        "═══ ВСЯ ІНФОРМАЦІЯ ПРО САДОЧОК ═══",
        "",
        "КОНТАКТИ:",
        f"- Назва: {brand}",
        f"- Телефон: {info.phone or '—'}",
        f"- Email: {info.email or '—'}",
        f"- Адреса: {info.address or '—'}",
        f"- Facebook: {info.facebook or '—'}",
        f"- Instagram: {info.instagram or '—'}",
        f"- Telegram: {info.telegram or '—'}",
        f"- Threads: {info.threads or '—'}",
        "",
        "ГОЛОВНА СТОРІНКА:",
        f"- Слоган: «{text.hero_title or ''}»",
        f"- Тег: {text.hero_badge or ''}",
        f"- Опис: {text.hero_desc or ''}",
        f"- Досвід: {text.hero_badge_value or ''} — {text.hero_badge_label or ''}",
        "",
        f"ПРО САДОЧОК ({text.about_title or ''}):",
        text.about_desc or "",
        "",
    ]

    highlights = [h.strip() for h in (text.about_highlights or "").splitlines() if h.strip()]
    if highlights:
        lines.append("Тези про садочок:")
        for h in highlights:
            lines.append(f"- {h}")
        lines.append("")

    cards = AboutCard.objects.all()
    if cards.exists():
        lines.append("ПЕРЕВАГИ:")
        for c in cards:
            lines.append(f"- {c.title}: {c.text}")
        lines.append("")

    directions = DirectionCard.objects.all()
    if directions.exists():
        lines.append(f"НАПРЯМКИ РОЗВИТКУ ({text.directions_title or ''}):")
        for d in directions:
            lines.append(f"- {d.title}: {d.text}")
        lines.append("")

    services = ServiceGroup.objects.all()
    if services.exists():
        lines.append(f"ВІКОВІ ГРУПИ ({text.services_title or ''}):")
        for s in services:
            features = [f.strip() for f in (s.features or "").splitlines() if f.strip()]
            popular = " [найпопулярніша]" if s.is_popular else ""
            lines.append(f"• {s.title} (вік: {s.age}){popular}")
            lines.append(f"  {s.desc}")
            if features:
                lines.append(f"  Що включено: {'; '.join(features)}")
        lines.append("")

    if text.premises_title or text.premises_subtitle or text.premises_desc:
        lines.append(f"ПРИМІЩЕННЯ ({text.premises_title or ''}):")
        if text.premises_subtitle:
            lines.append(text.premises_subtitle)
        if text.premises_desc:
            lines.append(text.premises_desc)
        lines.append("")

    faqs = FAQItem.objects.all()
    if faqs.exists():
        lines.append("ЧАСТІ ЗАПИТАННЯ ТА ВІДПОВІДІ (FAQ):")
        for i, f in enumerate(faqs, 1):
            lines.append(f"{i}. Питання: {f.question}")
            lines.append(f"   Відповідь: {f.answer}")
        lines.append("")

    phone = info.phone or ""
    lines.extend([
        "═══ ІНСТРУКЦІЇ ═══",
        "1. Відповідай українською мовою, тепло й привітно. Помірно використовуй емодзі (1-3 на відповідь).",
        "2. Якщо питання збігається з FAQ — давай відповідь з FAQ, переформулювавши природно.",
        "3. Якщо є точна інформація вище — використовуй її. Не вигадуй ціни, прізвища, графіки.",
        f"4. Якщо інформації нема — кажи: «На жаль, цією деталлю я не володію. Зателефонуйте за номером {phone} — там точно допоможуть».",
        "5. Загальні питання про виховання/розвиток дітей — можеш відповідати як експерт стисло.",
        f"6. Якщо запитують «як записатись» — кажи: «Натисніть кнопку \"Заповнити анкету\" вгорі сторінки або зателефонуйте {phone}».",
        "7. Не на тему садочка / дітей — ввічливо переспрямуй.",
        "8. Тримай відповідь у межах 2-4 коротких речень, якщо тільки користувач не просить детальніше.",
    ])

    return "\n".join(lines)


@api_view(['POST'])
def submit_chat(request):
    """Проксі для Gemini. Ключ читається з env GEMINI_API_KEY (НІКОЛИ не з фронта)."""
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not api_key:
        return Response(
            {'error': 'AI-помічник тимчасово недоступний (API-ключ не налаштовано на сервері).'},
            status=_http_status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    data = request.data
    messages = data.get('messages') or []
    if not isinstance(messages, list) or not messages:
        return Response({'error': 'Порожнє повідомлення.'}, status=_http_status.HTTP_400_BAD_REQUEST)

    # Базова перевірка: останнє повідомлення — від користувача
    if messages[-1].get('role') == 'model':
        return Response({'error': 'Очікується повідомлення від користувача в кінці історії.'}, status=400)

    # Конвертуємо у формат Gemini
    contents = []
    for m in messages:
        role = 'model' if m.get('role') == 'model' else 'user'
        text = (m.get('text') or '').strip()
        if not text:
            continue
        contents.append({'role': role, 'parts': [{'text': text}]})

    if not contents:
        return Response({'error': 'Усі повідомлення порожні.'}, status=400)

    site_context = _build_ai_context()
    body = {
        'contents': contents,
        'systemInstruction': {'parts': [{'text': site_context}]},
        'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 600},
    }

    last_error_msg = ''
    last_error_status = ''
    last_retry_hint = ''
    tried = []

    for model in GEMINI_MODELS:
        tried.append(model)
        url = f'https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}'
        try:
            r = gemini_http.post(url, json=body, timeout=30)
            result = r.json()
        except gemini_http.exceptions.RequestException as e:
            last_error_msg = str(e)
            last_error_status = 'NETWORK_ERROR'
            continue
        except ValueError:
            last_error_msg = 'Invalid JSON from Gemini'
            last_error_status = 'PARSE_ERROR'
            continue

        # Успіх
        try:
            text = result['candidates'][0]['content']['parts'][0]['text']
            if text:
                return Response({'text': text, 'model': model})
        except (KeyError, IndexError, TypeError):
            pass

        err = result.get('error', {}) if isinstance(result, dict) else {}
        last_error_msg = err.get('message', 'невідома помилка')
        last_error_status = err.get('status', '')

        # Витягуємо «retry in X seconds» якщо є
        m = re.search(r'retry in ([\d.]+)s', last_error_msg, re.IGNORECASE)
        if m:
            secs = int(float(m.group(1)))
            if secs > 60:
                last_retry_hint = f' Спробуйте через {(secs + 59) // 60} хв.'
            else:
                last_retry_hint = f' Спробуйте через {secs} с.'

        # Ретраїмо лише квоту/недоступну модель — інше припиняє пошук
        if _RETRYABLE_PATTERNS.search(last_error_msg + ' ' + last_error_status):
            continue
        break

    # Усі моделі впали — формуємо дружнє повідомлення
    combined = (last_error_msg + ' ' + last_error_status).lower()
    if re.search(r'quota|resource_exhausted|exceeded|limit:\s*0', combined):
        header = f"Безкоштовна квота Gemini вичерпана для всіх моделей.{last_retry_hint}"
    elif re.search(r'permission_denied|forbidden|api[_ ]?key|invalid_argument', combined):
        header = "Проблема з API-ключем Gemini на сервері."
    else:
        header = "Не вдалося отримати відповідь від AI."

    return Response(
        {
            'error': header,
            'details': last_error_msg,
            'status': last_error_status,
            'tried': len(tried),
        },
        status=_http_status.HTTP_502_BAD_GATEWAY,
    )


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
