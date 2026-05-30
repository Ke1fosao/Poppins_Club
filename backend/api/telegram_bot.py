"""
Telegram-бот «The Poppins Club» — webhook-режим, без зовнішніх бібліотек.

Дві ролі:
  • БАТЬКИ (будь-хто, хто написав боту) — діляться контактом, ставлять запитання
    та лишають відгуки прямо з Telegram. Відгуки йдуть на модерацію.
  • АДМІНІСТРАТОРИ (is_admin=True, дозвіл надається в адмінці сайту) — отримують
    сповіщення про звернення й керують ними кнопками (зокрема статус «Архів»),
    модерують відгуки, бачать дії інших адмінів.

Захист від спаму: обов'язковий контакт перед поданням, кулдаун між поданнями,
обмеження довжини.
"""

import html
import os
import re
import time

import requests

_API = "https://api.telegram.org/bot{token}/{method}"
_TIMEOUT = 15

# Стани діалогу
ST_IDLE = "idle"
ST_QUESTION = "awaiting_question"
ST_REVIEW = "awaiting_review_text"

# Анти-спам
COOLDOWN_SECONDS = 30
MAX_QUESTION = 2000
MAX_REVIEW = 1000
MIN_TEXT = 5

# Підписи кнопок (reply-клавіатура) — звіряються у обробнику
BTN_QUESTION = "❓ Поставити запитання"
BTN_REVIEW = "🗣 Залишити відгук"
BTN_CONTACTS = "📞 Контакти садочка"
BTN_ANKETA = "📝 Записатися (анкета)"
BTN_STATS = "📊 Статистика"
BTN_NEW = "🆕 Нові заявки"
BTN_HELP = "❓ Довідка"
BTN_CANCEL = "✖️ Скасувати"
BTN_SHARE = "📱 Поділитися контактом"


# ==========================================================================
#  Конфіг
# ==========================================================================
def _token():
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def webhook_secret():
    return os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()


def _site_base_url():
    return os.environ.get("SITE_BASE_URL", "").strip().rstrip("/")


def _bootstrap_admin_ids():
    raw = os.environ.get("TELEGRAM_ALLOWED_IDS", "")
    return {x.strip() for x in re.split(r"[,\s]+", raw) if x.strip()}


def is_configured():
    return bool(_token())


# ==========================================================================
#  Низькорівневі виклики Bot API
# ==========================================================================
def _call(method, **payload):
    token = _token()
    if not token:
        return None
    try:
        r = requests.post(_API.format(token=token, method=method), json=payload, timeout=_TIMEOUT)
        return r.json()
    except Exception:
        return None


def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup is not None:
        data["reply_markup"] = reply_markup
    return _call("sendMessage", **data)


def answer_callback(callback_id, text=""):
    return _call("answerCallbackQuery", callback_query_id=callback_id, text=text)


def edit_message_text(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text,
            "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup is not None:
        data["reply_markup"] = reply_markup
    return _call("editMessageText", **data)


# ==========================================================================
#  Webhook-керування (manage.py telegram_webhook ...)
# ==========================================================================
def set_webhook(base_url):
    if not _token() or not webhook_secret():
        return {"ok": False, "description": "Не задано TELEGRAM_BOT_TOKEN / TELEGRAM_WEBHOOK_SECRET"}
    url = base_url.rstrip("/") + f"/api/telegram/{webhook_secret()}/"
    return _call("setWebhook", url=url,
                 allowed_updates=["message", "callback_query"],
                 drop_pending_updates=True)


def get_webhook_info():
    return _call("getWebhookInfo")


def delete_webhook():
    return _call("deleteWebhook", drop_pending_updates=True)


# ==========================================================================
#  Користувачі / ролі
# ==========================================================================
def _upsert_user(chat_id, frm):
    from .models import TelegramSubscriber
    name = (f"{frm.get('first_name', '')} {frm.get('last_name', '')}".strip()
            or frm.get("username", "") or "")
    username = frm.get("username", "") or ""
    user, _ = TelegramSubscriber.objects.get_or_create(chat_id=str(chat_id))
    changed = False
    if name and user.name != name:
        user.name, changed = name, True
    if username and user.username != username:
        user.username, changed = username, True
    # Бутстрап адміна через env (зручно для першого налаштування власником)
    if not user.is_admin and str(chat_id) in _bootstrap_admin_ids():
        user.is_admin, user.is_active, changed = True, True, True
    if changed:
        user.save()
    return user


def _is_admin(user):
    return bool(user and user.is_admin)


def _active_admin_chats(exclude=None):
    from .models import TelegramSubscriber
    qs = TelegramSubscriber.objects.filter(is_admin=True, is_active=True)
    return [c for c in qs.values_list("chat_id", flat=True) if str(c) != str(exclude)]


def _set_state(user, state, **data):
    user.state = state
    sd = dict(user.state_data or {})
    sd.update(data)
    user.state_data = sd
    user.save(update_fields=["state", "state_data"])


def _cooldown_remaining(user):
    last = float((user.state_data or {}).get("last_submit", 0) or 0)
    return max(0, int(COOLDOWN_SECONDS - (time.time() - last)))


def _mark_submitted(user):
    sd = dict(user.state_data or {})
    sd["last_submit"] = time.time()
    user.state = ST_IDLE
    user.state_data = sd
    user.save(update_fields=["state", "state_data"])


# ==========================================================================
#  Клавіатури
# ==========================================================================
def _parent_menu(user):
    rows = []
    if not user.phone:
        rows.append([{"text": BTN_SHARE, "request_contact": True}])
    rows.append([BTN_QUESTION, BTN_REVIEW])
    rows.append([BTN_CONTACTS, BTN_ANKETA])
    return {"keyboard": rows, "resize_keyboard": True}


def _admin_menu():
    return {"keyboard": [[BTN_STATS, BTN_NEW], [BTN_QUESTION, BTN_REVIEW], [BTN_HELP]],
            "resize_keyboard": True}


def _cancel_menu():
    return {"keyboard": [[BTN_CANCEL]], "resize_keyboard": True}


def _share_contact_menu():
    return {"keyboard": [[{"text": BTN_SHARE, "request_contact": True}], [BTN_CANCEL]],
            "resize_keyboard": True}


def _rating_kb():
    return {"inline_keyboard": [[
        {"text": "⭐" * n, "callback_data": f"rate:{n}"} for n in range(1, 6)
    ]]}


def _status_kb(prefix, obj_id):
    return {"inline_keyboard": [
        [{"text": "📞 В роботі", "callback_data": f"{prefix}:in_progress:{obj_id}"},
         {"text": "✅ Зв'язались", "callback_data": f"{prefix}:contacted:{obj_id}"}],
        [{"text": "🎉 Зараховано", "callback_data": f"{prefix}:enrolled:{obj_id}"},
         {"text": "🚫 Відмова", "callback_data": f"{prefix}:rejected:{obj_id}"}],
        [{"text": "📦 Архів", "callback_data": f"{prefix}:archived:{obj_id}"}],
    ]}


def _review_mod_kb(obj_id):
    return {"inline_keyboard": [[
        {"text": "✅ Опублікувати", "callback_data": f"rev:approve:{obj_id}"},
        {"text": "🗑 Відхилити", "callback_data": f"rev:reject:{obj_id}"},
    ]]}


# ==========================================================================
#  Форматування
# ==========================================================================
def _esc(value):
    return html.escape(str(value if value not in (None, "") else "—"))


def _admin_link(prefix, obj_id):
    base = _site_base_url()
    if not base:
        return ""
    model = {"s": "surveyapplication", "c": "contactmessage", "rev": "testimonial"}.get(prefix)
    return f'\n🔗 <a href="{base}/admin/api/{model}/{obj_id}/change/">Відкрити в адмінці</a>'


def _format_survey(app):
    ages = ", ".join(app.ages or []) or "—"
    fmt = ", ".join(app.formats or []) or "—"
    lines = [
        "🆕 <b>Нова заявка з анкети!</b>",
        "",
        f"👶 Дитина: <b>{_esc(app.child_name)}</b>",
        f"👪 Батьки: {_esc(app.parent_name)}",
        f"📞 Телефон: <code>{_esc(app.phone)}</code>",
    ]
    if app.email:
        lines.append(f"✉️ Email: {_esc(app.email)}")
    lines.append(f"🎂 Вік: {_esc(ages)}")
    if any(app.formats or []):
        lines.append(f"🗓 Формат: {_esc(fmt)}")
    return "\n".join(lines)


def _format_contact(msg):
    head = "📨 <b>Нове запитання з Telegram!</b>" if msg.source == "telegram" else "📨 <b>Нове повідомлення з форми!</b>"
    return (
        f"{head}\n\n"
        f"👤 {_esc(msg.name)}\n"
        f"📞 <code>{_esc(msg.phone)}</code>\n\n"
        f"💬 {_esc(msg.message)}"
    )


def _format_review(t):
    return (
        "🗣 <b>Новий відгук (на модерації)</b>\n\n"
        f"{'⭐' * int(t.rating or 0)}\n"
        f"«{_esc(t.text)}»\n\n"
        f"👤 {_esc(t.author_name)}"
        + (f" · {_esc(t.author_contact)}" if t.author_contact else "")
        + "\n\nОпублікувати на сайті?"
    )


# ==========================================================================
#  Вихідні сповіщення (адмінам)
# ==========================================================================
def notify_new_survey(app):
    if not is_configured():
        return
    text = _format_survey(app) + _admin_link("s", app.id)
    for chat_id in _active_admin_chats():
        send_message(chat_id, text, reply_markup=_status_kb("s", app.id))


def notify_new_contact(msg):
    if not is_configured():
        return
    text = _format_contact(msg) + _admin_link("c", msg.id)
    for chat_id in _active_admin_chats():
        send_message(chat_id, text, reply_markup=_status_kb("c", msg.id))


def notify_new_review(t):
    if not is_configured():
        return
    text = _format_review(t) + _admin_link("rev", t.id)
    for chat_id in _active_admin_chats():
        send_message(chat_id, text, reply_markup=_review_mod_kb(t.id))


def notify_admin_granted(user):
    """Викликається з адмінки сайту, коли людині надали права адміністратора."""
    if not is_configured() or not user.chat_id:
        return
    send_message(
        user.chat_id,
        "🎉 <b>Вам надано права адміністратора The Poppins Club!</b>\n\n"
        "Тепер ви отримуватимете сповіщення про нові заявки, повідомлення та відгуки, "
        "і зможете керувати ними прямо тут:\n"
        "• кнопки статусу під кожним зверненням (зокрема 📦 Архів);\n"
        "• модерація відгуків (опублікувати / відхилити);\n"
        "• команди: 📊 /stats, 🆕 /new.\n\n"
        "Інші адміністратори бачитимуть, хто взяв звернення в роботу.",
        reply_markup=_admin_menu(),
    )


def _broadcast_status_change(actor, obj, kind_label, status_label, exclude_chat):
    who = _esc(getattr(obj, "child_name", None) or getattr(obj, "name", None) or "звернення")
    text = f"👤 <b>{_esc(actor)}</b> змінив(ла) статус: {kind_label} «{who}» → {status_label}"
    for chat_id in _active_admin_chats(exclude=exclude_chat):
        send_message(chat_id, text)


# ==========================================================================
#  Обробка вхідних оновлень
# ==========================================================================
def handle_update(update):
    if not isinstance(update, dict):
        return
    if "callback_query" in update:
        _handle_callback(update["callback_query"])
        return
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    if "contact" in msg:
        _handle_contact(msg)
        return
    _handle_message(msg)


def _handle_contact(msg):
    chat_id = msg.get("chat", {}).get("id")
    frm = msg.get("from", {})
    user = _upsert_user(chat_id, frm)
    contact = msg.get("contact", {}) or {}
    phone = contact.get("phone_number", "") or ""
    if phone:
        user.phone = phone[:32]
        user.save(update_fields=["phone"])
    send_message(
        chat_id,
        "✅ Дякую! Контакт збережено.\n\nТепер можете поставити запитання або залишити відгук 🙂",
        reply_markup=_admin_menu() if _is_admin(user) else _parent_menu(user),
    )


def _handle_message(msg):
    text = (msg.get("text") or "").strip()
    chat_id = msg.get("chat", {}).get("id")
    frm = msg.get("from", {})
    user = _upsert_user(chat_id, frm)
    low = text.lower()
    admin = _is_admin(user)

    # Універсальні команди
    if low.startswith("/start"):
        _set_state(user, ST_IDLE)
        send_message(chat_id, _welcome(user), reply_markup=_admin_menu() if admin else _parent_menu(user))
        return
    if text == BTN_CANCEL or low.startswith("/cancel"):
        _set_state(user, ST_IDLE)
        send_message(chat_id, "Скасовано.", reply_markup=_admin_menu() if admin else _parent_menu(user))
        return
    if low.startswith("/help") or text == BTN_HELP:
        send_message(chat_id, _admin_help() if admin else _parent_help(),
                     reply_markup=_admin_menu() if admin else _parent_menu(user))
        return

    # Команди адміністратора
    if admin and (low.startswith("/stats") or text == BTN_STATS):
        send_message(chat_id, _stats_text())
        return
    if admin and (low.startswith("/new") or text == BTN_NEW):
        _send_new_apps(chat_id)
        return

    # Дії з меню батьків
    if text == BTN_CONTACTS:
        send_message(chat_id, _contacts_text())
        return
    if text == BTN_ANKETA:
        base = _site_base_url() or ""
        link = f"{base}/anketa" if base else "розділ «Заповнити анкету» на сайті"
        send_message(chat_id, f"📝 Заповніть анкету попередньої реєстрації:\n{link}")
        return
    if text == BTN_QUESTION:
        if not user.phone:
            send_message(chat_id, "Спершу поділіться контактом 👇", reply_markup=_share_contact_menu())
            return
        _set_state(user, ST_QUESTION)
        send_message(chat_id, "✍️ Напишіть ваше запитання одним повідомленням — і ми передамо його адміністрації.",
                     reply_markup=_cancel_menu())
        return
    if text == BTN_REVIEW:
        if not user.phone:
            send_message(chat_id, "Спершу поділіться контактом 👇", reply_markup=_share_contact_menu())
            return
        send_message(chat_id, "🗣 Оцініть садочок від 1 до 5 зірок:", reply_markup=_rating_kb())
        return

    # Текст у межах сценарію
    if user.state == ST_QUESTION:
        _submit_question(user, text)
        return
    if user.state == ST_REVIEW:
        _submit_review(user, text)
        return

    # Нічого не підійшло
    send_message(chat_id, _admin_help() if admin else _parent_help(),
                 reply_markup=_admin_menu() if admin else _parent_menu(user))


def _handle_callback(cb):
    cb_id = cb.get("id")
    data = cb.get("data", "")
    frm = cb.get("from", {})
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    message_id = cb.get("message", {}).get("message_id")
    user = _upsert_user(frm.get("id"), frm)

    # Вибір оцінки відгуку (доступно всім)
    m = re.match(r"^rate:([1-5])$", data)
    if m:
        _set_state(user, ST_REVIEW, rating=int(m.group(1)))
        answer_callback(cb_id, "Оцінка збережена")
        edit_message_text(chat_id, message_id, f"{'⭐' * int(m.group(1))}\n\n✍️ Тепер напишіть свій відгук одним повідомленням:")
        send_message(chat_id, "Очікую ваш відгук…", reply_markup=_cancel_menu())
        return

    # Далі — лише для адміністраторів
    if not _is_admin(user):
        answer_callback(cb_id, "Лише для адміністраторів 🔒")
        return

    actor = user.name or user.username or str(chat_id)

    # Зміна статусу заявки/повідомлення
    m = re.match(r"^([sc]):([a-z_]+):(\d+)$", data)
    if m:
        prefix, status, obj_id = m.group(1), m.group(2), int(m.group(3))
        from .models import SurveyApplication, ContactMessage, REQUEST_STATUS_CHOICES
        labels = dict(REQUEST_STATUS_CHOICES)
        Model = SurveyApplication if prefix == "s" else ContactMessage
        try:
            obj = Model.objects.get(pk=obj_id)
        except Model.DoesNotExist:
            answer_callback(cb_id, "Запис не знайдено")
            return
        obj.status = status
        obj.is_read = True
        obj.handled_by = actor
        obj.save(update_fields=["status", "is_read", "handled_by", "updated_at"])
        answer_callback(cb_id, f"Статус: {labels.get(status, status)}")
        base = _format_survey(obj) if prefix == "s" else _format_contact(obj)
        base += _admin_link(prefix, obj_id)
        new_text = base + f"\n\n📌 Статус: <b>{_esc(labels.get(status, status))}</b> · 👤 {_esc(actor)}"
        edit_message_text(chat_id, message_id, new_text, reply_markup=_status_kb(prefix, obj_id))
        _broadcast_status_change(actor, obj, "заявка" if prefix == "s" else "повідомлення",
                                 labels.get(status, status), exclude_chat=chat_id)
        return

    # Модерація відгуку
    m = re.match(r"^rev:(approve|reject):(\d+)$", data)
    if m:
        action, obj_id = m.group(1), int(m.group(2))
        from .models import Testimonial
        try:
            t = Testimonial.objects.get(pk=obj_id)
        except Testimonial.DoesNotExist:
            answer_callback(cb_id, "Відгук не знайдено")
            return
        if action == "approve":
            t.is_published = True
            t.save(update_fields=["is_published"])
            answer_callback(cb_id, "Опубліковано ✅")
            edit_message_text(chat_id, message_id,
                              _format_review(t) + f"\n\n✅ <b>Опубліковано</b> · 👤 {_esc(actor)}")
            _broadcast_status_change(actor, t, "відгук", "опубліковано", exclude_chat=chat_id)
        else:
            edit_message_text(chat_id, message_id,
                              _format_review(t) + f"\n\n🗑 <b>Відхилено</b> · 👤 {_esc(actor)}")
            t.delete()
            answer_callback(cb_id, "Відхилено 🗑")
        return

    answer_callback(cb_id)


# ==========================================================================
#  Подання запитання / відгуку (батьки)
# ==========================================================================
def _submit_question(user, text):
    rem = _cooldown_remaining(user)
    if rem:
        send_message(user.chat_id, f"⏳ Зачекайте {rem} с перед наступним повідомленням.")
        return
    if len(text) < MIN_TEXT:
        send_message(user.chat_id, "Опишіть запитання трохи детальніше (мін. 5 символів).")
        return
    text = text[:MAX_QUESTION]
    from .models import ContactMessage
    msg = ContactMessage.objects.create(
        name=(user.name or user.username or "Батьки")[:100],
        phone=(user.phone or "")[:20],
        message=text,
        source="telegram",
    )
    _mark_submitted(user)
    send_message(user.chat_id, "✅ Дякуємо! Ваше запитання передано адміністрації — ми відповімо найближчим часом 💛",
                 reply_markup=_parent_menu(user))
    try:
        notify_new_contact(msg)
    except Exception:
        pass


def _submit_review(user, text):
    rem = _cooldown_remaining(user)
    if rem:
        send_message(user.chat_id, f"⏳ Зачекайте {rem} с перед наступним відгуком.")
        return
    if len(text) < MIN_TEXT:
        send_message(user.chat_id, "Напишіть, будь ласка, трохи більше (мін. 5 символів).")
        return
    text = text[:MAX_REVIEW]
    rating = int((user.state_data or {}).get("rating", 5))
    contact = " ".join(filter(None, [user.phone, f"@{user.username}" if user.username else ""]))
    from .models import Testimonial
    t = Testimonial.objects.create(
        author_name=(user.name or user.username or "Батьки")[:100],
        relation="",
        text=text,
        rating=rating,
        is_published=False,        # модерація!
        source="telegram",
        author_contact=contact[:150],
    )
    _mark_submitted(user)
    send_message(user.chat_id, "✅ Дякуємо за відгук! Він з'явиться на сайті після перевірки адміністратором 💛",
                 reply_markup=_parent_menu(user))
    try:
        notify_new_review(t)
    except Exception:
        pass


# ==========================================================================
#  Тексти
# ==========================================================================
def _welcome(user):
    name = html.escape(user.name) if user.name else ""
    hello = f"Вітаю, {name}! " if name else "Вітаю! "
    if _is_admin(user):
        return (f"👋 {hello}Ви — <b>адміністратор</b> The Poppins Club.\n\n"
                "Отримуєте сповіщення про звернення й керуєте ними кнопками. "
                "Меню — нижче. /help — довідка.")
    return (f"👋 {hello}Я бот садочка <b>The Poppins Club</b>.\n\n"
            "Тут ви можете:\n"
            "• ❓ поставити запитання адміністрації;\n"
            "• 🗣 залишити відгук про садочок;\n"
            "• 📞 переглянути контакти та 📝 заповнити анкету.\n\n"
            "Спершу поділіться контактом (кнопка нижче) — щоб ми могли з вами зв'язатися 👇")


def _parent_help():
    return ("ℹ️ <b>Що я вмію:</b>\n"
            "• ❓ <b>Поставити запитання</b> — напишіть, і адміністрація відповість.\n"
            "• 🗣 <b>Залишити відгук</b> — оцінка + текст (з'явиться на сайті після модерації).\n"
            "• 📞 <b>Контакти садочка</b> · 📝 <b>Записатися</b>.\n\n"
            "Спершу поділіться контактом — це швидко й безпечно.")


def _admin_help():
    return ("ℹ️ <b>Адмін-команди:</b>\n"
            "📊 /stats — статистика заявок\n"
            "🆕 /new — нові заявки з кнопками\n\n"
            "Під кожним зверненням — кнопки статусу (зокрема 📦 Архів). Під відгуком — "
            "«Опублікувати / Відхилити». Інші адміни бачать, хто що взяв.")


def _contacts_text():
    from .models import SiteInfo
    info = SiteInfo.objects.first()
    if not info:
        return "Контакти зараз недоступні."
    lines = ["📞 <b>Контакти The Poppins Club</b>", ""]
    if info.phone:
        lines.append(f"☎️ {_esc(info.phone)}")
    if info.email:
        lines.append(f"✉️ {_esc(info.email)}")
    if info.address:
        lines.append(f"📍 {_esc(info.address)}")
    socials = []
    if info.facebook: socials.append(f'<a href="{info.facebook}">Facebook</a>')
    if info.instagram: socials.append(f'<a href="{info.instagram}">Instagram</a>')
    if info.telegram: socials.append(f'<a href="{info.telegram}">Telegram</a>')
    if socials:
        lines.append("🌐 " + " · ".join(socials))
    return "\n".join(lines)


def _stats_text():
    from .models import SurveyApplication, ContactMessage
    s = SurveyApplication.objects
    return (
        "📊 <b>Статистика заявок</b>\n\n"
        f"🆕 Нові: <b>{s.filter(status='new').count()}</b>\n"
        f"📞 В роботі: <b>{s.filter(status__in=['in_progress', 'contacted']).count()}</b>\n"
        f"🎉 Зараховано: <b>{s.filter(status='enrolled').count()}</b>\n"
        f"🚫 Відмова: <b>{s.filter(status='rejected').count()}</b>\n"
        f"📦 Архів: <b>{s.filter(status='archived').count()}</b>\n"
        f"📁 Усього: <b>{s.count()}</b>\n\n"
        f"📨 Нові повідомлення: <b>{ContactMessage.objects.filter(status='new').count()}</b>"
    )


def _send_new_apps(chat_id):
    from .models import SurveyApplication
    new_apps = list(SurveyApplication.objects.filter(status="new")[:8])
    if not new_apps:
        send_message(chat_id, "✅ Нових заявок немає. Чудова робота! 🎉")
        return
    send_message(chat_id, f"🆕 Нових заявок: <b>{len(new_apps)}</b>")
    for app in new_apps:
        send_message(chat_id, _format_survey(app) + _admin_link("s", app.id),
                     reply_markup=_status_kb("s", app.id))
