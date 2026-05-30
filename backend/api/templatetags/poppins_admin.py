"""
Шаблонні теги для дашборду адмінки The Poppins Club.

Уся статистика рахується ЗА СТАТУСОМ (єдине джерело правди) і БЕЗ архівних —
щойно ви змінюєте статус заявки, вона одразу залишає лічильник «нові»/«в роботі».
"""

from django import template

from api.models import SurveyApplication, ContactMessage

register = template.Library()


@register.simple_tag
def poppins_dashboard_stats():
    """Лічильники для панелі на головній адмінки (за статусом, без архіву)."""
    surveys = SurveyApplication.objects.filter(is_archived=False)
    messages = ContactMessage.objects.filter(is_archived=False)

    recent = list(
        SurveyApplication.objects.filter(is_archived=False).only(
            "id", "child_name", "parent_name", "phone", "status", "created_at"
        )[:6]
    )

    return {
        "survey_total": SurveyApplication.objects.count(),
        "survey_new": surveys.filter(status="new").count(),
        "survey_in_progress": surveys.filter(status="in_progress").count(),
        "survey_done": surveys.filter(status="done").count(),
        "msg_total": ContactMessage.objects.count(),
        "msg_new": messages.filter(status="new").count(),
        "recent": recent,
    }
