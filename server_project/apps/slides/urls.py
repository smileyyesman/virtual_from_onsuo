from django.urls import path

from . import views

app_name = "slides"

urlpatterns = [
    path(
        "",
        views.DepartmentSlideListView.as_view(),
        name="department_list",
    ),
    path(
        "<slug>",
        views.SlideListView.as_view(),
        name="slide_list",
    ),
]
