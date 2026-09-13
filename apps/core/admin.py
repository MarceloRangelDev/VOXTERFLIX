from django.contrib import admin

from apps.core.models import SecurityEvent


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Painel administrativo somente leitura para auditoria de segurança."""

    list_display = ("event_type", "user", "ip_address", "path", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("ip_address", "path", "user__username")
    ordering = ("-created_at",)
    readonly_fields = ("event_type", "user", "ip_address", "path", "metadata", "created_at", "updated_at")

    def has_add_permission(self, request):
        # Eventos de segurança só devem ser criados pelo próprio sistema.
        return False

    def has_change_permission(self, request, obj=None):
        return False
