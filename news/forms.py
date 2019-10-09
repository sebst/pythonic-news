from django import forms

from .models import Comment, Story

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


class AddStoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['title', 'url', 'text']

    def clean(self):
        cleaned_data = super().clean()

        title = self.cleaned_data.get('title')
        text = self.cleaned_data.get('text')
        url = self.cleaned_data.get('url')
        if not title:
            raise forms.ValidationError("Please provide a title.")
        if (not text) and (not url):
            raise forms.ValidationError("Please provide either a text or a URL.")



class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['title', 'text']

    
