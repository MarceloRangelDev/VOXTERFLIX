from django.contrib import admin

from apps.profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "avatar", "is_kids", "created_at")
    list_filter = ("is_kids", "avatar")
    search_fields = ("name", "user__username", "user__email")
    ordering = ("user", "created_at")
