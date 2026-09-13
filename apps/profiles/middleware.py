"""Middleware que resolve o perfil ativo a partir da sessão."""

from apps.profiles.models import Profile


class ActiveProfileMiddleware:
    """Anexa `request.active_profile` em toda requisição autenticada.

    Guardamos apenas o ID do perfil na sessão (não o objeto), e resolvemos
    o objeto aqui. Se o perfil guardado não existir mais ou não pertencer
    ao usuário logado (ex.: sessão antiga, perfil excluído), limpamos a
    sessão em vez de deixar o restante da aplicação lidar com um estado
    inconsistente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.active_profile = None

        if request.user.is_authenticated:
            profile_id = request.session.get("active_profile_id")
            if profile_id:
                profile = Profile.objects.filter(pk=profile_id, user=request.user).first()
                if profile:
                    request.active_profile = profile
                else:
                    request.session.pop("active_profile_id", None)

        return self.get_response(request)
