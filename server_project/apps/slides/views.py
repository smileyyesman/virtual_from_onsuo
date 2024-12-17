from accounts.models import Department
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView

from .models import Slide


class AllSlidesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    model = Department
    template_name = "slides/all_slides.html"
    context_object_name = "departments"

    def get_queryset(self):
        return Department.objects.prefetch_related("slides").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["slides_without_department"] = Slide.objects.filter(department__isnull=True)
        return context

    def test_func(self):
        allowed_groups = ["admin"]
        return self.request.user.groups.filter(name__in=allowed_groups).exists()
