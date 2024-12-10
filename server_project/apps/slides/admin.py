from django.contrib import admin

from .models import Department, Slide


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "file", "uploaded_at", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"name": ("file",), "slug": ("name",)}


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
