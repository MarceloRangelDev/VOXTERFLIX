from django.urls import path

from apps.history import views

app_name = "history"

urlpatterns = [
    path("", views.history_list, name="lista"),
    path("<int:pk>/remover/", views.remove_history_item, name="remover"),
    path("progresso/", views.update_progress, name="progresso"),
]
