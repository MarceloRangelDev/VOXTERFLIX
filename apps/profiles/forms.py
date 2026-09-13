"""Formulários de criação e edição de perfis."""

from django import forms
from django.conf import settings

from apps.profiles.models import Profile


class ProfileForm(forms.ModelForm):
    """Formulário usado tanto na criação quanto na edição de um perfil."""

    class Meta:
        model = Profile
        fields = ["name", "avatar", "is_kids"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome do perfil", "maxlength": 50}),
            "avatar": forms.Select(attrs={"class": "form-select", "data-avatar-select": "true"}),
            "is_kids": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        """Reforça no formulário (com mensagem amigável) o limite de perfis.

        A regra "oficial" está em `Profile.clean()`; aqui apenas evitamos que
        o usuário veja um erro genérico de integridade do banco.
        """
        cleaned_data = super().clean()
        is_new = self.instance.pk is None
        if is_new and self.user is not None:
            total = Profile.objects.filter(user=self.user).count()
            if total >= settings.MAX_PROFILES_PER_USER:
                raise forms.ValidationError(
                    f"Você já atingiu o limite de {settings.MAX_PROFILES_PER_USER} perfis por conta."
                )
        return cleaned_data
