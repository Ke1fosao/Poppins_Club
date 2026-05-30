"""
Шаблонні теги для дашборду адмінки The Poppins Club.

Уся статистика рахується ЗА СТАТУСОМ (єдине джерело правди). Щойно ви
змінюєте статус заявки — вона одразу залишає лічильник «нові»/«в роботі».
"""

from django import template

from api.models import SurveyApplication, ContactMessage

register = template.Library()


@register.simple_tag
def poppins_dashboard_stats():
    """Лічильники для панелі на головній адмінки (усе — за статусом)."""
    surveys = SurveyApplication.objects.all()
    messages = ContactMessage.objects.all()

    recent = list(
        SurveyApplication.objects.only(
            "id", "child_name", "parent_name", "phone", "status", "created_at"
        )[:6]
    )

    return {
        "survey_total": surveys.count(),
        "survey_new": surveys.filter(status="new").count(),
        "survey_in_progress": surveys.filter(status__in=["in_progress", "contacted"]).count(),
        "survey_enrolled": surveys.filter(status="enrolled").count(),
        "msg_total": messages.count(),
        "msg_new": messages.filter(status="new").count(),
        "recent": recent,
    }
