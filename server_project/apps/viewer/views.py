from io import BytesIO

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator

from .models import Slide


def openseadragon_view(request, slug):
    """
    Render a page with the OpenSeadragon viewer for the specified slide.
    """
    slide_obj = get_object_or_404(Slide, name=slug)
    context = {
        "slide_name": slide_obj.name.replace("-", " ").capitalize(),
        "dzi_url": f"/slides/{slug}.dzi",
    }
    return render(request, "viewer/viewer.html", context)


def dzi_descriptor(request, slug):
    """
    Serve the Deep Zoom descriptor (DZI) XML file for a slide.
    """
    slide_obj = get_object_or_404(Slide, name=slug)
    with open_slide(slide_obj.file.path) as slide:
        deepzoom = DeepZoomGenerator(slide)
        dzi_content = deepzoom.get_dzi("jpeg")
    return HttpResponse(dzi_content, content_type="application/xml")


def tile(request, slug, level, col, row, format):
    """
    Serve individual Deep Zoom tiles for a slide.
    """
    slide_obj = get_object_or_404(Slide, name=slug)
    with open_slide(slide_obj.file.path) as slide:
        deepzoom = DeepZoomGenerator(slide)

        if format not in ["jpeg", "png"]:
            raise Http404("Unsupported format")
        try:
            tile_img = deepzoom.get_tile(level, (col, row))
            buffer = BytesIO()
            tile_img.save(buffer, format=format, quality=75)
            return HttpResponse(buffer.getvalue(), content_type=f"image/{format}")
        except ValueError:
            raise Http404("Invalid level or tile coordinates")
