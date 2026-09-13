"""Serviço central de envio de e-mails transacionais via Resend.

Toda a aplicação envia e-mail através de `ResendEmailService`, nunca chamando
o SDK do Resend diretamente em views ou forms. Isso centraliza o tratamento
de erros, o logging seguro e a gravação de auditoria em `EmailLog`.
"""

from __future__ import annotations

import logging

import resend
from django.conf import settings
from django.template.loader import render_to_string

from apps.notifications.models import EmailLog

logger = logging.getLogger("voxterflix")


class ResendEmailService:
    """Encapsula a integração com o SDK oficial Python do Resend."""

    def __init__(self) -> None:
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.RESEND_FROM_EMAIL
        self.from_name = settings.RESEND_FROM_NAME

    # ------------------------------------------------------------------
    # API pública: um método por tipo de e-mail transacional
    # ------------------------------------------------------------------

    def send_confirmation_email(self, user, confirm_url: str) -> bool:
        return self._send(
            to=user.email,
            subject="Confirme seu e-mail — VoxterFlix",
            template_name="notifications/email/confirmation.html",
            context={"user": user, "confirm_url": confirm_url},
            email_type=EmailLog.EmailType.CONFIRMATION,
            # Uma chave por usuário evita reenviar a mesma confirmação em
            # duplo clique/duplo submit do formulário de cadastro.
            idempotency_key=f"confirmation/{user.pk}",
        )

    def send_welcome_email(self, user) -> bool:
        return self._send(
            to=user.email,
            subject="Bem-vindo(a) ao VoxterFlix!",
            template_name="notifications/email/welcome.html",
            context={"user": user},
            email_type=EmailLog.EmailType.WELCOME,
            idempotency_key=f"welcome/{user.pk}",
        )

    def send_password_reset_email(self, user, reset_url: str) -> bool:
        return self._send(
            to=user.email,
            subject="Recuperação de senha — VoxterFlix",
            template_name="notifications/email/password_reset.html",
            context={"user": user, "reset_url": reset_url},
            email_type=EmailLog.EmailType.PASSWORD_RESET,
            # Cada solicitação gera um token novo, então não aplicamos
            # idempotência aqui — o usuário pode legitimamente pedir de novo.
        )

    def send_password_changed_email(self, user) -> bool:
        return self._send(
            to=user.email,
            subject="Sua senha foi alterada — VoxterFlix",
            template_name="notifications/email/password_changed.html",
            context={"user": user},
            email_type=EmailLog.EmailType.PASSWORD_CHANGED,
        )

    # ------------------------------------------------------------------
    # Implementação interna
    # ------------------------------------------------------------------

    def _send(
        self,
        *,
        to: str,
        subject: str,
        template_name: str,
        context: dict,
        email_type: str,
        idempotency_key: str | None = None,
    ) -> bool:
        if not self.api_key:
            # A aplicação não deve quebrar nem fingir que enviou o e-mail
            # quando a integração não está configurada — apenas registra.
            logger.warning(
                "RESEND_API_KEY não configurada; e-mail '%s' para %s não foi enviado.",
                email_type,
                to,
            )
            EmailLog.objects.create(
                to_email=to,
                email_type=email_type,
                status=EmailLog.Status.SKIPPED,
                error="RESEND_API_KEY não configurada",
            )
            return False

        html_content = render_to_string(template_name, context)
        resend.api_key = self.api_key

        params: dict = {
            "from": f"{self.from_name} <{self.from_email}>",
            "to": [to],
            "subject": subject,
            "html": html_content,
        }

        try:
            if idempotency_key:
                response = resend.Emails.send(params, {"idempotency_key": idempotency_key})
            else:
                response = resend.Emails.send(params)
        except Exception as exc:  # noqa: BLE001 - falha do provedor não deve derrubar a requisição
            logger.error("Falha ao enviar e-mail '%s' para %s: %s", email_type, to, exc)
            EmailLog.objects.create(
                to_email=to,
                email_type=email_type,
                status=EmailLog.Status.FAILED,
                idempotency_key=idempotency_key or "",
                error=str(exc)[:500],
            )
            return False

        EmailLog.objects.create(
            to_email=to,
            email_type=email_type,
            status=EmailLog.Status.SENT,
            provider_message_id=response.get("id", "") if isinstance(response, dict) else "",
            idempotency_key=idempotency_key or "",
        )
        return True
