from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class LoggedOutOnlyView(UserPassesTestMixin):
    def test_func(self):
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        messages.error(self.request, "이미 로그인되어 있습니다.")
        return redirect("home")


class LoggedInOnlyView(LoginRequiredMixin):
    login_url = reverse_lazy("login")
