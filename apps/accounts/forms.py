"""Formulários de autenticação: cadastro, login e recuperação de senha."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User
from django.urls import reverse

from apps.notifications.services import ResendEmailService


class SignUpForm(UserCreationForm):
    """Cadastro de conta, reaproveitando a validação de senha do Django.

    Adicionamos e-mail obrigatório e único — o Django, por padrão, nem
    exige e nem valida unicidade de e-mail no `UserCreationForm`.
    """

    email = forms.EmailField(
        label="E-mail",
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "seu@email.com"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nome de usuário"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Senha"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Confirme a senha"})

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Já existe uma conta cadastrada com este e-mail.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        # A conta só é ativada após a confirmação do e-mail (ver accounts.views.confirm_email).
        user.is_active = False
        if commit:
            user.save()
        return user


class StyledAuthenticationForm(AuthenticationForm):
    """Só adiciona classes do Bootstrap; a validação continua sendo a do Django."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Usuário"})
        self.fields["password"].widget.attrs.update({"class": "form-control", "placeholder": "Senha"})

    def get_invalid_login_error(self):
        # Mesma mensagem genérica tanto para usuário inexistente, senha errada
        # ou conta com e-mail ainda não confirmado (is_active=False) — o
        # ModelBackend já recusa autenticar contas inativas, então os três
        # casos chegam aqui da mesma forma. Nunca revela qual deles ocorreu.
        return forms.ValidationError("Usuário ou senha inválidos.", code="invalid_login")


class ResendPasswordResetForm(PasswordResetForm):
    """Reaproveita toda a lógica oficial do Django (token, expiração, uid);
    troca apenas o *transporte* do e-mail, que passa a ser o Resend em vez
    do backend de e-mail padrão do Django.
    """

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        reset_path = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": context["uid"], "token": context["token"]},
        )
        reset_url = f"{context['protocol']}://{context['domain']}{reset_path}"
        ResendEmailService().send_password_reset_email(context["user"], reset_url)
