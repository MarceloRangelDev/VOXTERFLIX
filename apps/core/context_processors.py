"""Context processors globais do VoxterFlix."""

from django.conf import settings


def voxterflix_context(request):
    """Expõe dados usados em praticamente todos os templates.

    Evita repetir `{% if request.session.active_profile_id %}` em cada view:
    o perfil ativo (definido pelo ActiveProfileMiddleware) já chega pronto.
    """
    return {
        "site_name": settings.SITE_NAME,
        "active_profile": getattr(request, "active_profile", None),
    }
