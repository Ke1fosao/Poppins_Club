from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from api import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/content/', views.get_site_content),
    path('api/contact/', views.submit_contact),
    path('api/survey/', views.submit_survey),
    path('api/chat/', views.submit_chat),
]

# Віддача media і кореня frontend/dist у dev (у prod це робить WhiteNoise + PA static maps)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SPA catch-all: будь-яка інша URL віддає index.html (для /anketa і подібних маршрутів React Router)
# templates/index.html має бути присутній (копіюється з frontend/dist/index.html після білда)
urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='spa'),
]
