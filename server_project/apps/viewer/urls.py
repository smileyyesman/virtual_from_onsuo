from django.urls import path

from . import views

urlpatterns = [
    path("", views.viewer, name="viewer"),
    path("<slug>.dzi", views.dzi, name="dzi"),
    path("<slug>_files/<int:level>/<int:col>_<int:row>.<format>", views.tile, name="tile"),
]
