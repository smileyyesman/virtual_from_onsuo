from django.contrib import admin

from .models import Slide


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("name", "file", "created", "updated")
    search_fields = ("name",)
    prepopulated_fields = {"name": ("file",)}
