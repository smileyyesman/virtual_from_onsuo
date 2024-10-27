from io import BytesIO

from django.http import Http404, HttpResponse
from django.shortcuts import render
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator

# Path to your slide file
SLIDE_FILE_PATH = "/home/onsuo/dev/virtual_microscope/slides/H7050x20 blood vessels human.ndpi"
SLIDE_NAME = "H7050x20 blood vessels human"

# Create the DeepZoomGenerator instance when the server starts
slide = open_slide(SLIDE_FILE_PATH)
deepzoom = DeepZoomGenerator(slide)


def viewer(request):
    """
    View to render the main Deep Zoom viewer.
    """
    context = {
        "slide_name": SLIDE_NAME,
        "slide_url": f"/zoomviewer/{SLIDE_NAME}.dzi",
    }
    return render(request, "zoomviewer/viewer.html", context)


def dzi(request, slug):
    """
    View to serve the Deep Zoom descriptor (DZI) XML file.
    """
    if slug != SLIDE_NAME:
        raise Http404("Slide not found")

    # Get DZI XML format from the DeepZoomGenerator
    dzi_content = deepzoom.get_dzi("jpeg")
    return HttpResponse(dzi_content, content_type="application/xml")


def tile(request, slug, level, col, row, format):
    """
    View to serve individual Deep Zoom tiles.
    """
    if slug != SLIDE_NAME:
        raise Http404("Slide not found")
    if format not in ["jpeg", "png"]:
        raise Http404("Unsupported format")

    try:
        # Get the requested tile from the DeepZoomGenerator
        tile_img = deepzoom.get_tile(level, (col, row))
        buffer = BytesIO()
        tile_img.save(buffer, format=format, quality=75)
        return HttpResponse(buffer.getvalue(), content_type=f"image/{format}")
    except ValueError:
        # Invalid level or tile coordinates
        raise Http404("Tile not found")
