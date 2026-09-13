from django.contrib import admin

from apps.notifications.models import EmailLog


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("to_email", "email_type", "status", "created_at")
    list_filter = ("email_type", "status", "created_at")
    search_fields = ("to_email", "provider_message_id")
    ordering = ("-created_at",)
    readonly_fields = [f.name for f in EmailLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
