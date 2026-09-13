"""Utilitários de segurança compartilhados: logging de eventos e rate limiting.

Centralizamos essas funções aqui para que accounts, catalog e streaming
não precisem reimplementar a mesma lógica (DRY) e para que a política de
"o que é registrado" e "como é limitado" fique em um único lugar.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from django.core.cache import cache
from django.http import HttpRequest

from apps.core.models import SecurityEvent

security_logger = logging.getLogger("voxterflix.security")


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """Obtém o IP real do cliente, considerando proxies reversos comuns."""
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_security_event(
    event_type: str,
    request: Optional[HttpRequest] = None,
    user=None,
    **metadata,
) -> None:
    """Registra um evento de segurança no log e no banco.

    Nunca deve receber senha, token ou chave de API em `metadata` — apenas
    informações que ajudem a investigar um incidente (ex.: username tentado,
    motivo do bloqueio).
    """
    ip_address = get_client_ip(request) if request else None
    path = request.path if request else ""

    security_logger.info(
        "%s | usuario=%s | ip=%s | path=%s | %s",
        event_type,
        getattr(user, "username", None) or metadata.get("username"),
        ip_address,
        path,
        metadata,
    )

    SecurityEvent.objects.create(
        event_type=event_type,
        user=user if user and getattr(user, "is_authenticated", False) else None,
        ip_address=ip_address,
        path=path,
        metadata=metadata,
    )


_RATE_LIMIT_PATTERN = re.compile(r"^(\d+)/(\d+)([smh])$")

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600}


def parse_rate_limit(rate: str) -> tuple[int, int]:
    """Converte uma string como "3/15m" em (limite=3, janela_em_segundos=900)."""
    match = _RATE_LIMIT_PATTERN.match(rate.strip())
    if not match:
        raise ValueError(f"Formato de rate limit inválido: {rate!r}")
    limit, amount, unit = match.groups()
    return int(limit), int(amount) * _UNIT_SECONDS[unit]


def is_rate_limited(key: str, rate: str) -> bool:
    """Verifica (sem incrementar) se `key` já atingiu o limite."""
    limit, _ = parse_rate_limit(rate)
    attempts = cache.get(f"ratelimit:{key}", 0)
    return attempts >= limit


def register_attempt(key: str, rate: str) -> int:
    """Incrementa o contador de tentativas de `key` e retorna o total atual."""
    _, window_seconds = parse_rate_limit(rate)
    cache_key = f"ratelimit:{key}"
    # add() só define o valor se a chave não existir, preservando o TTL
    # da primeira tentativa dentro da janela.
    cache.add(cache_key, 0, timeout=window_seconds)
    return cache.incr(cache_key)


def check_rate_limit(key: str, rate: str) -> tuple[bool, int]:
    """Verifica e incrementa em uma única chamada.

    Uso típico: ações em que toda chamada conta contra o limite (busca,
    endpoints do player). Para login — onde só tentativas *falhas* devem
    contar — use `is_rate_limited`/`register_attempt` separadamente.
    """
    if is_rate_limited(key, rate):
        return False, 0
    total = register_attempt(key, rate)
    limit, _ = parse_rate_limit(rate)
    return True, max(limit - total, 0)


def reset_rate_limit(key: str) -> None:
    """Limpa o contador (ex.: após um login bem-sucedido)."""
    cache.delete(f"ratelimit:{key}")
