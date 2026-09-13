"""Regras de restrição de conteúdo para perfis infantis.

A regra é aplicada sempre no backend (views), nunca só escondendo botões
no template — um perfil infantil não deve conseguir acessar detalhes ou
o player de um título restrito nem digitando a URL diretamente.
"""

_CLASSIFICACOES_BLOQUEADAS = {"R", "NC-17", "TV-MA", "18", "18+"}
_GENEROS_BLOQUEADOS = {"horror", "crime", "war", "thriller"}


def is_blocked_for_kids(*, rated: str = "", genre: str = "") -> bool:
    """Retorna True se o título não deve ser exibido/reproduzido em perfil infantil."""
    rated_normalizado = (rated or "").strip().upper()
    if rated_normalizado in _CLASSIFICACOES_BLOQUEADAS:
        return True

    generos = {g.strip().lower() for g in (genre or "").split(",") if g.strip()}
    if generos & _GENEROS_BLOQUEADOS:
        return True

    return False
