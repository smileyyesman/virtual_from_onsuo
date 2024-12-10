from django.views.generic import ListView

from .models import Department, Slide


class AllSlidesView(ListView):
    model = Department
    template_name = "slides/all_slides.html"
    context_object_name = "departments"

    def get_queryset(self):
        return Department.objects.prefetch_related("slides").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["slides_without_department"] = Slide.objects.filter(department__isnull=True)
        return context
