from django import forms
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from taggit.forms import TagWidget

from .models import Post, Review, ReReview, Photo
from .widgets import PreviewImageFileWidget


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content", "tags"]
        widgets = {
            "content": SummernoteWidget(),
            "tags"   : TagWidget(),
        }

    def get_form(self, form_class):
        initials = {"user": self.request.user}
        form = form_class(initial=initials)
        return form


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 3})}


class ReReviewForm(forms.ModelForm):
    class Meta:
        model = ReReview
        fields = ["message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 3})}


class CreatePhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ("file",)
        widgets = {"file": PreviewImageFileWidget()}


PhotoFormSet = forms.inlineformset_factory(
    Post,
    Photo,
    form=CreatePhotoForm,
    extra=5,
)


class ConfirmPostDeleteForm(forms.ModelForm):
    password = forms.CharField(
        strip=False,
        label=_("Enter your password"),
        widget=forms.PasswordInput(attrs={"placeholder": _("Password")}),
    )

    class Meta:
        model = Post
        fields = []
