"""Modelos compartilhados entre os demais apps do VoxterFlix."""

from django.db import models


class TimestampedModel(models.Model):
    """Modelo abstrato com campos de auditoria temporal.

    Reaproveitado por vários apps para evitar repetir `created_at`/`updated_at`
    (princípio DRY) e manter um padrão único de auditoria no projeto.
    """

    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


class SecurityEvent(TimestampedModel):
    """Registro de eventos relevantes de segurança.

    Guardamos apenas metadados do evento (tipo, IP, usuário, rota) — nunca
    senha, token ou chave de API — para permitir auditoria sem criar um
    novo vetor de exposição de segredos.
    """

    class EventType(models.TextChoices):
        LOGIN_SUCCESS = "login_success", "Login bem-sucedido"
        LOGIN_FAILED = "login_failed", "Falha de login"
        LOGIN_BLOCKED = "login_blocked", "Login bloqueado por rate limit"
        SIGNUP = "signup", "Cadastro realizado"
        PASSWORD_RESET_REQUESTED = "password_reset_requested", "Recuperação de senha solicitada"
        PASSWORD_RESET_COMPLETED = "password_reset_completed", "Senha redefinida"
        EMAIL_CONFIRMED = "email_confirmed", "E-mail confirmado"
        RATE_LIMIT_BLOCKED = "rate_limit_blocked", "Ação bloqueada por rate limit"
        PLAYER_ACCESS = "player_access", "Acesso ao player"
        PLAYER_DENIED = "player_denied", "Acesso ao player negado"

    event_type = models.CharField("tipo de evento", max_length=40, choices=EventType.choices)
    user = models.ForeignKey(
        "auth.User", verbose_name="usuário", null=True, blank=True, on_delete=models.SET_NULL
    )
    ip_address = models.GenericIPAddressField("endereço IP", null=True, blank=True)
    path = models.CharField("rota", max_length=255, blank=True)
    metadata = models.JSONField("metadados", default=dict, blank=True)

    class Meta:
        verbose_name = "evento de segurança"
        verbose_name_plural = "eventos de segurança"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["ip_address", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} ({self.created_at:%d/%m/%Y %H:%M})"
