from email.policy import default
from django import forms

from api.models import Post


class PostCreateForm(forms.Form):

    title = forms.CharField(label="Title", max_length=50, required=True,
                            widget=forms.TextInput(attrs={'placeholder': 'What\'s this post about?'}))
    description = forms.CharField(
        label="Description", max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Describe your post in a few words...'}))
    visibility = forms.ChoiceField(
        label="Visibility", choices=Post.Visibility.choices, required=True)
    contentType = forms.ChoiceField(
        label="Content Type", choices=Post.ContentType.choices, required=True)
    content = forms.CharField(
        label="Content", max_length=500, required=False, widget=forms.Textarea(attrs={'placeholder': 'Write your post here...'}))
    image = forms.ImageField(required=False, label='Attach a photo')
