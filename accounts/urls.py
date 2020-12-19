from django.conf import settings
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView, RedirectView
from . import views

urlpatterns = [
    path("", RedirectView.as_view(url="profile/")),
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page=settings.LOGIN_URL),
        name="logout",
    ),
    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile, name="my_profile"),
    path("profile/<int:pk>/", views.profile, name="profile"),
    path("profile/update/", views.UpdateProfileView.as_view(), name="update"),
]
