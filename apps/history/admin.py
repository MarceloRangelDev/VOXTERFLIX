from django.contrib import admin

from apps.history.models import WatchHistory


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ("title", "profile", "season", "episode", "percent", "updated_at")
    list_filter = ("type", "updated_at")
    search_fields = ("title", "imdb_id", "profile__name")
    ordering = ("-updated_at",)
