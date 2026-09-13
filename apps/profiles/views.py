"""Views de seleção e gerenciamento de perfis."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.profiles.forms import ProfileForm
from apps.profiles.models import Profile


@login_required
def select_profile(request):
    """Tela "Quem está assistindo?" com os perfis da conta."""
    profiles = Profile.objects.filter(user=request.user)
    return render(request, "profiles/select.html", {"profiles": profiles})


@login_required
def activate_profile(request, profile_id):
    """Define o perfil escolhido como perfil ativo na sessão."""
    profile = get_object_or_404(Profile, pk=profile_id, user=request.user)
    request.session["active_profile_id"] = profile.pk
    return redirect("catalog:home")


@login_required
def manage_profiles(request):
    """Lista de perfis com opções de criar/editar/excluir."""
    profiles = Profile.objects.filter(user=request.user)
    return render(
        request,
        "profiles/manage.html",
        {
            "profiles": profiles,
            "max_profiles": settings.MAX_PROFILES_PER_USER,
            "can_add": profiles.count() < settings.MAX_PROFILES_PER_USER,
        },
    )


@login_required
def create_profile(request):
    """Cria um novo perfil, respeitando o limite por conta."""
    if request.method == "POST":
        form = ProfileForm(request.POST, user=request.user)
        # Precisa ser atribuído antes de is_valid(): o ModelForm chama
        # instance.full_clean() durante a validação, e Profile.clean()
        # depende de self.user já estar definido para contar os perfis
        # existentes (senão explode com RelatedObjectDoesNotExist).
        form.instance.user = request.user
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil criado com sucesso.")
            return redirect("profiles:gerenciar")
    else:
        form = ProfileForm(user=request.user)
    return render(request, "profiles/form.html", {"form": form, "titulo": "Novo perfil"})


@login_required
def edit_profile(request, profile_id):
    """Edita nome, avatar ou tipo (infantil) de um perfil existente."""
    profile = get_object_or_404(Profile, pk=profile_id, user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect("profiles:gerenciar")
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, "profiles/form.html", {"form": form, "titulo": "Editar perfil"})


@login_required
@require_http_methods(["POST"])
def delete_profile(request, profile_id):
    """Remove um perfil e limpa a sessão caso ele estivesse ativo."""
    profile = get_object_or_404(Profile, pk=profile_id, user=request.user)
    profile.delete()
    if request.session.get("active_profile_id") == profile_id:
        request.session.pop("active_profile_id", None)
    messages.success(request, "Perfil removido.")
    return redirect("profiles:gerenciar")
