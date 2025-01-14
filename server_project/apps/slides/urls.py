from django.urls import path

from . import views

app_name = "slides"

urlpatterns = [
    path(
        "",
        views.FolderNavigationView.as_view(),
        name="folder_navigation",
    ),
    path(
        "folders/create/",
        views.create_folder,
        name="create_folder",
    ),
    path(
        "folders/rename/",
        views.rename_folder,
        name="rename_folder",
    ),
    path(
        "folders/delete/",
        views.delete_folder,
        name="delete_folder",
    ),
    path(
        "folders/details/",
        views.folder_details,
        name="folder_details",
    ),
]
