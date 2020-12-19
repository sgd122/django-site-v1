from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),  # Account
    path("journal/", include("journal.urls")),  # Journal
    path("summernote/", include("django_summernote.urls")),
    path("", RedirectView.as_view(url="/journal"), name="home"),
]

# settings.DEBUG=True 일때에만 동작하며, Flase라면 빈 리스트를 반환합니다.
if settings.DEBUG:
    from django.conf.urls.static import static
    import debug_toolbar

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]