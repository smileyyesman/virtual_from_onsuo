import os
from io import BytesIO

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View
from slides.models import Slide


class SlideView(TemplateView):
    """
    Render a page with the OpenSeadragon viewer for the specified slide.
    """

    template_name = "slide_viewer/viewer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = kwargs.get("slug")
        slide_obj = get_object_or_404(Slide, slug=slug)
        context.update(
            {
                "slide_name": slide_obj.name,
                "dzi_url": f"/viewer/{slug}.dzi",
            }
        )
        return context


class DZIView(View):
    """
    Serve the Deep Zoom Image (DZI) XML file for a slide.
    """

    def get(self, request, slug):
        dzi_path = os.path.join(settings.MEDIA_ROOT, "images", slug, "image.dzi")
        with open(dzi_path, "r") as f:
            dzi_content = f.read()
        return HttpResponse(dzi_content, content_type="application/xml")


class TileView(View):
    """
    Serve individual Deep Zoom tiles for a slide.
    """

    def get(self, request, slug, level, col, row, format):
        tile_dir = os.path.join(settings.MEDIA_ROOT, "images", slug, "image_files")
        if format not in ["jpeg", "png"]:
            raise Http404("Unsupported format")

        try:
            with open(os.path.join(tile_dir, str(level), f"{col}_{row}.{format}"), "rb") as f:
                tile = BytesIO(f.read())
            return HttpResponse(tile, content_type=f"image/{format}")
        except ValueError:
            raise Http404("Invalid level or tile coordinates")
