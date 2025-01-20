from django.urls import path

from . import views

app_name = "slide_viewer"

urlpatterns = [
    path("<int:slide_id>", views.SlideView.as_view(), name="slide_view"),
    path("<int:slide_id>.dzi", views.get_dzi, name="get_dzi"),
    path(
        "<int:slide_id>_files/<int:level>/<int:col>_<int:row>.<format>",
        views.get_tiles,
        name="get_tiles",
    ),
    path("<int:slide_id>/thumbnail", views.get_thumbnail, name="get_thumbnail"),
]
