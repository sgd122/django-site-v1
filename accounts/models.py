from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from accounts.validators import validate_phone_number


class User(AbstractUser):
    """ Custom User Model """

    # createsuperuser 커맨드로 유저를 생성할 때 나타날 필드 이름 목록
    REQUIRED_FIELDS = ["phone_number"]

    phone_number = models.CharField(
        validators=[validate_phone_number], max_length=17
    )  # validators should be a list
    email_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars", blank=True, help_text="프로필사진")

    def get_absolute_url(self):
        return reverse("my_profile")
