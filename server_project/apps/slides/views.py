from accounts.models import Department
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from .models import Slide


class DepartmentSlideListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = [
        "slides.add_slide",
        "slides.change_slide",
        "slides.delete_slide",
    ]
    template_name = "slides/department_list.html"
    context_object_name = "departments"

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name="admin").exists():
            return Department.objects.all()
        elif user.groups.filter(name="publisher").exists():
            return Department.objects.filter(id=user.department.id)
        return Department.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_no_department_slides"] = Slide.objects.filter(department__isnull=True).exists()
        return context


class SlideListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = [
        "slides.add_slide",
        "slides.change_slide",
        "slides.delete_slide",
    ]
    template_name = "slides/slide_list.html"
    context_object_name = "slides"

    def get_queryset(self):
        user = self.request.user
        department_slug = self.kwargs.get("slug")

        if department_slug == "no-department":
            if user.groups.filter(name="admin").exists():
                return Slide.objects.filter(department__isnull=True)
            return Slide.objects.none()

        if department_slug:
            department = get_object_or_404(Department, slug=department_slug)

            if user.groups.filter(name="admin").exists():
                return department.slides.all()

            elif user.groups.filter(name="publisher").exists():
                if department == user.department:
                    return department.slides.all()
                raise Http404("Department not found")

        return Slide.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department_slug = self.kwargs.get("slug")
        if department_slug != "no-department":
            department = get_object_or_404(Department, slug=department_slug)
            context["department"] = department
        return context
