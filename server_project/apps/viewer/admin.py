from django.contrib import admin

from .models import Slide


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "file", "created", "updated")
    search_fields = ("title", "slug")
    prepopulated_fields = {"title": ("file",), "slug": ("title",)}
