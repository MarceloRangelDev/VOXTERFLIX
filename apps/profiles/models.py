"""Modelo de perfis (múltiplos perfis por conta, como em plataformas de streaming)."""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimestampedModel

# Avatares pré-definidos (ícones + cor), evitando a necessidade de upload de
# arquivos para um recurso que é apenas decorativo.
AVATAR_CHOICES = [
    ("azul", "Azul"),
    ("ciano", "Ciano"),
    ("verde", "Verde"),
    ("laranja", "Laranja"),
    ("roxo", "Roxo"),
    ("vermelho", "Vermelho"),
]


class Profile(TimestampedModel):
    """Um perfil pertencente a um usuário (conta).

    Cada usuário pode ter até `MAX_PROFILES_PER_USER` perfis (configurável
    via `.env`). Favoritos e histórico são sempre vinculados ao perfil, não
    diretamente ao usuário, para que cada perfil tenha sua própria experiência.
    """

    user = models.ForeignKey(User, verbose_name="usuário", related_name="profiles", on_delete=models.CASCADE)
    name = models.CharField("nome", max_length=50)
    avatar = models.CharField("avatar", max_length=20, choices=AVATAR_CHOICES, default="azul")
    is_kids = models.BooleanField("perfil infantil", default=False)

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfis"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="perfil_unico_por_usuario"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.user.username})"

    def clean(self):
        """Impede criar um novo perfil além do limite configurado.

        A validação fica no model (e é reforçada no form) para que nenhuma
        outra via de criação (admin, shell, futura API) escape da regra.
        """
        if self.pk is None:
            total = Profile.objects.filter(user=self.user).count()
            if total >= settings.MAX_PROFILES_PER_USER:
                raise ValidationError(
                    f"Limite de {settings.MAX_PROFILES_PER_USER} perfis por conta atingido."
                )
