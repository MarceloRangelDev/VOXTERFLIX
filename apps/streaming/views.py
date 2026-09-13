"""Views do player de streaming.

Fluxo: Detalhes -> "Assistir" -> esta view -> SuperFlixService -> template
do player. O frontend nunca recebe uma URL arbitrária; ele só recebe a URL
de embed já validada e montada pelo backend.
"""

import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.catalog.permissions import is_blocked_for_kids
from apps.catalog.services.omdb import OMDbError, OMDbNotFoundError, OMDbService
from apps.core.security import check_rate_limit, log_security_event
from apps.profiles.decorators import require_active_profile
from apps.streaming.services.superflix import (
    InvalidPlaybackRequestError,
    SuperFlixNotConfiguredError,
    SuperFlixService,
)


@login_required
@require_active_profile
def play_movie(request, imdb_id):
    return _play(request, imdb_id, season=None, episode=None)


@login_required
@require_active_profile
def play_episode(request, imdb_id, season, episode):
    return _play(request, imdb_id, season=season, episode=episode)


def _play(request, imdb_id, *, season, episode):
    allowed, _ = check_rate_limit(f"player:{request.user.pk}", "60/1m")
    if not allowed:
        log_security_event("rate_limit_blocked", request, user=request.user, contexto="player", imdb_id=imdb_id)
        return render(
            request,
            "streaming/player.html",
            {"error_message": "Muitas requisições ao player em pouco tempo. Aguarde um instante."},
        )

    omdb = OMDbService()
    try:
        title = omdb.get_by_imdb_id(imdb_id)
    except OMDbNotFoundError:
        log_security_event("player_denied", request, user=request.user, motivo="titulo_nao_encontrado", imdb_id=imdb_id)
        return render(request, "streaming/player.html", {"error_message": "Título não encontrado."})
    except OMDbError as exc:
        return render(request, "streaming/player.html", {"error_message": f"Catálogo indisponível: {exc}"})

    if request.active_profile.is_kids and is_blocked_for_kids(rated=title.rated, genre=title.genre):
        log_security_event("player_denied", request, user=request.user, motivo="restricao_infantil", imdb_id=imdb_id)
        return render(
            request,
            "streaming/player.html",
            {"error_message": "Este título não está disponível no perfil infantil."},
        )

    superflix = SuperFlixService()
    try:
        if season is not None:
            source = superflix.build_episode_source(imdb_id, season, episode)
        else:
            source = superflix.build_movie_source(imdb_id)
    except SuperFlixNotConfiguredError:
        return render(
            request,
            "streaming/player.html",
            {
                "title": title,
                "error_message": (
                    "O player ainda não está configurado neste ambiente. "
                    "Defina SUPERFLIX_API_BASE_URL no arquivo .env para habilitar a reprodução."
                ),
            },
        )
    except InvalidPlaybackRequestError as exc:
        log_security_event("player_denied", request, user=request.user, motivo="parametros_invalidos", detalhe=str(exc))
        return render(request, "streaming/player.html", {"error_message": "Não foi possível reproduzir este conteúdo."})

    log_security_event(
        "player_access",
        request,
        user=request.user,
        imdb_id=imdb_id,
        season=season,
        episode=episode,
    )

    return render(
        request,
        "streaming/player.html",
        {
            "title": title,
            "embed_url": source.embed_url,
            "season": season,
            "episode": episode,
            "duration_seconds": _parse_runtime_seconds(title.runtime),
        },
    )


def _parse_runtime_seconds(runtime: str) -> int:
    """Converte o campo "Runtime" da OMDb (ex.: "142 min") em segundos.

    Usado só como referência para a estimativa de progresso do player (ver
    `static/js/player.js`) — sem acesso ao player interno da SuperFlixAPI,
    não há como medir o tempo real de reprodução.
    """
    match = re.search(r"(\d+)", runtime or "")
    return int(match.group(1)) * 60 if match else 0
