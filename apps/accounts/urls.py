from django.contrib.auth import views as auth_views
from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("cadastro/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("confirmar/<uidb64>/<token>/", views.confirm_email, name="confirmar_email"),
    path("senha/alterar/", views.VoxterPasswordChangeView.as_view(), name="password_change"),
    path("senha/alterar/concluido/", views.VoxterPasswordChangeDoneView.as_view(), name="password_change_done"),
    path("senha/recuperar/", views.VoxterPasswordResetView.as_view(), name="password_reset"),
    path("senha/recuperar/enviado/", views.VoxterPasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "senha/redefinir/<uidb64>/<token>/",
        views.VoxterPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "senha/redefinir/concluido/",
        views.VoxterPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
