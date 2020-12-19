import json
import os
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import Count, QuerySet, ProtectedError
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
    CreateView,
)
from django.views.generic.base import TemplateView
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from accounts import mixins
from .forms import (
    PostForm,
    ReviewForm,
    ReReviewForm,
    PhotoFormSet,
    ConfirmPostDeleteForm
)
from .models import Post, Review, ReReview


class PostListView(ListView):
    model = Post
    queryset = Post.objects.all().prefetch_related("review_set", "photo_set")
    paginate_by = 10  # 10개 단위로 페이지

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        ordering_priority = []
        query: str = self.request.GET.get("query", "")
        if query:
            qs = qs.filter(title__icontains=query)

        # 종합해서 ordering query를 생성한다.
        if self.request.GET.get("sort"):
            if self.request.GET.get("sort") == "post":
                ordering_priority.append("-id")
            elif self.request.GET.get("sort") == "like":
                ordering_priority.append("-likes")
            elif self.request.GET.get("sort") == "mypost":
                qs = qs.filter(author=self.request.user)
            qs = qs.order_by(*ordering_priority)
        return qs

    def get_context_data(self, **kwargs):
        context = super(PostListView, self).get_context_data(**kwargs)
        paginator = context["paginator"]
        page_numbers_range = 5  # Display only 5 page numbers
        max_index = len(paginator.page_range)

        page = self.request.GET.get("page")
        current_page = int(page) if page else 1

        start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
        end_index = start_index + page_numbers_range
        if end_index >= max_index:
            end_index = max_index

        page_range = paginator.page_range[start_index:end_index]
        context["page_range"] = page_range
        return context


home = PostListView.as_view()


####
class TagCloudTV(TemplateView):
    template_name = "journal/tag_list.html"


class PostTagListView(PostListView):
    queryset = Post.objects.all().prefetch_related("review_set", "photo_set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tagname"] = self.kwargs["tag"]
        return context

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        tag_query: str = self.kwargs.get("tag")
        if tag_query:
            qs = qs.filter(tags__name=tag_query)
        return qs


post_tag = PostTagListView.as_view()


####


class PostDetailView(DetailView):
    queryset = Post.objects.all().prefetch_related("review_set", "photo_set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["review_form"] = ReviewForm()
        context["rereview_form"] = ReReviewForm()
        return context


post_detail = PostDetailView.as_view()


def post_next(request, pk):
    qs = Post.objects.filter(pk__gt=pk).order_by("pk").first()
    if not qs:
        qs = Post.objects.get(pk=pk)
    return redirect(reverse("journal:detail", kwargs={"pk": qs.pk}))


def post_prev(requeset, pk):
    qs = Post.objects.filter(pk__lt=pk).order_by("-pk").first()
    if not qs:
        qs = Post.objects.get(pk=pk)
    return redirect(reverse("journal:detail", kwargs={"pk": qs.pk}))


@login_required
def post_new(request):
    if request.method == "POST":
        post_form = PostForm(request.POST)
        photo_formset = PhotoFormSet(request.POST, request.FILES)
        if post_form.is_valid() and photo_formset.is_valid():
            post = post_form.save(commit=False)
            post.author = request.user

            # DB입력시의 순서를 보장하기 위해 transaction을 사용.
            with transaction.atomic():
                # 첫번째: 실제 DB에 저장
                post.save()
                post_form.save_m2m()

                # 두번째
                photo_formset.instance = post
                photo_formset.save()  # 실제 DB에 저장

                ######
                # 메일발송부분
                post_url = reverse("journal:detail", kwargs={"pk": post.pk})
                User = get_user_model()
                post_url = request.scheme + "://" + request.META["HTTP_HOST"] + post_url
                context = {
                    "post"    : post.title,
                    "post_url": post_url,
                }
                # render_to_string을 이용해 HTML코드와 context를 잘 버무려줍니다.
                html = render_to_string("widgets/mail_preview.html", context)
                message = Mail(
                    from_email="sgd0947@gmail.com",
                    to_emails=list(
                        User.objects.filter(email_verified=True).values_list(
                            "email", flat=True
                        )
                    ),
                    subject="mysite에서 새로운 포스트가 등록되었습니다.",
                    html_content=html,
                )

                try:
                    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
                    response = sg.send(message)
                except Exception as e:
                    print(e)
                ######

                messages.success(request, "저장되었습니다.")
                return redirect(post)
    else:
        post_form = PostForm()
        photo_formset = PhotoFormSet()

    return render(
        request,
        "journal/post_create.html",
        {
            "form"         : post_form,
            "photo_formset": photo_formset,
        },
    )


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.method == "POST":
        post_form = PostForm(request.POST, instance=post)
        photo_formset = PhotoFormSet(request.POST, request.FILES, instance=post)

        if post_form.instance.author != request.user and not request.user.is_staff:
            messages.warning(request, "작성자만 수정 가능합니다.")
            return redirect(post)

        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.author = request.user

            # DB입력시의 순서를 보장하기 위해 transaction을 사용.
            with transaction.atomic():
                # 첫번째: 실제 DB에 저장
                post.save()
                post_form.save_m2m()

                # 두번째
                photo_formset.instance = post
                photo_formset.save()  # 실제 DB에 저장

                messages.success(request, "저장되었습니다.")
                return redirect(post)
    else:
        post_form = PostForm(instance=post)
        photo_formset = PhotoFormSet(instance=post)

    return render(
        request,
        "journal/post_edit.html",
        {
            "form"         : post_form,
            "photo_formset": photo_formset,
        },
    )


class PostDeleteView(mixins.LoggedInOnlyView, DeleteView):
    model = Post
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "form" not in kwargs:
            context["form"] = ConfirmPostDeleteForm()

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ConfirmPostDeleteForm(request.POST, instance=self.object)

        if form.instance.author != request.user and not request.user.is_staff:
            messages.warning(request, "작성자만 삭제가 가능합니다.")
            return redirect(reverse("journal:detail", kwargs={"pk": self.object.pk}))

        if not check_password(request.POST.get("password"), request.user.password):
            messages.warning(request, "비밀번호가 잘못되었습니다.")
            return redirect(reverse("journal:detail", kwargs={"pk": self.object.pk}))

        if form.is_valid():
            return self.delete(request, *args, **kwargs)
        else:
            return self.render_to_response(
                self.get_context_data(form=form),
            )


post_delete = PostDeleteView.as_view()


# Review
class CreateReviewView(mixins.LoggedInOnlyView, CreateView):
    model = Review
    form_class = ReviewForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        journal_pk = self.kwargs.get("journal_pk")
        post = get_object_or_404(Post, pk=journal_pk)
        form.instance.post = post
        form.instance.author = self.request.user  # 현재 로그인 유저 객체

        if self.request.is_ajax():  # ajax 방식일 때 아래 코드 실행
            form.instance.message = self.request.POST["message"]
            response = super().form_valid(form)
            message = "추가되었습니다."
            context = {"message": message}
            return HttpResponse(json.dumps(context), content_type="application/json")

        response = super().form_valid(form)
        messages.success(self.request, "추가되었습니다.")
        return redirect(post)


review_new = CreateReviewView.as_view()


class CreateReReviewView(mixins.LoggedInOnlyView, CreateView):
    model = ReReview
    form_class = ReReviewForm
    template_name = "journal/rereview_create.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_pk = self.kwargs.get("review_pk")
        review = get_object_or_404(Review, pk=review_pk)
        context["parent_review"] = review
        return context

    def form_valid(self, form):
        review_pk = self.kwargs.get("review_pk")
        journal_pk = self.kwargs.get("journal_pk")
        post = get_object_or_404(Post, pk=journal_pk)
        review = get_object_or_404(Review, pk=review_pk)
        form.instance.review = review
        form.instance.author = self.request.user  # 현재 로그인 유저 객체

        if self.request.is_ajax():  # ajax 방식일 때 아래 코드 실행
            form.instance.message = self.request.POST["message"]
            response = super().form_valid(form)
            message = "추가되었습니다."
            context = {"message": message}
            return HttpResponse(json.dumps(context), content_type="application/json")

        response = super().form_valid(form)
        messages.success(self.request, "추가되었습니다.")
        return redirect(post)


re_review_new = CreateReReviewView.as_view()


class EditReviewView(mixins.LoggedInOnlyView, UpdateView):
    model = Review
    form_class = ReviewForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        journal_pk = self.kwargs.get("journal_pk")
        post = get_object_or_404(Post, pk=journal_pk)
        form.instance.post = post
        form.instance.author = self.request.user  # 현재 로그인 유저 객체
        messages.success(self.request, "수정되었습니다.")
        if self.request.is_ajax():  # ajax 방식일 때 아래 코드 실행
            form.instance.message = self.request.POST["message"]
            response = super().form_valid(form)
            message = "수정되었습니다."
            context = {"message": message}
            return HttpResponse(json.dumps(context), content_type="application/json")

        response = super().form_valid(form)
        return redirect(post)


review_edit = EditReviewView.as_view()


class EditReReviewView(mixins.LoggedInOnlyView, UpdateView):
    model = ReReview
    form_class = ReReviewForm
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_pk = self.kwargs.get("review_pk")
        review = get_object_or_404(Review, pk=review_pk)
        context["parent_review"] = review
        return context

    def form_valid(self, form):
        review_pk = self.kwargs.get("review_pk")
        journal_pk = self.kwargs.get("journal_pk")
        post = get_object_or_404(Post, pk=journal_pk)
        review = get_object_or_404(Review, pk=review_pk)
        form.instance.review = review
        form.instance.author = self.request.user  # 현재 로그인 유저 객체

        if self.request.is_ajax():  # ajax 방식일 때 아래 코드 실행
            form.instance.message = self.request.POST["message"]
            response = super().form_valid(form)
            message = "수정되었습니다."
            context = {"message": message}
            return HttpResponse(json.dumps(context), content_type="application/json")

        response = super().form_valid(form)
        messages.success(self.request, "추가되었습니다.")
        return redirect(post)


re_review_edit = EditReReviewView.as_view()


class ReviewDeleteView(mixins.LoggedInOnlyView, DeleteView):
    model = Review
    success_url = reverse_lazy("home")

    def post(self, request, *args, **kwargs):
        try:
            return self.delete(request, *args, **kwargs)
        except ProtectedError:
            response = JsonResponse({"error": "하위 댓글이 존재하여 삭제할 수 없습니다."})
            response.status_code = 403
            return response

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        journal_pk = self.kwargs.get("journal_pk")
        if self.request.is_ajax():  # ajax 방식일 때 아래 코드 실행
            message = "삭제되었습니다."
            context = {"message": message}
            return HttpResponse(json.dumps(context), content_type="application/json")
        messages.success(self.request, "삭제되었습니다.")
        return redirect(reverse("journal:detail", kwargs={"pk": journal_pk}))


review_delete = ReviewDeleteView.as_view()


class ReReviewDeleteView(mixins.LoggedInOnlyView, DeleteView):
    model = ReReview
    success_url = reverse_lazy("home")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        journal_pk = self.kwargs.get("journal_pk")
        if self.request.is_ajax():  # ajax 방식일 때 아래 코드 실행
            message = "삭제되었습니다."
            context = {"message": message}
            return HttpResponse(json.dumps(context), content_type="application/json")
        messages.success(self.request, "삭제되었습니다.")
        return redirect(reverse("journal:detail", kwargs={"pk": journal_pk}))


re_review_delete = ReReviewDeleteView.as_view()


# Photo
class PostPhotosView(mixins.LoggedInOnlyView, DetailView):
    model = Post
    template_name = "journal/post_photos.html"

    def get_object(self, queryset=None):
        post = super().get_object(queryset=queryset)
        # if post.host.pk != self.request.user.pk:
        #     raise Http404()
        return post


# 좋아요 기능
@login_required
def post_likes(request):
    if request.is_ajax():  # ajax 방식일 때 아래 코드 실행
        post_pk = request.GET["post_pk"]  # 좋아요를 누른 게시물id (post_pk)가지고 오기
        post = Post.objects.get(id=post_pk)

        if not request.user.is_authenticated:  # 버튼을 누른 유저가 비로그인 유저일 때
            message = "로그인을 해주세요"
            context = {"like_count": post.likes.count(), "message": message}
            return HttpResponse(json.dumps(context), content_type="application/json")

        user = request.user  # request.user : 현재 로그인한 유저
        if post.likes.filter(id=user.id).exists():  # 이미 좋아요를 누른 유저일 때
            post.likes.remove(user)  # like field에 현재 유저 추가
            message = "좋아요 취소"
        else:  # 좋아요를 누르지 않은 유저일 때
            post.likes.add(user)  # like field에 현재 유저 삭제
            message = "좋아요 성공"
        # post.likes.count() : 게시물이 받은 좋아요 수
        context = {"like_count": post.likes.count(), "message": message}
        return HttpResponse(json.dumps(context), content_type="application/json")


def post_reviews(request, pk):
    review = Review.objects.filter(post__id=pk)

    data = list(
        review.values(
            "message",
            "author",
            "author__first_name",
            "id",
            "created_at",
            "post__id",
            "rereview__id",
            "rereview__message",
            "rereview__created_at",
            "rereview__author",
            "rereview__author__first_name",
        )
    )
    return JsonResponse(data, safe=False)


# 전체 댓글리스트 보기
class ReviewListView(PostListView):
    def get_queryset(self) -> QuerySet:
        qs = Review.objects.all().prefetch_related("post")
        return qs


reviews_all = ReviewListView.as_view()


def post_photo_download(request, pk):
    post = get_object_or_404(Post, pk=pk)

    io = BytesIO()  # file-like object, HttpResponse 객체로 file-like object
    with ZipFile(io, "w") as zipfile:
        for photo in post.photo_set.all():
            image_data = photo.file.read()
            image_name = os.path.basename(
                photo.file.path
            )
            zipfile.writestr(image_name, image_data)

    io.seek(0)

    return FileResponse(io, as_attachment=True, filename='export-{}-{}-photos.zip'.format(
        datetime.today().strftime("%Y%m%d"), pk
    ))


def chart_home(request):
    return render(request, "journal/rank.html")


def population_chart(request):
    labels = []
    data = []

    User = get_user_model()
    # queryset = User.objects.values("username").annotate(
    #     country_population=Sum("population")
    # )

    queryset = (
        User.objects.values("username")
            .annotate(
            nposts=Count("post__like"),
            nlikes=Count("like"),
            # nrank=Func(F("nposts") / 10, function="likes"),
        )
            .order_by("-nposts")
    )

    for entry in queryset:
        labels.append(entry["username"])
        data.append(entry["nposts"])

    return JsonResponse(
        data={
            "labels": labels,
            "data"  : data,
        }
    )
