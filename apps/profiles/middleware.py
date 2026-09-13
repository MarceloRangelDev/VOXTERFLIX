"""Middleware que resolve o perfil ativo a partir da sessão."""

from django.contrib import messages
from django.shortcuts import redirect

from apps.profiles.models import Profile

# Prefixo usado para montar o Django Admin em config/urls.py
# (`path("admin/", admin.site.urls)`). Comparamos contra ele para bloquear
# o acesso à administração quando o perfil ativo é infantil, mesmo que a
# conta logada seja de um usuário staff/superuser.
ADMIN_PATH_PREFIX = "/admin/"


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

        # Restrição de perfil infantil aplicada no backend: mesmo que a
        # conta seja staff/superuser, enquanto o perfil ativo na sessão for
        # infantil, a administração fica bloqueada. O link também é
        # escondido no template (navbar), mas isso sozinho não impediria
        # o acesso direto pela URL — por isso a checagem vive aqui.
        if request.active_profile and request.active_profile.is_kids:
            if request.path.startswith(ADMIN_PATH_PREFIX):
                messages.warning(request, "A administração não está disponível em perfis infantis.")
                return redirect("profiles:selecionar")

        return self.get_response(request)
