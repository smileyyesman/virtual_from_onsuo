from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver


class Slide(models.Model):
    file = models.FileField(upload_to="slides/", help_text="Choose a slide file to upload.")
    title = models.CharField(max_length=250, unique=True, help_text="Title of the slide.")
    slug = models.SlugField(max_length=250, unique=True, help_text="Unique slug for the slide.")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Slide"
        verbose_name_plural = "Slides"
        ordering = ("title",)


@receiver(post_delete, sender=Slide)
def delete_slide_file(sender, instance, **kwargs):
    instance.file.delete(False)


@receiver(pre_save, sender=Slide)
def delete_old_slide_file(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Slide.objects.get(pk=instance.pk)
        if old_instance.file != instance.file:
            old_instance.file.delete(False)
