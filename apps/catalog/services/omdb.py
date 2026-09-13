"""Integração com a OMDb API (https://www.omdbapi.com/).

Este é o único ponto do projeto que conhece a estrutura de requisição e
resposta da OMDb. Views e templates nunca fazem requests HTTP diretamente —
sempre passam por `OMDbService`, o que facilita testes (mockando a classe)
e troca futura de provedor.

Parâmetros e formato de resposta confirmados na documentação oficial em
https://www.omdbapi.com/ (busca por título com `s=`, por ID com `i=`,
detalhe com `plot=full`, erros vêm como `{"Response": "False", "Error": "..."}`).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("voxterflix")


class OMDbError(Exception):
    """Erro genérico de comunicação com a OMDb."""


class OMDbTimeoutError(OMDbError):
    """A OMDb não respondeu dentro do tempo limite configurado."""


class OMDbNotFoundError(OMDbError):
    """A OMDb respondeu, mas o título não foi encontrado."""


class OMDbRateLimitError(OMDbError):
    """A OMDb sinalizou limite de requisições/chave inválida."""


@dataclass
class TitleSummary:
    """Representação normalizada de um item de busca (endpoint `s=`)."""

    imdb_id: str
    title: str
    year: str
    type: str
    poster: str


@dataclass
class TitleDetail:
    """Representação normalizada dos detalhes de um título (endpoint `i=`)."""

    imdb_id: str
    title: str
    year: str
    type: str
    poster: str
    plot: str = ""
    genre: str = ""
    director: str = ""
    writer: str = ""
    actors: str = ""
    runtime: str = ""
    rated: str = ""
    country: str = ""
    language: str = ""
    imdb_rating: str = ""
    imdb_votes: str = ""
    total_seasons: Optional[str] = None
    raw: dict = field(default_factory=dict)


class OMDbService:
    """Cliente HTTP para a OMDb API, com cache e tratamento de erros.

    Docstrings e comentários em português explicam as decisões que não são
    óbvias apenas lendo o código (por que cachear, por que tratar cada erro
    de um jeito específico).
    """

    def __init__(self) -> None:
        self.api_key = settings.OMDB_API_KEY
        self.base_url = settings.OMDB_BASE_URL
        self.timeout = settings.OMDB_TIMEOUT
        self.cache_ttl = settings.OMDB_CACHE_TTL

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def search(self, query: str, *, type_: str = "", year: str = "", page: int = 1) -> tuple[list[TitleSummary], int]:
        """Busca títulos por palavra-chave. Retorna (resultados, total_encontrado)."""
        params = {"s": query, "page": max(1, min(page, 100))}
        if type_:
            params["type"] = type_
        if year:
            params["y"] = year

        data = self._request(params, cache_prefix="search")
        results = [
            TitleSummary(
                imdb_id=item.get("imdbID", ""),
                title=item.get("Title", ""),
                year=item.get("Year", ""),
                type=item.get("Type", ""),
                poster=self._normalize_poster(item.get("Poster")),
            )
            for item in data.get("Search", [])
        ]
        total = int(data.get("totalResults", 0) or 0)
        return results, total

    def get_by_imdb_id(self, imdb_id: str) -> TitleDetail:
        """Busca os detalhes completos de um título pelo IMDb ID."""
        if not imdb_id:
            raise OMDbNotFoundError("IMDb ID vazio.")

        data = self._request({"i": imdb_id, "plot": "full"}, cache_prefix="detail")
        return TitleDetail(
            imdb_id=data.get("imdbID", imdb_id),
            title=data.get("Title", ""),
            year=data.get("Year", ""),
            type=data.get("Type", ""),
            poster=self._normalize_poster(data.get("Poster")),
            plot=self._clean(data.get("Plot")),
            genre=self._clean(data.get("Genre")),
            director=self._clean(data.get("Director")),
            writer=self._clean(data.get("Writer")),
            actors=self._clean(data.get("Actors")),
            runtime=self._clean(data.get("Runtime")),
            rated=self._clean(data.get("Rated")),
            country=self._clean(data.get("Country")),
            language=self._clean(data.get("Language")),
            imdb_rating=self._clean(data.get("imdbRating")),
            imdb_votes=self._clean(data.get("imdbVotes")),
            total_seasons=data.get("totalSeasons"),
            raw=data,
        )

    # ------------------------------------------------------------------
    # Implementação interna
    # ------------------------------------------------------------------

    @staticmethod
    def _clean(value: Optional[str]) -> str:
        """A OMDb usa a string literal "N/A" para campos ausentes."""
        if not value or value == "N/A":
            return ""
        return value

    @staticmethod
    def _normalize_poster(poster: Optional[str]) -> str:
        if not poster or poster == "N/A":
            return ""
        return poster

    def _cache_key(self, prefix: str, params: dict) -> str:
        ordered = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"omdb:{prefix}:{ordered}"

    def _request(self, params: dict, *, cache_prefix: str) -> dict[str, Any]:
        if not self.api_key:
            raise OMDbError(
                "OMDB_API_KEY não configurada. Defina a variável de ambiente para usar o catálogo."
            )

        cache_key = self._cache_key(cache_prefix, params)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        request_params = {**params, "apikey": self.api_key, "r": "json"}

        try:
            response = requests.get(self.base_url, params=request_params, timeout=self.timeout)
        except requests.Timeout as exc:
            logger.warning("Timeout ao consultar a OMDb: %s", params)
            raise OMDbTimeoutError("A OMDb não respondeu a tempo.") from exc
        except requests.RequestException as exc:
            logger.error("Erro de rede ao consultar a OMDb: %s", exc)
            raise OMDbError("Não foi possível conectar à OMDb.") from exc

        if response.status_code == 401:
            raise OMDbRateLimitError("Chave da OMDb inválida ou limite de requisições excedido.")
        if response.status_code >= 500:
            raise OMDbError(f"A OMDb retornou erro do servidor ({response.status_code}).")
        if response.status_code >= 400:
            raise OMDbError(f"A OMDb retornou erro na requisição ({response.status_code}).")

        try:
            data = response.json()
        except ValueError as exc:
            raise OMDbError("Resposta inválida da OMDb (JSON malformado).") from exc

        if str(data.get("Response")) == "False":
            error_message = data.get("Error", "Título não encontrado.")
            if "not found" in error_message.lower():
                raise OMDbNotFoundError(error_message)
            if "request limit" in error_message.lower() or "invalid api key" in error_message.lower():
                raise OMDbRateLimitError(error_message)
            raise OMDbError(error_message)

        # Só cacheamos respostas de sucesso — erros nunca devem "colar"
        # no cache, senão um problema temporário pareceria permanente.
        cache.set(cache_key, data, timeout=self.cache_ttl)
        return data
