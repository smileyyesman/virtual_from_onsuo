from django.urls import path

from . import views

urlpatterns = [
    path("<slug>.dzi", views.dzi_descriptor, name="dzi_descriptor"),
    path("<slug>_files/<int:level>/<int:col>_<int:row>.<format>", views.tile, name="tile"),
    path("<slug>", views.openseadragon_view, name="openseadragon_view"),  # should be at the end.
]
