from django.contrib import admin

from .models import Enrollment, Lecture


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "created_at", "updated_at", "is_active")
    list_filter = ("author", "is_active")
    search_fields = ("name", "creater__username")
    ordering = ("-updated_at",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("lecture", "user", "enrolled_at")
    list_filter = ("lecture", "user")
    search_fields = ("lecture__name", "user__username")
    ordering = ("-enrolled_at",)
