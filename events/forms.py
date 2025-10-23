from django import forms
from django.db import models
from .models import Event, EventCategory


class EventFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Search by name or description"}),
    )
    city = forms.CharField(
        required=False,
        label="City",
        widget=forms.TextInput(attrs={"placeholder": "City"}),
    )
    status = forms.ChoiceField(required=False, choices=[], label="Status")
    category = forms.ChoiceField(required=False, choices=[], label="Distance")
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Sort by"),
            ("popularity", "Most popular"),
            ("soonest", "Upcoming soonest"),
            ("latest", "Latest start date"),
        ],
        label="Sort",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        status_choices = [("", "Any status")] + list(Event.Status.choices)
        self.fields["status"].choices = status_choices

        category_choices = [("", "All distances")]
        category_choices.extend(
            (category.id, category.display_name)
            for category in EventCategory.objects.order_by("distance_km")
        )
        self.fields["category"].choices = category_choices

        for field in self.fields.values():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} control".strip()

    def filter_queryset(self, queryset):
        if not self.is_valid():
            return queryset

        q = self.cleaned_data.get("q")
        city = self.cleaned_data.get("city")
        status = self.cleaned_data.get("status")
        category = self.cleaned_data.get("category")
        sort = self.cleaned_data.get("sort_by")

        if q:
            queryset = queryset.filter(
                models.Q(title__icontains=q) | models.Q(description__icontains=q)
            )
        if city:
            queryset = queryset.filter(city__icontains=city)
        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(categories__id=category)

        if sort == "popularity":
            queryset = queryset.order_by("-popularity_score", "start_date")
        elif sort == "soonest":
            queryset = queryset.order_by("start_date")
        elif sort == "latest":
            queryset = queryset.order_by("-start_date")

        return queryset.distinct()
