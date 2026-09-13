"""Decorators de controle de acesso relacionados a perfis."""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def require_active_profile(view_func):
    """Garante que exista um perfil selecionado antes de acessar a view.

    Funcionalidades como favoritos, histórico e player fazem sentido apenas
    no contexto de um perfil específico. Sem isso, redirecionamos para a
    tela "Quem está assistindo?" em vez de deixar a view falhar.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.active_profile is None:
            messages.info(request, "Selecione um perfil para continuar.")
            return redirect("profiles:selecionar")
        return view_func(request, *args, **kwargs)

    return wrapper
