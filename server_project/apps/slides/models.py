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
from django.shortcuts import get_object_or_404
from openslide import OpenSlide
from openslide.deepzoom import DeepZoomGenerator


class Slide(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.FileField(
        upload_to="slides/",
        help_text="Choose a slide file to upload.",
    )
    name = models.CharField(
        max_length=250,
        unique=True,
        help_text="Name of the slide.",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Unique slug for the slide.",
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the slide.",
    )
    image_path = models.CharField(
        max_length=250,
        blank=True,
        help_text="Path to the image files.",
    )
    created_at = models.DateField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        db_column="uploaded_by",
        related_name="slides",
        blank=True,
        null=True,
    )
    department = models.ForeignKey(
        "Department",
        on_delete=models.SET_NULL,
        related_name="slides",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Slide"
        verbose_name_plural = "Slides"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        self.image_path = os.path.join("images", self.slug)
        super().save(**kwargs)


class Department(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    slide = models.ManyToManyField(
        "Slide",
        related_name="tags",
        blank=True,
    )

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ("name",)

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Slide)
def delete_old_files(sender, instance, **kwargs):
    if not instance.pk:
        return

    old_instance = get_object_or_404(Slide, pk=instance.pk)
    old_slideimage_dir = os.path.join(settings.MEDIA_ROOT, "images", old_instance.slug)

    if old_instance.file != instance.file:
        # delete slide file
        old_instance.file.delete(False)
        # delete a directory of image files for the slide
        shutil.rmtree(old_slideimage_dir)
    elif old_instance.slug != instance.slug:
        if os.path.exists(old_slideimage_dir):
            # rename existing directory
            slideimage_dir = os.path.join(settings.MEDIA_ROOT, "images", instance.slug)
            os.rename(old_slideimage_dir, slideimage_dir)


@receiver(post_save, sender=Slide)
def generate_image_files(sender, instance, **kwargs):
    slideimage_dir = os.path.join(settings.MEDIA_ROOT, "images", instance.slug)
    if os.path.exists(slideimage_dir):
        return

    dzi_path = os.path.join(slideimage_dir, "image.dzi")
    tile_dir = os.path.join(slideimage_dir, "image_files/")
    os.makedirs(tile_dir)

    FORMAT = "jpeg"
    """
    png:
        lossless, original qualtiy
        8~9 times bigger size than ndpi --> total: x10 of ndpi file size
    jpeg:
        lossy, lower quality
        same or smaller size than ndpi --> total: x2 of ndpi file size
    """
    slide = OpenSlide(instance.file.path)
    deepzoom = DeepZoomGenerator(slide)
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
def delete_files(sender, instance, **kwargs):
    # delete slide file
    instance.file.delete(False)
    # delete a directory of dzi and image files for the slide
    slideimage_dir = os.path.join(settings.MEDIA_ROOT, "images", instance.slug)
    if os.path.exists(slideimage_dir):
        shutil.rmtree(slideimage_dir)


def get_metadata(slide_path):
    slide = OpenSlide(slide_path)
    metadata = slide.properties.items()
    return metadata
