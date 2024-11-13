from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']  # Adjust based on the fields you want to be editable

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']