from django.urls import path

from . import views

app_name = "slides"

urlpatterns = [
    path("", views.AllSlidesView.as_view(), name="all_slides"),
]
