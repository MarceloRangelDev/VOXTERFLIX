"""Modelo de favoritos ("Minha Lista"), sempre vinculado a um perfil."""

from django.db import models

from apps.core.models import TimestampedModel
from apps.profiles.models import Profile


class Favorite(TimestampedModel):
    """Um título salvo na lista de um perfil específico.

    A relação é Profile -> título (não User -> título), porque cada perfil
    de uma mesma conta deve ter sua própria lista, igual a uma plataforma
    de streaming real. Guardamos uma pequena "foto" dos dados (título,
    poster, ano, tipo) para exibir a lista sem precisar consultar a OMDb
    a cada carregamento — só o suficiente para a UI, o resto vem sob demanda.
    """

    profile = models.ForeignKey(Profile, verbose_name="perfil", related_name="favorites", on_delete=models.CASCADE)
    imdb_id = models.CharField("IMDb ID", max_length=20)
    title = models.CharField("título", max_length=255)
    poster = models.URLField("poster", max_length=500, blank=True)
    year = models.CharField("ano", max_length=10, blank=True)
    type = models.CharField("tipo", max_length=10, blank=True)

    class Meta:
        verbose_name = "favorito"
        verbose_name_plural = "favoritos"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["profile", "imdb_id"], name="favorito_unico_por_perfil"),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.profile.name})"
