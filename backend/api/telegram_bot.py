"""
Telegram-бот «The Poppins Club» — webhook-режим, без зовнішніх бібліотек.

Чому webhook, а не polling:
    Безкоштовний PythonAnywhere НЕ дозволяє постійно працюючі процеси
    (polling), але дає публічний HTTPS-домен. Тому Telegram сам надсилає
    оновлення на /api/telegram/<secret>/, а Django їх обробляє. Вихідні
    повідомлення — звичайні HTTPS-запити до Bot API (через requests, який
    уже є залежністю). Жодних нових пакетів не потрібно.

Можливості:
    • Сповіщення про нові заявки та повідомлення — з inline-кнопками, що
      міняють статус заявки прямо з Telegram.
    • Команди/меню: /start (підписатися), /stop, /stats, /new, /help.

Налаштування (env-змінні, кладуться у backend/.env або у WSGI на PA):
    TELEGRAM_BOT_TOKEN       — токен від @BotFather (обов'язково)
    TELEGRAM_WEBHOOK_SECRET  — довільний секрет для URL вебхука (обов'язково)
    TELEGRAM_ALLOWED_IDS     — (необов'язково) дозволені Telegram user id
                               через кому; якщо порожньо — бот відкритий усім,
                               хто напише /start.
    SITE_BASE_URL            — (необов'язково) напр. https://ke1fosao.pythonanywhere.com
                               для прямих посилань на заявку в адмінці.
"""

import html
import os
import re

import requests

_API = "https://api.telegram.org/bot{token}/{method}"
_TIMEOUT = 15


# --------------------------------------------------------------------------
#  Конфіг із середовища
# --------------------------------------------------------------------------
def _token():
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def webhook_secret():
    return os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()


def _site_base_url():
    return os.environ.get("SITE_BASE_URL", "").strip().rstrip("/")


def _allowed_ids():
    raw = os.environ.get("TELEGRAM_ALLOWED_IDS", "")
    return {x.strip() for x in re.split(r"[,\s]+", raw) if x.strip()}


def is_configured():
    return bool(_token())


def _authorized(user_id):
    allowed = _allowed_ids()
    return (not allowed) or (str(user_id) in allowed)


# --------------------------------------------------------------------------
#  Низькорівневі виклики Bot API
# --------------------------------------------------------------------------
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
    if reply_markup:
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


# --------------------------------------------------------------------------
#  Webhook-керування (через manage.py-команду або shell)
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
#  Форматування / клавіатури
# --------------------------------------------------------------------------
def _esc(value):
    return html.escape(str(value if value not in (None, "") else "—"))


def _status_keyboard(prefix, obj_id):
    return {"inline_keyboard": [
        [{"text": "📞 В роботі", "callback_data": f"{prefix}:in_progress:{obj_id}"},
         {"text": "✅ Зв'язались", "callback_data": f"{prefix}:contacted:{obj_id}"}],
        [{"text": "🎉 Зараховано", "callback_data": f"{prefix}:enrolled:{obj_id}"},
         {"text": "🚫 Відмова", "callback_data": f"{prefix}:rejected:{obj_id}"}],
    ]}


def _main_menu():
    return {
        "keyboard": [["📊 Статистика", "🆕 Нові заявки"], ["❓ Довідка"]],
        "resize_keyboard": True,
    }


def _admin_link(prefix, obj_id):
    base = _site_base_url()
    if not base:
        return ""
    model = "surveyapplication" if prefix == "s" else "contactmessage"
    return f'\n\n🔗 <a href="{base}/admin/api/{model}/{obj_id}/change/">Відкрити в адмінці</a>'


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
    return (
        "📨 <b>Нове повідомлення з форми!</b>\n\n"
        f"👤 {_esc(msg.name)}\n"
        f"📞 <code>{_esc(msg.phone)}</code>\n\n"
        f"💬 {_esc(msg.message)}"
    )


# --------------------------------------------------------------------------
#  Вихідні сповіщення (викликаються з views при сабміті форм)
# --------------------------------------------------------------------------
def _active_chats():
    from .models import TelegramSubscriber
    return list(TelegramSubscriber.objects.filter(is_active=True).values_list("chat_id", flat=True))


def notify_new_survey(app):
    if not is_configured():
        return
    text = _format_survey(app) + _admin_link("s", app.id)
    kb = _status_keyboard("s", app.id)
    for chat_id in _active_chats():
        send_message(chat_id, text, reply_markup=kb)


def notify_new_contact(msg):
    if not is_configured():
        return
    text = _format_contact(msg) + _admin_link("c", msg.id)
    kb = _status_keyboard("c", msg.id)
    for chat_id in _active_chats():
        send_message(chat_id, text, reply_markup=kb)


# --------------------------------------------------------------------------
#  Обробка вхідних оновлень (webhook)
# --------------------------------------------------------------------------
def handle_update(update):
    if not isinstance(update, dict):
        return
    if "callback_query" in update:
        _handle_callback(update["callback_query"])
        return
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    _handle_message(msg)


def _handle_message(msg):
    text = (msg.get("text") or "").strip()
    chat_id = msg.get("chat", {}).get("id")
    frm = msg.get("from", {})
    from_id = frm.get("id")
    name = (f"{frm.get('first_name', '')} {frm.get('last_name', '')}".strip()
            or frm.get("username", "") or "")

    if not _authorized(from_id):
        send_message(chat_id, "🔒 Це приватний бот сповіщень садочка. Доступ обмежено.")
        return

    low = text.lower()
    if low.startswith("/start"):
        _subscribe(chat_id, name)
        send_message(chat_id, _welcome(name), reply_markup=_main_menu())
    elif low.startswith("/stop") or text == "🔕 Відписатися":
        _unsubscribe(chat_id)
        send_message(chat_id, "🔕 Готово, сповіщення вимкнено. Напишіть /start, щоб увімкнути знову.")
    elif low.startswith("/stats") or text == "📊 Статистика":
        send_message(chat_id, _stats_text())
    elif low.startswith("/new") or text == "🆕 Нові заявки":
        _send_new_apps(chat_id)
    else:
        send_message(chat_id, _help_text(), reply_markup=_main_menu())


def _handle_callback(cb):
    cb_id = cb.get("id")
    data = cb.get("data", "")
    from_id = cb.get("from", {}).get("id")
    message = cb.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")

    if not _authorized(from_id):
        answer_callback(cb_id, "Доступ обмежено")
        return

    m = re.match(r"^([sc]):([a-z_]+):(\d+)$", data)
    if not m:
        answer_callback(cb_id)
        return
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
    obj.save(update_fields=["status", "is_read", "updated_at"])
    answer_callback(cb_id, f"Статус: {labels.get(status, status)}")

    base = _format_survey(obj) if prefix == "s" else _format_contact(obj)
    base += _admin_link(prefix, obj_id)
    new_text = base + f"\n\n📌 Статус: <b>{_esc(labels.get(status, status))}</b>"
    edit_message_text(chat_id, message_id, new_text, reply_markup=_status_keyboard(prefix, obj_id))


# --------------------------------------------------------------------------
#  Команди-помічники
# --------------------------------------------------------------------------
def _subscribe(chat_id, name):
    from .models import TelegramSubscriber
    TelegramSubscriber.objects.update_or_create(
        chat_id=str(chat_id),
        defaults={"name": name, "is_active": True},
    )


def _unsubscribe(chat_id):
    from .models import TelegramSubscriber
    TelegramSubscriber.objects.filter(chat_id=str(chat_id)).update(is_active=False)


def _welcome(name):
    hello = f"Вітаю, {html.escape(name)}! " if name else "Вітаю! "
    return (
        f"👋 {hello}Це бот сповіщень <b>The Poppins Club</b>.\n\n"
        "Тепер ви <b>отримуватимете тут кожну нову заявку й повідомлення</b> з сайту "
        "та зможете міняти їхній статус прямо в чаті.\n\n"
        "Команди:\n"
        "📊 /stats — статистика заявок\n"
        "🆕 /new — показати нові заявки\n"
        "🔕 /stop — вимкнути сповіщення\n"
        "❓ /help — довідка"
    )


def _help_text():
    return (
        "ℹ️ <b>Бот сповіщень The Poppins Club</b>\n\n"
        "📊 /stats — статистика заявок\n"
        "🆕 /new — нові заявки (з кнопками статусу)\n"
        "▶️ /start — підписатися на сповіщення\n"
        "🔕 /stop — відписатися\n\n"
        "Коли приходить заявка — натискайте кнопки під нею, щоб змінити статус "
        "(він одразу оновлюється і на сайті в адмінці)."
    )


def _stats_text():
    from .models import SurveyApplication, ContactMessage
    s = SurveyApplication.objects
    return (
        "📊 <b>Статистика заявок</b>\n\n"
        f"🆕 Нові: <b>{s.filter(status='new').count()}</b>\n"
        f"📞 В роботі: <b>{s.filter(status__in=['in_progress', 'contacted']).count()}</b>\n"
        f"🎉 Зараховано: <b>{s.filter(status='enrolled').count()}</b>\n"
        f"🚫 Відмова: <b>{s.filter(status='rejected').count()}</b>\n"
        f"📁 Усього заявок: <b>{s.count()}</b>\n\n"
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
                     reply_markup=_status_keyboard("s", app.id))
