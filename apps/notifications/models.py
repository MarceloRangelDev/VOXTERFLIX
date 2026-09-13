"""Registro de e-mails enviados (auditoria e idempotência)."""

from django.db import models

from apps.core.models import TimestampedModel


class EmailLog(TimestampedModel):
    """Guarda o resultado de cada tentativa de envio via Resend.

    Nunca armazena o conteúdo do e-mail nem tokens — apenas o suficiente
    para auditoria (para quem, que tipo, se deu certo) e para permitir
    verificações de idempotência (evitar reenviar o mesmo e-mail).
    """

    class EmailType(models.TextChoices):
        CONFIRMATION = "confirmation", "Confirmação de e-mail"
        WELCOME = "welcome", "Boas-vindas"
        PASSWORD_RESET = "password_reset", "Recuperação de senha"
        PASSWORD_CHANGED = "password_changed", "Alteração de senha"

    class Status(models.TextChoices):
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falhou"
        SKIPPED = "skipped", "Não enviado (sem configuração)"

    to_email = models.EmailField("destinatário")
    email_type = models.CharField("tipo", max_length=30, choices=EmailType.choices)
    status = models.CharField("status", max_length=20, choices=Status.choices)
    provider_message_id = models.CharField("id da mensagem no provedor", max_length=100, blank=True)
    idempotency_key = models.CharField("chave de idempotência", max_length=150, blank=True)
    error = models.CharField("erro", max_length=500, blank=True)

    class Meta:
        verbose_name = "e-mail enviado"
        verbose_name_plural = "e-mails enviados"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["to_email", "email_type", "created_at"])]

    def __str__(self) -> str:
        return f"{self.get_email_type_display()} -> {self.to_email} ({self.status})"
