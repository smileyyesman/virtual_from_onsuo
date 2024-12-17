from django.contrib import admin

from .models import Course, Enrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "creater", "created_at", "updated_at", "is_active")
    list_filter = ("creater", "is_active")
    search_fields = ("name", "creater__username")
    ordering = ("-updated_at",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("course", "user", "enrolled_at")
    list_filter = ("course", "user")
    search_fields = ("course__name", "user__username")
    ordering = ("-enrolled_at",)
