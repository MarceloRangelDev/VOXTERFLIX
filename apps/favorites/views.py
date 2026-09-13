"""Views de gerenciamento da lista de favoritos."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.services.omdb import OMDbError, OMDbService
from apps.favorites.models import Favorite
from apps.profiles.decorators import require_active_profile


@login_required
@require_active_profile
def my_list(request):
    """Exibe a lista de favoritos do perfil ativo."""
    favorites = Favorite.objects.filter(profile=request.active_profile)
    return render(request, "favorites/list.html", {"favorites": favorites})


@login_required
@require_active_profile
@require_POST
def toggle_favorite(request, imdb_id):
    """Adiciona ou remove um título da lista do perfil ativo.

    Se já existir, remove (toggle); se não existir, busca o mínimo de dados
    na OMDb (cacheados) para guardar a "foto" usada na listagem.
    """
    profile = request.active_profile
    existing = Favorite.objects.filter(profile=profile, imdb_id=imdb_id).first()

    if existing:
        existing.delete()
        messages.success(request, "Removido da sua lista.")
        is_favorite = False
    else:
        try:
            detail = OMDbService().get_by_imdb_id(imdb_id)
            Favorite.objects.create(
                profile=profile,
                imdb_id=imdb_id,
                title=detail.title,
                poster=detail.poster,
                year=detail.year,
                type=detail.type,
            )
            messages.success(request, "Adicionado à sua lista.")
            is_favorite = True
        except OMDbError as exc:
            messages.error(request, f"Não foi possível adicionar: {exc}")
            is_favorite = False

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "catalog:home"
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("catalog:home")
