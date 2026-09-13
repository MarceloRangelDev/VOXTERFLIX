from django.contrib import admin

from apps.catalog.models import Category, CuratedTitle


class CuratedTitleInline(admin.TabularInline):
    model = CuratedTitle
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_kids_allowed")
    list_filter = ("is_kids_allowed",)
    search_fields = ("name", "slug")
    ordering = ("order",)
    inlines = [CuratedTitleInline]


@admin.register(CuratedTitle)
class CuratedTitleAdmin(admin.ModelAdmin):
    list_display = ("imdb_id", "category", "order", "is_featured")
    list_filter = ("category", "is_featured")
    search_fields = ("imdb_id",)
    ordering = ("category", "order")
