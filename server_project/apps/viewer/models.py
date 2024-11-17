from django.db import models


class Slide(models.Model):
    name = models.SlugField(max_length=250, unique=True, help_text="Unique slug for the slide.")
    file = models.FileField(upload_to="slides/", help_text="Choose a slide file to upload.")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
