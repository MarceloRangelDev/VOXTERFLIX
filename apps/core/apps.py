from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"

    def ready(self):
        # Personaliza o cabeçalho do Django Admin com a marca do VoxterFlix,
        # em vez de deixar o "Django administration" padrão.
        from django.contrib import admin

        admin.site.site_header = "VoxterFlix — Administração"
        admin.site.site_title = "VoxterFlix Admin"
        admin.site.index_title = "Painel administrativo"
