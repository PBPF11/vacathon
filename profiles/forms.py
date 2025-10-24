from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

from .models import RunnerAchievement, UserProfile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "display_name",
            "bio",
            "city",
            "country",
            "avatar_url",
            "favorite_distance",
            "instagram_handle",
            "strava_profile",
            "website",
            "birth_date",
            "emergency_contact_name",
            "emergency_contact_phone",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} control".strip()


class ProfileAchievementForm(forms.ModelForm):
    class Meta:
        model = RunnerAchievement
        fields = ("title", "description", "achieved_on", "link")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "achieved_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} control".strip()


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "control"


class AccountPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "control"
