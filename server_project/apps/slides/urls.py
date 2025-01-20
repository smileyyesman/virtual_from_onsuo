from django.urls import path

from . import views

app_name = "slides"

urlpatterns = [
    path("", views.SlideNavigationView.as_view(), name="slide_navigation"),
    path("upload/", views.upload_slide, name="upload_slide"),
    path("edit/", views.edit_slide, name="edit_slide"),
    path("move/", views.move_slide, name="move_slide"),
    path("delete/", views.delete_slide, name="delete_slide"),
    path("details/", views.slide_details, name="slide_details"),
    path("folders/create/", views.create_folder, name="create_folder"),
    path("folders/rename/", views.rename_folder, name="rename_folder"),
    path("folders/move/", views.move_folder, name="move_folder"),
    path("folders/delete/", views.delete_folder, name="delete_folder"),
    path("folders/details/", views.folder_details, name="folder_details"),
    path("tree/", views.get_folder_tree, name="get_folder_tree"),
]
