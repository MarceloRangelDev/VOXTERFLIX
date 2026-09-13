"""Histórico de visualização por perfil ("Continuar assistindo")."""

from django.db import models

from apps.core.models import TimestampedModel
from apps.profiles.models import Profile


class WatchHistory(TimestampedModel):
    """Progresso de reprodução de um título (ou episódio) para um perfil.

    Guardamos `season`/`episode` como opcionais: para filmes ficam vazios;
    para séries, cada episódio tem sua própria linha, permitindo retomar
    exatamente o episódio que estava sendo visto.
    """

    profile = models.ForeignKey(Profile, verbose_name="perfil", related_name="history", on_delete=models.CASCADE)
    imdb_id = models.CharField("IMDb ID", max_length=20)
    title = models.CharField("título", max_length=255)
    poster = models.URLField("poster", max_length=500, blank=True)
    type = models.CharField("tipo", max_length=10, blank=True)
    # 0 representa "não se aplica" (filme). Evitamos NULL aqui porque
    # NULL não é comparável a NULL em UniqueConstraint (SQLite/PostgreSQL
    # tratariam duas linhas com season/episode nulos como não-duplicadas).
    season = models.PositiveIntegerField("temporada", default=0, blank=True)
    episode = models.PositiveIntegerField("episódio", default=0, blank=True)
    progress_seconds = models.PositiveIntegerField("progresso (segundos)", default=0)
    duration_seconds = models.PositiveIntegerField("duração (segundos)", default=0)
    percent = models.FloatField("percentual concluído", default=0)

    class Meta:
        verbose_name = "histórico de visualização"
        verbose_name_plural = "históricos de visualização"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "imdb_id", "season", "episode"], name="progresso_unico_por_episodio"
            ),
        ]

    def __str__(self) -> str:
        sufixo = f" T{self.season}E{self.episode}" if self.season else ""
        return f"{self.title}{sufixo} — {self.profile.name} ({self.percent:.0f}%)"

    @property
    def is_finished(self) -> bool:
        # Consideramos "concluído" a partir de 95% para não exigir 100%
        # exato (o player pode nunca reportar exatamente o fim do vídeo).
        return self.percent >= 95
