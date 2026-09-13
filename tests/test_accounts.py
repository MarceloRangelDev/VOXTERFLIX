"""Testes de cadastro, login, confirmação de e-mail e rate limiting."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.accounts.tokens import email_confirmation_token
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


class SignUpTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.accounts.views.ResendEmailService")
    def test_signup_creates_inactive_user(self, mock_email_service):
        response = self.client.post(
            reverse("accounts:signup"),
            {"username": "novo_usuario", "email": "novo@exemplo.com", "password1": "SenhaForte123!", "password2": "SenhaForte123!"},
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="novo_usuario")
        self.assertFalse(user.is_active)
        mock_email_service.return_value.send_confirmation_email.assert_called_once()

    @patch("apps.accounts.views.ResendEmailService")
    def test_signup_rejects_duplicate_email(self, mock_email_service):
        User.objects.create_user(username="existente", email="dup@exemplo.com", password="x")
        response = self.client.post(
            reverse("accounts:signup"),
            {"username": "outro", "email": "dup@exemplo.com", "password1": "SenhaForte123!", "password2": "SenhaForte123!"},
        )
        self.assertEqual(response.status_code, 200)  # form volta com erro
        self.assertFalse(User.objects.filter(username="outro").exists())


class ConfirmEmailTests(TestCase):
    @patch("apps.accounts.views.ResendEmailService")
    def test_confirm_email_activates_account(self, mock_email_service):
        user = User.objects.create_user(username="pendente", email="pendente@exemplo.com", password="x", is_active=False)
        token = email_confirmation_token.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        response = self.client.get(reverse("accounts:confirmar_email", kwargs={"uidb64": uidb64, "token": token}))

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(response.status_code, 302)
        mock_email_service.return_value.send_welcome_email.assert_called_once()

    def test_confirm_email_rejects_invalid_token(self):
        user = User.objects.create_user(username="pendente2", email="p2@exemplo.com", password="x", is_active=False)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        self.client.get(reverse("accounts:confirmar_email", kwargs={"uidb64": uidb64, "token": "token-invalido"}))

        user.refresh_from_db()
        self.assertFalse(user.is_active)


class LoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="ana", email="ana@exemplo.com", password="SenhaForte123!")

    def test_login_with_valid_credentials(self):
        response = self.client.post(reverse("accounts:login"), {"username": "ana", "password": "SenhaForte123!"})
        self.assertEqual(response.status_code, 302)

    def test_login_with_invalid_password_shows_generic_message(self):
        response = self.client.post(reverse("accounts:login"), {"username": "ana", "password": "errada"})
        self.assertContains(response, "Usuário ou senha inválidos.")

    def test_login_inactive_user_shows_generic_message(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse("accounts:login"), {"username": "ana", "password": "SenhaForte123!"})
        # Não deve autenticar nem revelar que a conta existe mas está inativa.
        self.assertContains(response, "Usuário ou senha inválidos.")

    def test_login_blocked_after_repeated_failures(self):
        for _ in range(3):
            self.client.post(reverse("accounts:login"), {"username": "ana", "password": "errada"})

        response = self.client.post(reverse("accounts:login"), {"username": "ana", "password": "SenhaForte123!"})
        self.assertContains(response, "Muitas tentativas de login")

    def test_rate_limit_is_scoped_per_username(self):
        """Bloquear "ana" não deve afetar o login de outro usuário no mesmo IP."""
        User.objects.create_user(username="bruno", email="bruno@exemplo.com", password="SenhaForte123!")
        for _ in range(3):
            self.client.post(reverse("accounts:login"), {"username": "ana", "password": "errada"})

        response = self.client.post(reverse("accounts:login"), {"username": "bruno", "password": "SenhaForte123!"})
        self.assertEqual(response.status_code, 302)
