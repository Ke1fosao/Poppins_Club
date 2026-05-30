"""
Сигнали застосунку.

Коли в адмінці людині вмикають прапорець «Адміністратор» (is_admin: False→True)
у Telegram-користувача — бот автоматично надсилає їй привітання з правами.
Працює незалежно від місця зміни (форма редагування чи редагування у списку).
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import TelegramSubscriber, SurveyApplication, ContactMessage


@receiver(pre_save, sender=TelegramSubscriber)
def _remember_old_is_admin(sender, instance, **kwargs):
    if instance.pk:
        instance._was_admin = (
            TelegramSubscriber.objects.filter(pk=instance.pk)
            .values_list("is_admin", flat=True)
            .first()
        ) or False
    else:
        instance._was_admin = False


@receiver(post_save, sender=TelegramSubscriber)
def _on_admin_granted(sender, instance, created, **kwargs):
    # Спрацьовує лише на переході «звичайний → адміністратор»
    if getattr(instance, "_was_admin", False) or not instance.is_admin:
        return
    # Адмін завжди має отримувати сповіщення
    if not instance.is_active:
        TelegramSubscriber.objects.filter(pk=instance.pk).update(is_active=True)
        instance.is_active = True
    try:
        from . import telegram_bot as tg
        tg.notify_admin_granted(instance)
    except Exception:
        pass


# --- Синхронізація статусу звернень у всіх адмінів Telegram ----------------
@receiver(pre_save, sender=SurveyApplication)
@receiver(pre_save, sender=ContactMessage)
def _remember_old_request(sender, instance, **kwargs):
    if instance.pk:
        old = sender.objects.filter(pk=instance.pk).values("status", "is_archived").first() or {}
        instance._old_status = old.get("status")
        instance._old_archived = old.get("is_archived")
    else:
        instance._old_status = None
        instance._old_archived = None


@receiver(post_save, sender=SurveyApplication)
@receiver(post_save, sender=ContactMessage)
def _sync_request_to_telegram(sender, instance, created, **kwargs):
    # Синхронізуємо лише при реальній зміні статусу/архіву (не на створенні)
    if created:
        return
    if (instance.status == getattr(instance, "_old_status", None)
            and instance.is_archived == getattr(instance, "_old_archived", None)):
        return
    try:
        from . import telegram_bot as tg
        tg.sync_status_to_telegram(instance)
    except Exception:
        pass
