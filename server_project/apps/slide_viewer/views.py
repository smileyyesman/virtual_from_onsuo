import os
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from slides.models import Slide


class SlideView(TemplateView):
    """Render a page with the OpenSeadragon viewer for the specified slide."""

    template_name = "slide_viewer/viewer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slide_id = kwargs.get("slide_id")
        slide = get_object_or_404(Slide, id=slide_id)

        context["slide"] = slide
        context["dzi_url"] = reverse_lazy("slide_viewer:get_dzi", kwargs={"slide_id": slide_id})
        return context


def get_dzi(request, slide_id):
    """Serve the Deep Zoom Image (DZI) XML file for a slide."""

    dzi_path = get_object_or_404(Slide, id=slide_id).get_dzi_path()

    try:
        with open(dzi_path, "r") as f:
            dzi_content = f.read()
    except Exception as e:
        messages.error(request, f"Failed to load DZI file: {str(e)}")

    return HttpResponse(dzi_content, content_type="application/xml")


def get_tiles(request, slide_id, level, col, row, format):
    """Serve individual Deep Zoom tiles for a slide."""

    if format not in ["jpeg", "png"]:
        messages.error(request, "Unsupported format")

    tile_directory = get_object_or_404(Slide, id=slide_id).get_tile_directory()

    try:
        with open(os.path.join(tile_directory, str(level), f"{col}_{row}.{format}"), "rb") as f:
            tile = BytesIO(f.read())
        return HttpResponse(tile, content_type=f"image/{format}")
    except Exception as e:
        messages.error(request, f"Failed to load tile images: {str(e)}")


def get_thumbnail(request, slide_id):
    """Serve the thumbnail image for a slide."""

    thumbnail_path = get_object_or_404(Slide, id=slide_id).get_thumbnail_path()

    try:
        with open(thumbnail_path, "rb") as f:
            thumbnail = BytesIO(f.read())
        return HttpResponse(thumbnail, content_type="image/png")
    except Exception as e:
        messages.error(request, f"Failed to load thumbnail: {str(e)}")
