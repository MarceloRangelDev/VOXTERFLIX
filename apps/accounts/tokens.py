"""Gerador de token de confirmação de e-mail.

Reaproveita o mesmo mecanismo seguro que o Django usa para recuperação de
senha (`PasswordResetTokenGenerator`): um hash assinado com `SECRET_KEY`,
sem precisar guardar o token em uma tabela. A única diferença é o valor
usado no hash — aqui incluímos `is_active`, então o token para de funcionar
automaticamente assim que a conta é confirmada (evita reuso do link).
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.is_active}{user.email}{timestamp}"


email_confirmation_token = EmailConfirmationTokenGenerator()
