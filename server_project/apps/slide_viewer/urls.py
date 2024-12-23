from django.urls import path

from . import views

app_name = "slide_viewer"

urlpatterns = [
    path(
        "<slug>.dzi",
        views.DZIView.as_view(),
        name="dzi_view",
    ),
    path(
        "<slug>_files/<int:level>/<int:col>_<int:row>.<format>",
        views.TileView.as_view(),
        name="tile_view",
    ),
    path(
        "<slug>",
        views.SlideView.as_view(),
        name="slide_view",
    ),
]
