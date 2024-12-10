from django.db import models


class Annotataion(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, null=True)
    description = models.TextField(
        max_length=1000,
        help_text="Description of the annotation",
    )
    data = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slide = models.ForeignKey(
        "slides.Slide",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
