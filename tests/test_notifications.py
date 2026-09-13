"""Testes do serviço de e-mail: envio, falha e ausência de configuração."""

from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from apps.notifications.models import EmailLog
from apps.notifications.services import ResendEmailService


class ResendEmailServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tais", email="tais@exemplo.com", password="x")

    @override_settings(RESEND_API_KEY="")
    def test_skips_send_when_not_configured(self):
        result = ResendEmailService().send_welcome_email(self.user)

        self.assertFalse(result)
        log = EmailLog.objects.get(to_email="tais@exemplo.com")
        self.assertEqual(log.status, EmailLog.Status.SKIPPED)

    @override_settings(RESEND_API_KEY="chave-de-teste")
    @patch("apps.notifications.services.resend")
    def test_successful_send_creates_log(self, mock_resend):
        mock_resend.Emails.send.return_value = {"id": "msg-123"}

        result = ResendEmailService().send_welcome_email(self.user)

        self.assertTrue(result)
        log = EmailLog.objects.get(to_email="tais@exemplo.com")
        self.assertEqual(log.status, EmailLog.Status.SENT)
        self.assertEqual(log.provider_message_id, "msg-123")

    @override_settings(RESEND_API_KEY="chave-de-teste")
    @patch("apps.notifications.services.resend")
    def test_provider_failure_is_logged_without_raising(self, mock_resend):
        mock_resend.Emails.send.side_effect = Exception("Falha simulada do provedor")

        result = ResendEmailService().send_welcome_email(self.user)

        self.assertFalse(result)
        log = EmailLog.objects.get(to_email="tais@exemplo.com")
        self.assertEqual(log.status, EmailLog.Status.FAILED)

    @override_settings(RESEND_API_KEY="chave-de-teste")
    @patch("apps.notifications.services.resend")
    def test_idempotency_key_is_passed_for_welcome_email(self, mock_resend):
        mock_resend.Emails.send.return_value = {"id": "msg-456"}

        ResendEmailService().send_welcome_email(self.user)

        args, _ = mock_resend.Emails.send.call_args
        self.assertEqual(args[1], {"idempotency_key": f"welcome/{self.user.pk}"})
