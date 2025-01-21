import os
import shutil

from django.conf import settings
from django.db import models
from openslide import OpenSlide
from openslide.deepzoom import DeepZoomGenerator


class FolderManager(models.Manager):
    def base_folders(self):
        return self.filter(parent__isnull=True)


class Folder(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subfolders",
        blank=True,
        null=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        db_column="created_by",
        related_name="folders",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FolderManager()

    class Meta:
        unique_together = ("name", "parent")
        ordering = ("name",)

    def __str__(self):
        return self.get_full_path()

    def get_full_path(self):
        if self.parent:
            return f"{self.parent.get_full_path()}/{self.name}"
        return self.name

    def is_base_folder(self):
        """Check if this folder is a base folder"""
        return self.parent is None

    def get_base_folder(self):
        """Get the root folder of this folder's hierarchy"""
        current_folder = self
        while current_folder.parent:
            current_folder = current_folder.parent
        return current_folder

    def get_department(self):
        """Get the department this folder belongs to"""
        return self.get_base_folder().department

    def user_has_access(self, user):
        """Check if the user has access to this folder"""
        if user.is_admin():
            return True
        elif user.is_publisher() and user.department:
            return self.get_department() == user.department
        return False

    def is_empty(self):
        """Check if the folder and the subfolders don't have slides"""
        if self.slides.exists():
            return False
        for subfolder in self.subfolders.all():
            if not subfolder.is_empty():
                return False
        return True

    def is_children(self, folder):
        """Check if the folder is a subfolder of this folder"""
        current_folder = folder.parent
        while current_folder:
            if current_folder == self:
                return True
            current_folder = current_folder.parent
        return False


class SlideManager(models.Manager):
    def get_root_slides(self):
        """Get slides that aren't in any folder"""
        return self.filter(folder__isnull=True)


class Slide(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.FileField(
        upload_to="slides/",
        help_text="Choose a slide file to upload.",
    )
    name = models.CharField(
        max_length=250,
        help_text="Name of the slide.",
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the slide.",
    )
    image_root = models.CharField(
        max_length=250,
        blank=True,
        help_text="Relative path to the image directory.",
    )
    metadata = models.JSONField(blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        db_column="created_by",
        related_name="slides",
        blank=True,
        null=True,
    )
    folder = models.ForeignKey(
        Folder,
        on_delete=models.SET_NULL,
        related_name="slides",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SlideManager()

    class Meta:
        verbose_name = "Slide"
        verbose_name_plural = "Slides"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            need_slide_processing = True
            if self.pk:
                old_instance = Slide.objects.get(pk=self.pk)
                if old_instance.file != self.file:
                    # delete old slide file
                    old_instance.file.delete()
                    # delete old image directory
                    self._delete_directory(old_instance.get_image_directory())
                else:
                    need_slide_processing = False

            if not self.name:
                self.name = os.path.splitext(os.path.basename(self.file.name))[0]

            super().save(*args, **kwargs)

            if not self.image_root:
                image_root = os.path.join("images", str(self.id))
                Slide.objects.filter(pk=self.pk).update(image_root=image_root)
                self.image_root = image_root

            if need_slide_processing:
                self.process_slide()

        except Exception as e:
            raise Exception(f"Failed to save slide: {str(e)}")

    def delete(self, *args, **kwargs):
        try:
            self.file.delete(False)
            self._delete_directory(self.get_image_directory())
            super().delete(*args, **kwargs)
        except Exception as e:
            raise Exception(f"Failed to delete slide: {str(e)}")

    def process_slide(self):
        try:
            with OpenSlide(self.file.path) as slide:
                self._generate_images(slide)
                self._save_metadata(slide)
        except Exception as e:
            raise Exception(f"Failed to process slide: {str(e)}")

    def check_integrity(self):
        """Check integrity of the slide's files and metadata"""

        status = {
            "needs_repair": False,
            "file_exists": False,
            "dzi_exists": False,
            "tiles_complete": False,
            "thumbnail_exists": False,
            "associated_image_exists": False,
            "metadata_valid": False,
        }

        status["file_exists"] = os.path.exists(self.file.path)
        status["dzi_exists"] = os.path.exists(self.get_dzi_path())

        # Check tiles
        try:
            with OpenSlide(self.file.path) as slide:
                deepzoom = DeepZoomGenerator(slide)
                status["tiles_complete"] = self._verify_tiles(deepzoom)
        except:
            status["tiles_complete"] = False

        status["thumbnail_exists"] = os.path.exists(self.get_thumbnail_path())
        status["associated_image_exists"] = os.path.exists(self.get_associated_image_path())
        status["metadata_valid"] = self._verify_metadata()

        status["needs_repair"] = not all(
            [
                status["file_exists"],
                status["dzi_exists"],
                status["tiles_complete"],
                status["thumbnail_exists"],
                status["associated_image_exists"],
                status["metadata_valid"],
            ]
        )

        return status

    def repair(self, status):
        """Repair any missing or corrupted components"""

        status = self.check_integrity()

        if not status["needs_repair"]:
            return status

        if not status["file_exists"]:
            raise Exception("Original slide file does not exist")

        try:
            with OpenSlide(self.file.path) as slide:
                image_directory = self.get_image_directory()

                if not (
                    status["dzi_exists"]
                    and status["tiles_complete"]
                    and status["thumbnail_exists"]
                    and status["associated_image_exists"]
                ):
                    self._delete_directory(image_directory)
                    self._generate_images(slide, image_directory)

                if not status["metadata_valid"]:
                    self._save_metadata(slide)

            return self.check_integrity()

        except Exception as e:
            raise Exception(f"Failed to repair slide {self.name} (id={self.id}): {str(e)}")

    def user_has_access(self, user):
        """Check if the user has access to the slide"""
        return self.folder.user_has_access(user) if self.folder else user.is_admin()

    def get_image_directory(self):
        """Get the path to the image directory"""
        return os.path.join(settings.MEDIA_ROOT, self.image_root)

    def get_dzi_path(self):
        """Get the path to the DZI file"""
        return os.path.join(settings.MEDIA_ROOT, self.image_root, "image.dzi")

    def get_tile_directory(self):
        """Get the path to the tiles directory"""
        return os.path.join(settings.MEDIA_ROOT, self.image_root, "image_files")

    def get_thumbnail_path(self):
        """Get the URL of the thumbnail image"""
        return os.path.join(settings.MEDIA_ROOT, self.image_root, "thumbnail.png")

    def get_associated_image_path(self):
        """Get the path to the associated image"""
        return os.path.join(settings.MEDIA_ROOT, self.image_root, "associated_image.png")

    def _generate_images(self, slide: OpenSlide):
        """Generate related images for the slide"""

        FORMAT = "jpeg"

        try:
            # Setup directory
            tile_directory = self.get_tile_directory()
            os.makedirs(tile_directory, exist_ok=True)

            deepzoom = DeepZoomGenerator(slide)

            # Create DZI file
            dzi = deepzoom.get_dzi(FORMAT)
            with open(self.get_dzi_path(), "w") as f:
                f.write(dzi)

            # Generate tiles
            for level in range(deepzoom.level_count):
                level_dir = os.path.join(tile_directory, str(level))
                os.makedirs(level_dir, exist_ok=True)

                cols, rows = deepzoom.level_tiles[level]
                for col in range(cols):
                    for row in range(rows):
                        tile_path = os.path.join(level_dir, f"{col}_{row}.{FORMAT}")
                        tile = deepzoom.get_tile(level, (col, row))
                        tile.save(tile_path)

            # Save thumbnail and associated image
            slide.get_thumbnail((256, 256)).save(self.get_thumbnail_path())
            slide.associated_images.get("macro").save(self.get_associated_image_path())

        except Exception as e:
            raise Exception(f"Failed to generate images: {str(e)}")

    def _save_metadata(self, slide):
        """Extract and save metadata from the slide"""

        try:
            full_metadata = slide.properties

            metadata = {
                "mpp-x": float(full_metadata.get("openslide.mpp-x")),
                "mpp-y": float(full_metadata.get("openslide.mpp-y")),
                "sourceLens": int(full_metadata.get("hamamatsu.SourceLens")),
                "created": full_metadata.get("hamamatsu.Created"),
            }
            Slide.objects.filter(pk=self.pk).update(metadata=metadata)
            self.metadata = metadata  # Update instance attribute
        except Exception as e:
            raise Exception(f"Failed to save metadata: {str(e)}")

    def _verify_tiles(self, deepzoom):
        """Verify all expected tiles exist"""

        for level in range(deepzoom.level_count):
            level_dir = os.path.join(self.get_tile_directory(), str(level))
            if not os.path.exists(level_dir):
                return False

            cols, rows = deepzoom.level_tiles[level]
            expected_tiles = set(f"{col}_{row}.jpeg" for col in range(cols) for row in range(rows))
            existing_tiles = set(os.listdir(level_dir))
            if not expected_tiles.issubset(existing_tiles):
                return False

        return True

    def _verify_metadata(self):
        """Verify metadata is complete"""

        if not self.metadata:
            return False

        required_fields = {"mpp-x", "mpp-y", "sourceLens", "created"}
        return required_fields.issubset(self.metadata.keys())

    @staticmethod
    def _delete_directory(image_directory):
        try:
            if os.path.exists(image_directory):
                shutil.rmtree(image_directory)
        except Exception as e:
            raise Exception(f"Failed to delete image directory: {str(e)}")


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    slides = models.ManyToManyField(
        "Slide",
        related_name="tags",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ("name",)

    def __str__(self):
        return self.name
