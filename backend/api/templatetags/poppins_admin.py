"""
Шаблонні теги для дашборду адмінки The Poppins Club.
Дають живу статистику звернень на головній сторінці адмінки.
"""

from django import template
from django.db.models import Q

from api.models import SurveyApplication, ContactMessage

register = template.Library()

_CLOSED = ("enrolled", "rejected", "archived")


@register.simple_tag
def poppins_dashboard_stats():
    """Повертає словник лічильників для панелі на головній адмінки."""
    surveys = SurveyApplication.objects.all()
    messages = ContactMessage.objects.all()

    recent = list(
        SurveyApplication.objects.only(
            "id", "child_name", "parent_name", "phone", "status", "is_read", "created_at"
        )[:6]
    )

    return {
        "survey_total": surveys.count(),
        "survey_unread": surveys.filter(is_read=False).count(),
        "survey_open": surveys.exclude(status__in=_CLOSED).count(),
        "survey_enrolled": surveys.filter(status="enrolled").count(),
        "msg_total": messages.count(),
        "msg_unread": messages.filter(is_read=False).count(),
        "attention": surveys.filter(is_read=False).count() + messages.filter(is_read=False).count(),
        "recent": recent,
    }
