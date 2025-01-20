import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView

from .models import Folder, Slide


class SlideNavigationView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "slides/slide_navigation.html"
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
                "updated_at": folder.updated_at,
                "author": folder.author.username if folder.author else None,
            }
            for folder in subfolders
        ]
        items.extend(
            [
                {
                    "id": slide.id,
                    "name": slide.name,
                    "type": "slide",
                    "created_at": slide.created_at,
                    "updated_at": slide.updated_at,
                    "author": slide.author.username if slide.author else None,
                    "description": slide.description,
                    "tags": slide.tags,
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

        if self.request.user.is_admin():
            breadcrumbs.append({"id": "", "name": "Root"})

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
                    messages.success(request, f'Folder "{name}" created successfully.')
                else:
                    messages.error(request, "You don't have permission to create folder here.")
            else:
                messages.error(request, "You can't create folder here.")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                messages.warning(request, f'Folder "{name}" already exists. Try another name.')
            else:
                messages.error(request, f"Failed to create folder: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:slide_navigation"))


def rename_folder(request):
    if request.method == "POST":
        folder_id = request.POST.get("folder_id")
        new_name = request.POST.get("new_name")

        try:
            folder = Folder.objects.get(id=folder_id)
            if folder.user_has_access(request.user) and not folder.is_base_folder():
                folder.name = new_name
                folder.save()
                messages.success(request, f'Folder renamed to "{new_name}" successfully.')
            else:
                messages.error(request, "You don't have permission to rename this folder.")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                messages.warning(request, f'Folder "{new_name}" already exists. Try another name.')
            else:
                messages.error(request, f"Failed to rename folder: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:slide_navigation"))


def move_folder(request):
    if request.method == "POST":
        folder_id = request.POST.get("folder_id")
        new_parent_id = request.POST.get("destination_folder_id")

        try:
            folder = Folder.objects.get(id=folder_id)
            new_parent = Folder.objects.get(id=new_parent_id)

            if (
                folder.user_has_access(request.user)
                and new_parent.user_has_access(request.user)
                and not folder.is_base_folder()
            ):
                if not folder.is_children(new_parent) and not folder == new_parent:
                    folder.parent = new_parent
                    folder.save()
                    messages.success(
                        request,
                        f'Folder "{folder.name}" moved to "{new_parent.get_full_path()}" successfully.',
                    )
                else:
                    messages.error(request, "You can't move a folder to its own subfolder.")
            else:
                messages.error(request, "You don't have permission to move this folder.")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                messages.warning(
                    request, f'Folder "{folder.name}" already exists at this location.'
                )
            else:
                messages.error(request, f"Failed to move folder: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:slide_navigation"))


def delete_folder(request):
    if request.method == "POST":
        folder_id = request.POST.get("folder_id")

        try:
            folder = Folder.objects.get(id=folder_id)
            if folder.user_has_access(request.user) and not folder.is_base_folder():
                if folder.is_empty():
                    folder.delete()
                    messages.success(request, f'Folder "{folder.name}" deleted successfully.')
                else:
                    messages.warning(
                        request,
                        f'Folder "{folder.name}" is not empty. Please delete its contents first.',
                    )
            else:
                messages.error(request, "You don't have permission to delete this folder.")
        except Exception as e:
            messages.error(request, f"Failed to delete folder: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:slide_navigation"))


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
                    "updated_at": folder.updated_at.strftime("%Y-%m-%d %H:%M"),
                    "author": folder.author.username if folder.author else None,
                    "subfolder_count": folder.subfolders.all().count(),
                    "slide_count": folder.slides.all().count(),
                }
                return JsonResponse(data)
            else:
                return JsonResponse({"error": "Permission denied"}, status=403)
        except Folder.DoesNotExist:
            return JsonResponse({"error": "Folder not found"}, status=404)


def upload_slide(request):
    if request.method == "POST":
        file = request.FILES.get("slideFile")
        folder_id = request.POST.get("folder_id")
        slide_name = request.POST.get("slide_name")
        slide_description = request.POST.get("slide_description")

        try:
            if file:
                if not folder_id and request.user.is_admin():
                    Slide.objects.create(
                        file=file,
                        name=slide_name,
                        description=slide_description,
                        author=request.user,
                    )
                    messages.success(
                        request, f'Slide "{file.name}" uploaded to "Root" successfully.'
                    )
                else:
                    folder = Folder.objects.get(id=folder_id)
                    if folder.user_has_access(request.user):
                        Slide.objects.create(
                            file=file,
                            name=slide_name,
                            description=slide_description,
                            author=request.user,
                            folder=folder,
                        )
                        messages.success(
                            request,
                            f'Slide "{file.name}" uploaded to "{folder.get_full_path()}" successfully.',
                        )
                    else:
                        messages.error(request, "You don't have permission to upload here.")
            else:
                messages.error(request, "No file selected.")
        except Exception as e:
            messages.error(request, f"Failed to upload slide: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:slide_navigation"))


def edit_slide(request):
    if request.method == "POST":
        slide_id = request.POST.get("slide_id")
        new_name = request.POST.get("new_name")
        new_description = request.POST.get("new_description")

        try:
            slide = Slide.objects.get(id=slide_id)
            if slide.user_has_access(request.user):
                slide.name = new_name
                slide.description = new_description
                slide.save()
                messages.success(request, f'Slide "{slide.name}" updated successfully.')
            else:
                messages.error(request, "You don't have permission to edit this slide.")
        except Exception as e:
            messages.error(request, f"Failed to update slide: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:slide_navigation"))


def move_slide(request):
    if request.method == "POST":
        slide_id = request.POST.get("slide_id")
        new_folder_id = request.POST.get("destination_folder_id")

        try:
            slide = Slide.objects.get(id=slide_id)
            if new_folder_id:
                new_folder = Folder.objects.get(id=new_folder_id)
                if slide.user_has_access(request.user) and new_folder.user_has_access(request.user):
                    slide.folder = new_folder
                    slide.save()
                    messages.success(
                        request,
                        f'Slide "{slide.name}" moved to "{new_folder.get_full_path()}" successfully.',
                    )
                else:
                    messages.error(request, "You don't have permission to move this slide.")
            else:
                if request.user.is_admin():
                    slide.folder = None
                    slide.save()
                    messages.success(request, f'Slide "{slide.name}" moved to "Root" successfully.')
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                messages.warning(request, f'Slide "{slide.name}" already exists at this location.')
            else:
                messages.error(request, f"Failed to move slide: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:slide_navigation"))


def delete_slide(request):
    if request.method == "POST":
        slide_id = request.POST.get("slide_id")

        try:
            slide = Slide.objects.get(id=slide_id)
            if slide.user_has_access(request.user):
                slide.delete()
                messages.success(request, f'Slide "{slide.name}" deleted successfully.')
            else:
                messages.error(request, "You don't have permission to delete this slide.")
        except Exception as e:
            messages.error(request, f"Failed to delete slide: {str(e)}")

        # Redirect back to the same page with the current folder
        return redirect(request.META.get("HTTP_REFERER", "slides:slide_navigation"))


def slide_details(request):
    if request.method == "POST":
        data = json.loads(request.body)
        slide_id = data.get("slide_id")

        try:
            slide = Slide.objects.get(id=slide_id)
            if slide.user_has_access(request.user):
                data = {
                    "name": slide.name,
                    "description": slide.description,
                    "created_at": slide.created_at.strftime("%Y-%m-%d %H:%M"),
                    "updated_at": slide.updated_at.strftime("%Y-%m-%d %H:%M"),
                    "author": slide.author.username,
                    "folder": slide.folder.get_full_path() if slide.folder else "Root",
                    "metadata": slide.metadata,
                    "file": slide.file.name,
                }
                return JsonResponse(data)
            else:
                return JsonResponse({"error": "Permission denied"}, status=403)
        except Slide.DoesNotExist:
            return JsonResponse({"error": "Slide not found"}, status=404)


def get_folder_tree(request):
    def build_tree(folder):
        return {
            "id": folder.id,
            "name": folder.name,
            "subfolders": [build_tree(subfolders) for subfolders in folder.subfolders.all()],
        }

    if request.user.is_admin():
        base_folders = Folder.objects.filter(parent=None)
        tree = [build_tree(folder) for folder in base_folders]
    elif request.user.is_publisher():
        base_folder = request.user.department.base_folder
        tree = [build_tree(base_folder)]
    else:
        tree = []

    data = {
        "tree": tree,
        "show_root": request.user.is_admin(),
    }

    return JsonResponse(data, safe=False)
