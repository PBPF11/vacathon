from django import forms

from events.models import Event, EventCategory
from .models import EventRegistration


class RegistrationForm(forms.ModelForm):
    accept_terms = forms.BooleanField(
        required=True,
        label="I agree to the event terms and conditions.",
    )
    distance_label = forms.CharField(
        required=False,
        label="Preferred distance",
        help_text="If this event offers open categories, specify your target distance.",
    )

    class Meta:
        model = EventRegistration
        fields = [
            "category",
            "phone_number",
            "emergency_contact_name",
            "emergency_contact_phone",
            "medical_notes",
        ]
        widgets = {
            "medical_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.event: Event = kwargs.pop("event")
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        categories = self.event.categories.order_by("distance_km")
        if categories.exists():
            self.fields["category"].queryset = categories
            self.fields["category"].required = True
            self.fields["category"].label = "Select distance"
            self.fields["distance_label"].widget = forms.HiddenInput()
            self.fields["distance_label"].required = False
        else:
            self.fields["category"].widget = forms.HiddenInput()
            self.fields["category"].required = False
            self.fields["distance_label"].required = True
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} control".strip()

    def clean(self):
        cleaned = super().clean()
        if EventRegistration.objects.filter(user=self.user, event=self.event).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError("You have already registered for this event.")

        participant_limit = self.event.participant_limit or 0
        if participant_limit:
            active_qs = EventRegistration.objects.filter(
                event=self.event,
                status__in=[
                    EventRegistration.Status.PENDING,
                    EventRegistration.Status.CONFIRMED,
                    EventRegistration.Status.WAITLISTED,
                ],
            )
            if self.instance.pk:
                active_qs = active_qs.exclude(pk=self.instance.pk)
            active_registrations = active_qs.count()
            if active_registrations >= participant_limit:
                cleaned["waitlisted"] = True
        if not cleaned.get("category") and self.fields["category"].required:
            self.add_error("category", "Please select an available distance.")
        if (
            self.fields["category"].required is False
            and not cleaned.get("distance_label")
        ):
            raise forms.ValidationError("Please specify your intended distance.")
        return cleaned
