import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView

from .models import Folder, Slide


class FolderNavigationView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "slides/folder_navigation.html"
    context_object_name = "items"

    def get_folder(self):
        folder_id = self.request.GET.get("folder")
        if not folder_id:
            return (
                self.request.user.department.base_folder
                if self.request.user.is_publisher()
                else None
            )

        return get_object_or_404(Folder, id=folder_id)

    def test_func(self):
        if self.request.user.is_admin():
            return True

        folder = self.get_folder()
        return folder and folder.user_has_access(self.request.user)

    def get_queryset(self):
        current = self.get_folder()

        if not current and not self.request.user.is_admin():
            return []

        if current:
            # Get subfolders and slides in current folder
            subfolders = current.subfolders.all()
            slides = current.slides.all()
        else:
            # For admin, show all root folders
            subfolders = Folder.objects.base_folders()
            slides = Slide.objects.get_root_slides()

        items = [
            {
                "id": folder.id,
                "name": folder.name,
                "type": "folder",
                "created_at": folder.created_at,
            }
            for folder in subfolders
        ]

        items.extend(
            [
                {
                    "id": slide.id,
                    "name": slide.name,
                    "slug": slide.slug,
                    "type": "slide",
                    "created_at": slide.created_at,
                    "thumbnail_url": slide.get_thumbnail_url(),
                }
                for slide in slides
            ]
        )

        return sorted(items, key=lambda x: (x["type"], x["name"].lower()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current = self.get_folder()

        context["current_folder"] = current
        context["breadcrumbs"] = self.generate_breadcrumbs(current)
        return context

    def generate_breadcrumbs(self, folder):
        breadcrumbs = []
        current = folder

        while current:
            breadcrumbs.append({"id": current.id, "name": current.name})
            current = current.parent

        breadcrumbs.reverse()
        return breadcrumbs


def create_folder(request):
    if request.method == "POST":
        name = request.POST.get("name")
        parent_id = request.POST.get("parent_id")

        try:
            if parent_id:
                parent = Folder.objects.get(id=parent_id)
                if parent.user_has_access(request.user):
                    Folder.objects.create(name=name, parent=parent)
                else:
                    messages.error(request, "You don't have permission to create folder here.")
            else:
                messages.error(request, "parent doesn't exist.")
            messages.success(request, f'Folder "{name}" created successfully.')
        except Exception as e:
            messages.error(request, f"Error creating folder: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:folder_navigation"))


def rename_folder(request):
    if request.method == "POST":
        folder_id = request.POST.get("folder_id")
        new_name = request.POST.get("new_name")

        try:
            folder = Folder.objects.get(id=folder_id)
            if folder.user_has_access(request.user):
                folder.name = new_name
                folder.save()
                messages.success(request, f'Folder renamed to "{new_name}" successfully.')
            else:
                messages.error(request, "You don't have permission to rename this folder.")
        except Exception as e:
            messages.error(request, f"Error renaming folder: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:folder_navigation"))


def delete_folder(request):
    if request.method == "POST":
        folder_id = request.POST.get("folder_id")

        try:
            folder = Folder.objects.get(id=folder_id)
            if folder.user_has_access(request.user):
                folder.delete()
                messages.success(request, "Folder deleted successfully.")
            else:
                messages.error(request, "You don't have permission to delete this folder.")
        except Exception as e:
            messages.error(request, f"Error deleting folder: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:folder_navigation"))


def folder_details(request):
    if request.method == "POST":
        data = json.loads(request.body)
        folder_id = data.get("folder_id")

        try:
            folder = Folder.objects.get(id=folder_id)
            if folder.user_has_access(request.user):
                data = {
                    "name": folder.name,
                    "created_at": folder.created_at.strftime("%Y-%m-%d %H:%M"),
                    "subfolder_count": folder.subfolders.all().count(),
                    "slide_count": folder.slides.all().count(),
                }
                return JsonResponse(data)
            else:
                return JsonResponse({"error": "Permission denied"}, status=403)
        except Folder.DoesNotExist:
            return JsonResponse({"error": "Folder not found"}, status=404)
