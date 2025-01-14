from django.conf import settings
from django.db import models


class Annotation(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True)
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the annotation",
    )
    data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="annotations",
        blank=True,
        null=True,
    )
    slide = models.ForeignKey(
        "slides.Slide",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Annotation"
        verbose_name_plural = "Annotations"
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.name} - {self.slide}"
