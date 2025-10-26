from events.models import Event, EventCategory
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from events.models import EventCategory
from .models import RunnerAchievement, UserProfile

from events.models import Event, EventCategory
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

from .models import RunnerAchievement, UserProfile

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "city",
            "start_date",
            "end_date",
            "registration_deadline",
            "categories",
            "status",
            "popularity_score",
        ]
        widgets = {
            "start_date": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "control"
                },
                format='%Y-%m-%dT%H:%M'
            ),
            "end_date": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "control"
                },
                format='%Y-%m-%dT%H:%M'
            ),
            "registration_deadline": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "control"
                },
                format='%Y-%m-%dT%H:%M'
            ),
            "categories": forms.CheckboxSelectMultiple(),
            "description": forms.Textarea(attrs={"rows": 4, "class": "control"}),
            "title": forms.TextInput(attrs={"class": "control"}),
            "city": forms.TextInput(attrs={"class": "control"}),
            "popularity_score": forms.NumberInput(attrs={"class": "control"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['registration_deadline'].input_formats = ['%Y-%m-%dT%H:%M']

        self.fields['categories'].queryset = EventCategory.objects.all()
        self.fields['categories'].label = "Race Categories"


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

class AdminEventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "city", "start_date", "end_date",
                  "registration_deadline", "status", "categories"]