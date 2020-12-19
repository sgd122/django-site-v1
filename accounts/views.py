from django.contrib.auth import authenticate, login, logout
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import (
    FormView,
    UpdateView,
)

from journal.views import PostListView
from . import forms, models, mixins


class LoginView(mixins.LoggedOutOnlyView, FormView):
    template_name = "accounts/login_form.html"
    form_class = forms.LoginForm

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        next_arg = self.request.GET.get("next")
        if next_arg is not None:
            return next_arg
        else:
            return reverse("my_profile")


def log_out(request):
    messages.info(request, "See you later")
    logout(request)
    return redirect(reverse("home"))


class SignUpView(mixins.LoggedOutOnlyView, FormView):
    template_name = "accounts/signup_form.html"
    form_class = forms.SignUpForm
    success_url = reverse_lazy("login")
    initial = {
        "first_name": "",
        "last_name" : "",
        "email"     : "",
    }

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


signup = SignUpView.as_view()


class UserProfileView(mixins.LoggedInOnlyView, PostListView):
    model = models.User
    template_name = "accounts/profile.html"

    def get_queryset(self) -> QuerySet:
        queryset = self.request.user.like_set.all()
        if self.kwargs.get("pk"):
            pk = self.kwargs.get("pk")
            user_obj = models.User.objects.get(pk=pk)
            queryset = user_obj.like_set.all()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.request.user
        if self.kwargs.get("pk"):
            pk = self.kwargs.get("pk")
            user_obj = models.User.objects.get(pk=pk)
        context["user_obj"] = user_obj
        return context


profile = UserProfileView.as_view()


class UpdateProfileView(mixins.LoggedInOnlyView, SuccessMessageMixin, UpdateView):
    model = models.User
    template_name = "accounts/update-profile.html"
    fields = (
        "first_name",
        "last_name",
        "phone_number",
        "email_verified",
    )
    success_message = "Profile이 수정되었습니다."

    def get_object(self, queryset=None):
        return self.request.user

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.fields["first_name"].widget.attrs = {"placeholder": "이름"}
        form.fields["last_name"].widget.attrs = {"placeholder": "성"}
        form.fields["phone_number"].widget.attrs = {"placeholder": "휴대폰번호"}
        form.fields["phone_number"].label = "휴대폰번호"
        form.fields["email_verified"].label = "이메일 알림받기"
        return form

    def get_success_url(self):
        return reverse("my_profile")
