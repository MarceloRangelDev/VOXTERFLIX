"""Integração com a SuperFlixAPI.

A SuperFlixAPI funciona por *embed*: o player completo já vem dentro de
uma página servida pelo provedor, incluída via `<iframe>`. O padrão de URL
usado pela API (confirmado na documentação oficial em superflixapi.rest/doc
e replicado por integrações de terceiros que consomem a mesma API, como
github.com/TheusN/superflix) é:

    Filme:   {base_url}/filme/{imdb_id}
    Série:   {base_url}/serie/{imdb_id}/{temporada}/{episodio}

Não existe (nem é documentado publicamente) um endpoint que devolva um
JSON com as fontes de vídeo "puras" — por isso este serviço não inventa
esse tipo de chamada. Ele apenas monta, com validação estrita de entrada,
a URL do iframe que o template `streaming/player.html` vai renderizar.

O domínio da API já teve várias mudanças de TLD ao longo do tempo (.rest,
.pro, .my, .asia, .sbs, .top, .shop) — por isso o domínio nunca é
hardcoded: ele vem de `SUPERFLIX_API_BASE_URL` no `.env`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.conf import settings

IMDB_ID_PATTERN = re.compile(r"^tt\d{6,9}$")


class SuperFlixError(Exception):
    """Erro genérico da integração com a SuperFlixAPI."""


class SuperFlixNotConfiguredError(SuperFlixError):
    """`SUPERFLIX_API_BASE_URL` não foi definida no `.env`."""


class InvalidPlaybackRequestError(SuperFlixError):
    """Os parâmetros de reprodução (IMDb ID, temporada, episódio) são inválidos."""


@dataclass(frozen=True)
class PlaybackSource:
    """Dados prontos para o template do player."""

    embed_url: str
    kind: str  # "movie" ou "series"


class SuperFlixService:
    """Monta URLs de embed validadas para o player de streaming."""

    def __init__(self) -> None:
        self.base_url = (settings.SUPERFLIX_API_BASE_URL or "").rstrip("/")

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def build_movie_source(self, imdb_id: str) -> PlaybackSource:
        """Monta a URL de embed de um filme.

        Levanta `SuperFlixNotConfiguredError` se a integração não estiver
        configurada — a view decide como exibir isso ao usuário, sem que
        o restante da aplicação quebre.
        """
        self._validate_imdb_id(imdb_id)
        if not self.is_configured():
            raise SuperFlixNotConfiguredError(
                "SUPERFLIX_API_BASE_URL não configurada. Defina essa variável no .env para habilitar o player."
            )
        return PlaybackSource(embed_url=f"{self.base_url}/filme/{imdb_id}", kind="movie")

    def build_episode_source(self, imdb_id: str, season: int, episode: int) -> PlaybackSource:
        """Monta a URL de embed de um episódio de série/anime/dorama."""
        self._validate_imdb_id(imdb_id)
        season = self._validate_positive_int(season, "temporada")
        episode = self._validate_positive_int(episode, "episódio")
        if not self.is_configured():
            raise SuperFlixNotConfiguredError(
                "SUPERFLIX_API_BASE_URL não configurada. Defina essa variável no .env para habilitar o player."
            )
        return PlaybackSource(embed_url=f"{self.base_url}/serie/{imdb_id}/{season}/{episode}", kind="series")

    @staticmethod
    def _validate_imdb_id(imdb_id: str) -> None:
        # Nunca aceitamos uma URL arbitrária vinda do usuário — apenas um
        # IMDb ID no formato correto, que é então usado para montar a URL
        # final no backend. Isso evita SSRF, open redirect e proxy arbitrário.
        if not imdb_id or not IMDB_ID_PATTERN.match(imdb_id):
            raise InvalidPlaybackRequestError("IMDb ID inválido.")

    @staticmethod
    def _validate_positive_int(value, label: str) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise InvalidPlaybackRequestError(f"Valor de {label} inválido.") from exc
        if parsed < 1:
            raise InvalidPlaybackRequestError(f"Valor de {label} deve ser maior que zero.")
        return parsed
