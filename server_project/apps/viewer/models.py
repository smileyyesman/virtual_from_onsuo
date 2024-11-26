import os
import shutil

from django.conf import settings
from django.db import models
from django.db.models.signals import (
    post_delete,
    post_save,
    pre_save,
)
from django.dispatch import receiver
from openslide import OpenSlide
from openslide.deepzoom import DeepZoomGenerator


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


@receiver(pre_save, sender=Slide)
def delete_old_files(sender, instance, **kwargs):
    if not instance.pk:
        return

    old_instance = Slide.objects.get(pk=instance.pk)
    old_slideimage_dir = os.path.join(settings.MEDIA_ROOT, "images", old_instance.slug)

    if old_instance.file != instance.file:
        # delete slide file
        old_instance.file.delete(False)
        # delete a directory of dzi and image files for the slide
        shutil.rmtree(old_slideimage_dir)

    if old_instance.slug != instance.slug:
        if os.path.exists(old_slideimage_dir):
            # rename existing directory
            slideimage_dir = os.path.join(settings.MEDIA_ROOT, "images", instance.slug)
            os.rename(old_slideimage_dir, slideimage_dir)
            os.rename(
                os.path.join(slideimage_dir, old_instance.slug + ".dzi"),
                os.path.join(slideimage_dir, instance.slug + ".dzi"),
            )


@receiver(post_save, sender=Slide)
def create_image_files(sender, instance, **kwargs):
    slideimage_dir = os.path.join(settings.MEDIA_ROOT, "images", instance.slug)
    if os.path.exists(slideimage_dir):
        return

    dzi_path = os.path.join(slideimage_dir, instance.slug + ".dzi")
    tile_dir = os.path.join(slideimage_dir, instance.slug + "_files/")
    os.makedirs(tile_dir)

    slide = OpenSlide(instance.file.path)
    deepzoom = DeepZoomGenerator(slide)

    FORMAT = "jpeg"
    """
    png:
        lossless, original qualtiy
        8~9 times bigger size than ndpi --> total: x10 of ndpi file size
    jpeg:
        lossy, lower quality
        same or smaller size than ndpi --> total: x2 of ndpi file size
    """
    dzi = deepzoom.get_dzi(FORMAT)

    # create dzi file
    with open(dzi_path, "w") as f:
        f.write(dzi)

    # create tile images
    for level in range(deepzoom.level_count):
        level_dir = os.path.join(tile_dir, str(level))
        if not os.path.exists(level_dir):
            os.makedirs(level_dir)

        for col in range(deepzoom.level_tiles[level][0]):
            for row in range(deepzoom.level_tiles[level][1]):
                tile_path = os.path.join(level_dir, f"{col}_{row}.{FORMAT}")
                tile = deepzoom.get_tile(level, (col, row))
                tile.save(tile_path)

    slide.close()


@receiver(post_delete, sender=Slide)
def delete_slide_file(sender, instance, **kwargs):
    # delete slide file
    instance.file.delete(False)
    # delete a directory of dzi and image files for the slide
    slideimage_dir = os.path.join(settings.MEDIA_ROOT, "images", instance.slug)
    if os.path.exists(slideimage_dir):
        shutil.rmtree(slideimage_dir)
