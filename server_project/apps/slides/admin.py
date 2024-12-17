from django.contrib import admin

from .models import Slide, Tag


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "file", "created_at", "updated_at", "department")
    list_filter = ("department",)
    search_fields = ("name", "slug", "description")
    ordering = ("-created_at",)

    prepopulated_fields = {"name": ("file",), "slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("-created_at",)
