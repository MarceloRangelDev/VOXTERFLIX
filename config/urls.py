"""Configuração de URLs raiz do VoxterFlix."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.catalog.urls")),
    path("contas/", include("apps.accounts.urls")),
    path("perfis/", include("apps.profiles.urls")),
    path("favoritos/", include("apps.favorites.urls")),
    path("historico/", include("apps.history.urls")),
    path("streaming/", include("apps.streaming.urls")),
]

if settings.DEBUG:
    # Em produção, o servidor de mídia deve ser outro (nginx, S3 etc.);
    # servir MEDIA_URL pelo próprio Django é só para desenvolvimento local.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
