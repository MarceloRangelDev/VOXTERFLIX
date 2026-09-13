"""Views de autenticação: cadastro, login, confirmação de e-mail e senha.

Sempre que possível reaproveitamos as classes oficiais do
`django.contrib.auth` (login, geração de token de recuperação de senha,
hashing de senha) — apenas trocamos o transporte do e-mail para o Resend
e adicionamos rate limiting nos pontos sensíveis a força bruta/abuso.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.accounts.forms import ResendPasswordResetForm, SignUpForm, StyledAuthenticationForm
from apps.accounts.tokens import email_confirmation_token
from apps.core.security import (
    get_client_ip,
    is_rate_limited,
    log_security_event,
    register_attempt,
    reset_rate_limit,
)
from apps.notifications.services import ResendEmailService

SIGNUP_RATE_LIMIT = "5/1h"
PASSWORD_RESET_RATE_LIMIT = "3/1h"


def signup(request):
    """Cadastro de conta. A conta só é ativada após confirmar o e-mail."""
    if request.user.is_authenticated:
        return redirect("catalog:home")

    ip_key = f"signup:{get_client_ip(request)}"

    if request.method == "POST":
        if is_rate_limited(ip_key, SIGNUP_RATE_LIMIT):
            messages.error(request, "Muitos cadastros a partir deste endereço. Tente novamente mais tarde.")
            return render(request, "accounts/signup.html", {"form": SignUpForm()})

        form = SignUpForm(request.POST)
        if form.is_valid():
            register_attempt(ip_key, SIGNUP_RATE_LIMIT)
            user = form.save()
            _send_confirmation_email(request, user)
            log_security_event("signup", request, username=user.username)
            messages.success(request, "Cadastro realizado! Verifique seu e-mail para confirmar a conta.")
            return redirect("accounts:login")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


def _send_confirmation_email(request, user: User) -> None:
    token = email_confirmation_token.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    path = reverse("accounts:confirmar_email", kwargs={"uidb64": uidb64, "token": token})
    confirm_url = request.build_absolute_uri(path)
    ResendEmailService().send_confirmation_email(user, confirm_url)


def confirm_email(request, uidb64, token):
    """Ativa a conta se o token (assinado, com expiração) for válido."""
    user = _get_user_from_uidb64(uidb64)

    if user is not None and email_confirmation_token.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        log_security_event("email_confirmed", request, user=user)
        ResendEmailService().send_welcome_email(user)
        messages.success(request, "E-mail confirmado com sucesso! Você já pode entrar na sua conta.")
    else:
        messages.error(request, "Link de confirmação inválido ou expirado.")

    return redirect("accounts:login")


def _get_user_from_uidb64(uidb64: str):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None


def login_view(request):
    """Login com rate limiting por IP + usuário tentado.

    Apenas tentativas *falhas* contam para o limite — um login bem-sucedido
    zera o contador (evita punir o usuário legítimo por tentativas antigas).
    """
    if request.user.is_authenticated:
        return redirect("catalog:home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        rate_key = f"login:{get_client_ip(request)}:{username.lower()}"

        if is_rate_limited(rate_key, settings.LOGIN_RATE_LIMIT):
            log_security_event("login_blocked", request, username=username)
            messages.error(request, "Muitas tentativas de login. Tente novamente em alguns minutos.")
            return render(request, "accounts/login.html", {"form": StyledAuthenticationForm()})

        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            reset_rate_limit(rate_key)
            user = form.get_user()
            auth_login(request, user)
            log_security_event("login_success", request, user=user)
            next_url = request.POST.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect("profiles:selecionar")

        register_attempt(rate_key, settings.LOGIN_RATE_LIMIT)
        log_security_event("login_failed", request, username=username)
    else:
        form = StyledAuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


# ----------------------------------------------------------------------
# Views de senha: reaproveitam as classes oficiais do Django, trocando
# apenas templates, transporte de e-mail (Resend) e adicionando rate
# limiting/logging de segurança.
# ----------------------------------------------------------------------


class VoxterPasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    form_class = ResendPasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")

    def post(self, request, *args, **kwargs):
        ip_key = f"password_reset:{get_client_ip(request)}"
        if is_rate_limited(ip_key, PASSWORD_RESET_RATE_LIMIT):
            log_security_event("rate_limit_blocked", request, contexto="password_reset")
            # Redireciona para a mesma tela de sucesso — não confirmamos
            # nem negamos que o e-mail exista só porque o limite foi atingido.
            return redirect(self.success_url)
        register_attempt(ip_key, PASSWORD_RESET_RATE_LIMIT)
        log_security_event("password_reset_requested", request, email=request.POST.get("email", ""))
        return super().post(request, *args, **kwargs)


class VoxterPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class VoxterPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    def form_valid(self, form):
        response = super().form_valid(form)
        ResendEmailService().send_password_changed_email(form.user)
        log_security_event("password_reset_completed", self.request, user=form.user)
        return response


class VoxterPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class VoxterPasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        ResendEmailService().send_password_changed_email(self.request.user)
        log_security_event("password_reset_completed", self.request, user=self.request.user)
        return response


class VoxterPasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"
