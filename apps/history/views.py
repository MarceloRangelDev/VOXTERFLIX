"""Views de histórico de visualização."""

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.history.models import WatchHistory
from apps.profiles.decorators import require_active_profile


@login_required
@require_active_profile
def history_list(request):
    """Lista completa do histórico do perfil ativo, mais recente primeiro."""
    items = WatchHistory.objects.filter(profile=request.active_profile)
    return render(request, "history/list.html", {"items": items})


@login_required
@require_active_profile
@require_POST
def remove_history_item(request, pk):
    """Remove uma entrada do histórico."""
    item = get_object_or_404(WatchHistory, pk=pk, profile=request.active_profile)
    item.delete()
    messages.success(request, "Item removido do histórico.")
    return redirect("history:lista")


@login_required
@require_active_profile
@require_POST
def update_progress(request):
    """Endpoint chamado pelo player (JS) para registrar o progresso.

    Recebe JSON e faz upsert por (perfil, imdb_id, temporada, episódio),
    já que o mesmo episódio pode ser reaberto várias vezes.
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido."}, status=400)

    imdb_id = payload.get("imdb_id", "")
    if not imdb_id:
        return JsonResponse({"ok": False, "error": "imdb_id é obrigatório."}, status=400)

    duration = max(int(payload.get("duration_seconds") or 0), 0)
    progress = max(int(payload.get("progress_seconds") or 0), 0)
    percent = round(min(progress / duration * 100, 100), 2) if duration else 0

    WatchHistory.objects.update_or_create(
        profile=request.active_profile,
        imdb_id=imdb_id,
        season=int(payload.get("season") or 0),
        episode=int(payload.get("episode") or 0),
        defaults={
            "title": payload.get("title", "")[:255],
            "poster": payload.get("poster", "")[:500],
            "type": payload.get("type", "")[:10],
            "progress_seconds": progress,
            "duration_seconds": duration,
            "percent": percent,
        },
    )
    return JsonResponse({"ok": True})
