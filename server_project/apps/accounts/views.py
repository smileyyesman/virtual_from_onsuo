from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import CreateView

from .admin import UserCreationForm


class RegistrationView(CreateView):
    form_class = UserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class LoginView(BaseLoginView):
    template_name = "accounts/login.html"
    success_url = reverse_lazy("home")
    redirect_field_name = "next"

    def form_valid(self, form):
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            return next_url
        return self.success_url


class LogoutView(BaseLogoutView):
    # next_page = reverse_lazy("home")
    template_name = "accounts/logout.html"


class HomeView(View):
    template_name = "accounts/home.html"

    def get(self, request):
        return render(request, self.template_name)
