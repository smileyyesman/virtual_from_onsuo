from django.contrib import admin

from .models import (
    Folder,
    Slide,
    Tag,
)


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "created_at")
    search_fields = ("name",)
    ordering = ("-created_at",)


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "file", "created_at", "updated_at")
    search_fields = ("name", "slug", "description")
    ordering = ("-created_at",)

    prepopulated_fields = {"name": ("file",), "slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("-created_at",)
