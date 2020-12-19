from django.contrib import admin, messages
from django.utils.html import mark_safe
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from journal.models import Post, Review, Photo, Like, ReReview
from django_summernote.admin import SummernoteModelAdmin


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    pass


@admin.register(ReReview)
class ReReviewAdmin(admin.ModelAdmin):
    pass


@admin.register(Like)
class LikewAdmin(admin.ModelAdmin):
    pass


class PhotoInline(admin.TabularInline):

    model = Photo


class LikeInline(admin.TabularInline):

    model = Like


@admin.register(Post)
class PostAdmin(SummernoteModelAdmin):

    inlines = (PhotoInline, LikeInline)

    search_fields = ["title"]
    list_display = ["id", "title", "created_at"]
    list_display_links = ["title"]
    # list_filter = ["status", "created_at"]
    summernote_fields = ("content",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tags", "likes")

    def count_photos(self, obj):
        return obj.photos.count()

    count_photos.short_description = "Photo Count"


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):

    """ Photo Admin Definition """

    pass
    # list_display = ("__str__", "get_thumbnail")

    # def get_thumbnail(self, obj):
    #     return mark_safe(f'<img width="50px" src="{obj.file.url}"/>')

    # get_thumbnail.short_description = "Thumbnail"