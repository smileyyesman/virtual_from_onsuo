from django.contrib import admin

from .models import (
    Folder,
    Slide,
    Tag,
)


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("-created_at",)


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("name", "file", "folder", "created_at", "updated_at")
    search_fields = ("name", "description")
    ordering = ("-created_at",)

    prepopulated_fields = {"name": ("file",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("-created_at",)
