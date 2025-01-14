from django.conf import settings
from django.db import models


class Lecture(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slides = models.ManyToManyField(
        "slides.Slide",
        related_name="lectures",
        blank=True,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        db_column="created_by",
        related_name="lectures",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Lecture"
        verbose_name_plural = "Lectures"
        ordering = ("created_at",)

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    id = models.AutoField(primary_key=True)
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name="enrollments",
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        blank=True,
        null=True,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        ordering = ("enrolled_at",)

    def __str__(self):
        return f"{self.lecture} - {self.user}"
