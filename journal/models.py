from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase


# 단어 번역관련
class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TaggedPost(TaggedItemBase):
    content_object = models.ForeignKey("Post", on_delete=models.CASCADE)


class Post(TimestampModel):
    class Meta:
        ordering = ["-id"]  # 디폴트 정렬

    title = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(10),  # Callable Object
        ],
        db_index=True,  # makemigrations 시에 db_index SQL을 자동 추가
    )
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tags = TaggableManager(through=TaggedPost, blank=True)

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,  # User 모델과 Blog 모델을 M:N 관계로 두겠다.
        through="Like",  # Like라는 중개 모델을 통해 M:N 관계를 맺는다.
        through_fields=("post", "user"),  # Like에 post 속성, user 속성을 추가하겠다.
        related_name="likes"  # 1:N 관계에서 post와 연결된 comment를 가져올 때 comment_set으로 가져왔는데
        # related_name을 설정하면 post.like_set이 아니라 blog.likes로 like를 가져올 수 있다.
    )

    post_hit = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self):
        return reverse("journal:detail", args=[self.pk])

    def first_photo(self):
        try:
            (photo,) = self.photo_set.all()[:1]
            return photo.file.url
        except ValueError:
            return None

    def get_next_four_photos(self):
        photos = self.photo_set.all()[1:5]
        return photos

    def like_count(self):
        return self.likes.count()  # 몇 개의 Likes와 연결되어 있는가를 보여주기 위한 메소드

    @property
    def update_counter(self):
        self.post_hit = self.post_hit + 1
        self.save()
        return ""


class Review(TimestampModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(help_text="메시지를 작성해주세요.")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.message


class ReReview(TimestampModel):
    review = models.ForeignKey(Review, on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(help_text="메시지를 작성해주세요.")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.message


class Photo(TimestampModel):
    """ Photo Model Definition """

    caption = models.CharField(max_length=80, blank=True, null=True)
    file = models.ImageField(
        upload_to="journal/post/%Y/%m", blank=True  # 파일을 저장할 때, 저장경로를 계산할 목적으로 사용합니다.
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
