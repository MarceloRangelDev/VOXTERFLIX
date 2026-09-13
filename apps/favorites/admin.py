from django.contrib import admin

from apps.favorites.models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("title", "profile", "type", "year", "created_at")
    list_filter = ("type", "created_at")
    search_fields = ("title", "imdb_id", "profile__name")
    ordering = ("-created_at",)
