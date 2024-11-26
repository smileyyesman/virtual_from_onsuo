import os
from io import BytesIO

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Slide


def openseadragon_view(request, slug):
    """
    Render a page with the OpenSeadragon viewer for the specified slide.
    """
    slide_obj = get_object_or_404(Slide, slug=slug)
    context = {
        "slide_name": slide_obj.title,
        "dzi_url": f"/slides/{slug}.dzi",
    }
    return render(request, "viewer/viewer.html", context)


def dzi_descriptor(request, slug):
    """
    Serve the Deep Zoom Image (DZI) XML file for a slide.
    """
    dzi_path = os.path.join(settings.MEDIA_ROOT, "images", slug, slug + ".dzi")
    with open(dzi_path, "r") as f:
        dzi_content = f.read()
    return HttpResponse(dzi_content, content_type="application/xml")


def tile(request, slug, level, col, row, format):
    """
    Serve individual Deep Zoom tiles for a slide.
    """
    tile_dir = os.path.join(settings.MEDIA_ROOT, "images", slug, slug + "_files")
    if format not in ["jpeg", "png"]:
        raise Http404("Unsupported format")

    try:
        with open(os.path.join(tile_dir, str(level), f"{col}_{row}.{format}"), "rb") as f:
            tile = BytesIO(f.read())
        return HttpResponse(tile, content_type=f"image/{format}")
    except ValueError:
        raise Http404("Invalid level or tile coordinates")
