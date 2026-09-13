from django.urls import path

from apps.profiles import views

app_name = "profiles"

urlpatterns = [
    path("selecionar/", views.select_profile, name="selecionar"),
    path("ativar/<int:profile_id>/", views.activate_profile, name="ativar"),
    path("gerenciar/", views.manage_profiles, name="gerenciar"),
    path("novo/", views.create_profile, name="criar"),
    path("<int:profile_id>/editar/", views.edit_profile, name="editar"),
    path("<int:profile_id>/excluir/", views.delete_profile, name="excluir"),
]
