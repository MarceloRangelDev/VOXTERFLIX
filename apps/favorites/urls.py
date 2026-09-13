from django.urls import path

from apps.favorites import views

app_name = "favorites"

urlpatterns = [
    path("", views.my_list, name="lista"),
    path("<str:imdb_id>/alternar/", views.toggle_favorite, name="alternar"),
]
