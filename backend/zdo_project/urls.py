from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve as static_serve
from api import views

_DIST = settings.BASE_DIR.parent / 'frontend' / 'dist'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/content/', views.get_site_content),
    path('api/contact/', views.submit_contact),
    path('api/survey/', views.submit_survey),
    path('api/chat/', views.submit_chat),
    path('api/telegram/<str:secret>/', views.telegram_webhook),
    path('sitemap.xml', views.sitemap_xml),
    path('robots.txt', views.robots_txt),
    # Кореневі публічні файли (OG-картинка, фавікон) — інакше їх ловить SPA-catch-all.
    # Важливо для краулерів соцмереж, що не виконують JS.
    path('og-image.png', static_serve, {'document_root': str(_DIST), 'path': 'og-image.png'}),
    path('favicon.webp', static_serve, {'document_root': str(_DIST), 'path': 'favicon.webp'}),
]

# Віддача media і кореня frontend/dist у dev (у prod це робить WhiteNoise + PA static maps)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SPA catch-all: будь-яка інша URL віддає index.html (для /anketa і подібних маршрутів React Router)
# templates/index.html має бути присутній (копіюється з frontend/dist/index.html після білда)
urlpatterns += [
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='spa'),
]
