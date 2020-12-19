from django.urls import path

from . import views

app_name = "journal"

urlpatterns = [
    # Post
    path("", views.home, name="home"),  # 최상위 주소를 뜻한다.    
    path("new/", views.post_new, name="new"),  # 최상위 주소를 뜻한다.
    path("<int:pk>/", views.post_detail, name="detail"),
    path("<int:pk>/next/", views.post_next, name="post_next"),  # 다음 포스트가기
    path("<int:pk>/prev/", views.post_prev, name="post_prev"),  # 이전 포스트가기
    path("<int:pk>/edit/", views.post_edit, name="edit"),  # 포스트 수정
    path("<int:pk>/delete/", views.post_delete, name="delete"),  # 포스트 삭제
    path("<int:pk>/review/", views.post_reviews, name="review"),  # 포스트 댓글보기
    path(
        "<int:pk>/photo/download/",
        views.post_photo_download,
        name="post_photo_download",
    ),  # 포스트 사진 다운로드

    #  Review
    path("<int:journal_pk>/review/new/", views.review_new, name="review_new"),  # 댓글 쓰기
    path(
        "<int:journal_pk>/<int:review_pk>/review/new/",
        views.re_review_new,
        name="re_review_new",
    ),  # 2단계 대댓글 쓰기
    path(
        "<int:journal_pk>/review/edit/<int:pk>/", views.review_edit, name="review_edit"
    ),  # 댓글 수정
    path(
        "<int:journal_pk>/<int:review_pk>/review/edit/<int:pk>/",
        views.re_review_edit,
        name="re_review_edit",
    ),  # 2단계 대댓글  수정
    path(
        "<int:journal_pk>/review/delete/<int:pk>/",
        views.review_delete,
        name="review_delete",
    ),  # 댓글 삭제
    path(
        "<int:journal_pk>/<int:review_pk>/review/delete/<int:pk>/",
        views.re_review_delete,
        name="re_review_delete",
    ),  # 2단계 대댓글 삭제
    path("like/", views.post_likes, name="likes"),  # 좋아요 기능
    path("review/", views.reviews_all, name="reviews_all"),  # 전체 댓글리스트 보기

    # Chart
    path("chart_home/", views.chart_home, name="chart_home"),
    path("population-chart/", views.population_chart, name="population-chart"),

    # Tag
    path("tag/", views.TagCloudTV.as_view(), name="post_tag"),
    path("tag/<str:tag>/", views.post_tag, name="tag_detail"),
]
