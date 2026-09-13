"""Views do catálogo: Home, busca avançada e página de detalhes."""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.catalog.forms import AdvancedSearchForm
from apps.catalog.models import Category
from apps.catalog.permissions import is_blocked_for_kids
from apps.catalog.services.omdb import (
    OMDbError,
    OMDbNotFoundError,
    OMDbRateLimitError,
    OMDbService,
    OMDbTimeoutError,
)
from apps.core.security import check_rate_limit
from apps.favorites.models import Favorite
from apps.history.models import WatchHistory
from apps.profiles.decorators import require_active_profile

logger = logging.getLogger("voxterflix")


@login_required
@require_active_profile
def home(request):
    """Home com banner em destaque e carrosséis por categoria."""
    omdb = OMDbService()
    is_kids = request.active_profile.is_kids

    categories_qs = Category.objects.prefetch_related("titles")
    if is_kids:
        categories_qs = categories_qs.filter(is_kids_allowed=True)

    carousels = []
    featured = None

    for category in categories_qs:
        items = []
        for curated in category.titles.all():
            detail = _safe_get_detail(omdb, curated.imdb_id)
            if detail is None:
                continue
            if is_kids and is_blocked_for_kids(rated=detail.rated, genre=detail.genre):
                continue
            items.append(detail)
            if curated.is_featured and featured is None and not is_kids:
                featured = detail
        if items:
            carousels.append({"category": category, "items": items})

    continue_watching = (
        WatchHistory.objects.filter(profile=request.active_profile, percent__lt=95)
        .order_by("-updated_at")[:15]
    )

    return render(
        request,
        "catalog/home.html",
        {"carousels": carousels, "featured": featured, "continue_watching": continue_watching},
    )


def _safe_get_detail(omdb: OMDbService, imdb_id: str):
    """Busca um detalhe da OMDb sem deixar uma falha pontual quebrar a Home."""
    try:
        return omdb.get_by_imdb_id(imdb_id)
    except OMDbError as exc:
        logger.warning("Falha ao carregar título curado %s: %s", imdb_id, exc)
        return None


@login_required
@require_active_profile
def search(request):
    """Busca avançada com filtros persistidos na URL (query params)."""
    form = AdvancedSearchForm(request.GET or None)
    results = []
    total = 0
    error_message = None

    if request.GET and form.is_valid():
        rate_key = f"search:{request.user.pk}"
        allowed, _ = check_rate_limit(rate_key, "30/1m")
        if not allowed:
            error_message = "Muitas buscas em pouco tempo. Aguarde um instante e tente novamente."
        else:
            omdb = OMDbService()
            query = form.cleaned_data["q"]
            page = form.cleaned_data.get("page") or 1
            try:
                results, total = omdb.search(
                    query,
                    type_=form.cleaned_data.get("type", ""),
                    page=page,
                )
                if form.has_advanced_filters():
                    results = _apply_advanced_filters(omdb, results, form.cleaned_data)
                else:
                    results = _apply_sort(results, form.cleaned_data.get("sort"), omdb)
            except OMDbNotFoundError:
                results, total = [], 0
            except OMDbRateLimitError:
                error_message = "O serviço de catálogo está temporariamente indisponível (limite da OMDb excedido)."
            except OMDbTimeoutError:
                error_message = "O serviço de catálogo demorou demais para responder. Tente novamente."
            except OMDbError as exc:
                error_message = str(exc)

    if request.active_profile.is_kids:
        # Resultados simples (busca sem filtros avançados) não trazem
        # classificação/gênero — nesse caso a restrição só pode ser
        # aplicada de fato na página de detalhes. Quando filtros avançados
        # já buscaram o detalhe completo, filtramos aqui mesmo.
        results = [
            r
            for r in results
            if not (hasattr(r, "rated") and is_blocked_for_kids(rated=r.rated, genre=r.genre))
        ]

    return render(
        request,
        "catalog/search.html",
        {
            "form": form,
            "results": results,
            "total": total,
            "error_message": error_message,
            "query_string": request.GET.urlencode(),
        },
    )


def _apply_advanced_filters(omdb: OMDbService, results, filters) -> list:
    """Refina os resultados buscando detalhes (limitado para não sobrecarregar a OMDb)."""
    detailed = []
    for item in results[:10]:
        detail = _safe_get_detail(omdb, item.imdb_id)
        if detail is None:
            continue

        if filters.get("genre") and filters["genre"].lower() not in detail.genre.lower():
            continue
        if filters.get("country") and filters["country"].lower() not in detail.country.lower():
            continue
        if filters.get("language") and filters["language"].lower() not in detail.language.lower():
            continue
        if filters.get("rated") and filters["rated"].lower() not in detail.rated.lower():
            continue
        if filters.get("actor") and filters["actor"].lower() not in detail.actors.lower():
            continue
        if filters.get("director") and filters["director"].lower() not in detail.director.lower():
            continue

        year_val = _safe_int(detail.year[:4] if detail.year else "")
        if filters.get("year_from") and year_val and year_val < filters["year_from"]:
            continue
        if filters.get("year_to") and year_val and year_val > filters["year_to"]:
            continue

        rating_val = _safe_float(detail.imdb_rating)
        if filters.get("rating_min") is not None and (rating_val is None or rating_val < filters["rating_min"]):
            continue
        if filters.get("rating_max") is not None and (rating_val is None or rating_val > filters["rating_max"]):
            continue

        detailed.append(detail)

    return _apply_sort(detailed, filters.get("sort"), omdb)


def _apply_sort(items, sort_key, omdb):
    if not sort_key or sort_key == "relevance":
        return items

    def year_of(item):
        return _safe_int(getattr(item, "year", "")[:4] if getattr(item, "year", "") else "") or 0

    def rating_of(item):
        if hasattr(item, "imdb_rating"):
            return _safe_float(item.imdb_rating) or 0
        detail = _safe_get_detail(omdb, item.imdb_id)
        return _safe_float(detail.imdb_rating) if detail else 0

    if sort_key == "year_desc":
        return sorted(items, key=year_of, reverse=True)
    if sort_key == "year_asc":
        return sorted(items, key=year_of)
    if sort_key == "rating_desc":
        return sorted(items, key=rating_of, reverse=True)
    if sort_key == "rating_asc":
        return sorted(items, key=rating_of)
    return items


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@login_required
@require_active_profile
def detail(request, imdb_id):
    """Página de detalhes de um filme/série."""
    omdb = OMDbService()
    try:
        title = omdb.get_by_imdb_id(imdb_id)
    except OMDbNotFoundError:
        messages.error(request, "Título não encontrado.")
        return redirect("catalog:home")
    except OMDbError as exc:
        messages.error(request, f"Não foi possível carregar este título agora: {exc}")
        return redirect("catalog:home")

    if request.active_profile.is_kids and is_blocked_for_kids(rated=title.rated, genre=title.genre):
        messages.warning(request, "Este título não está disponível no perfil infantil.")
        return redirect("catalog:home")

    is_favorite = Favorite.objects.filter(profile=request.active_profile, imdb_id=imdb_id).exists()

    total_seasons = _safe_int(title.total_seasons) or 0
    seasons_range = range(1, total_seasons + 1) if total_seasons else []

    return render(
        request,
        "catalog/detail.html",
        {"title": title, "is_favorite": is_favorite, "seasons_range": seasons_range},
    )
