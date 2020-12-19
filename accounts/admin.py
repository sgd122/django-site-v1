from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from . import models


@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Custom Profile",
            {
                "fields": (
                    "avatar",
                    "phone_number",
                    "email_verified",
                )
            },
        ),
    )

    # list_filter = UserAdmin.list_filter + ("phone_number",)

    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "email_verified",
    )