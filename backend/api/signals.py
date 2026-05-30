"""
Сигнали застосунку.

Коли в адмінці людині вмикають прапорець «Адміністратор» (is_admin: False→True)
у Telegram-користувача — бот автоматично надсилає їй привітання з правами.
Працює незалежно від місця зміни (форма редагування чи редагування у списку).
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import TelegramSubscriber


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
