from django.urls import path, re_path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("buscar/", views.search, name="buscar"),
    # O IMDb ID sempre segue o formato "tt" + dígitos — validar isso já na
    # URL evita que valores arbitrários cheguem até a integração com a OMDb.
    re_path(r"^titulo/(?P<imdb_id>tt\d+)/$", views.detail, name="detalhe"),
]
