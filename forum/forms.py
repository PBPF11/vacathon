from django import forms

from events.models import Event
from .models import ForumPost, ForumThread


class ThreadForm(forms.ModelForm):
    class Meta:
        model = ForumThread
        fields = ("event", "title", "body")
        widgets = {
            "event": forms.Select(attrs={"class": "control"}),
            "title": forms.TextInput(attrs={"placeholder": "Thread title", "class": "control"}),
            "body": forms.Textarea(attrs={"rows": 5, "placeholder": "Start the discussion...", "class": "control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event"].queryset = Event.objects.order_by("title")


class PostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Share your thoughts...",
                    "class": "control",
                }
            )
        }

    def clean_content(self):
        content = self.cleaned_data.get("content", "").strip()
        if not content:
            raise forms.ValidationError("Your message cannot be empty.")
        return content
