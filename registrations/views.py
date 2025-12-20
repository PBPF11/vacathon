from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView, FormView, ListView
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from events.models import Event
from profiles.models import UserProfile
from .forms import RegistrationForm
from .models import EventRegistration


class RegistrationStartView(LoginRequiredMixin, FormView):
    template_name = "registrations/register.html"
    form_class = RegistrationForm

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(
            Event.objects.prefetch_related("categories"),
            slug=kwargs["slug"],
        )
        self.existing_registration = None
        if request.user.is_authenticated:
            self.existing_registration = EventRegistration.objects.filter(
                user=request.user, event=self.event
            ).select_related("category").first()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.event
        kwargs["user"] = self.request.user
        if self.existing_registration:
            kwargs["instance"] = self.existing_registration
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.event
        context["existing_registration"] = self.existing_registration
        context["event_capacity"] = {
            "limit": self.event.participant_limit,
            "registered": self.event.registered_count,
            "remaining": (
                max(self.event.participant_limit - self.event.registered_count, 0)
                if self.event.participant_limit
                else None
            ),
        }
        return context

    def form_valid(self, form):
        waitlisted = form.cleaned_data.pop("waitlisted", False)
        category = form.cleaned_data.get("category")
        distance_label = form.cleaned_data.get("distance_label") or ""
        status = (
            EventRegistration.Status.WAITLISTED
            if waitlisted
            else EventRegistration.Status.PENDING
        )
        registration, created = EventRegistration.objects.update_or_create(
            user=self.request.user,
            event=self.event,
            defaults={
                "category": category,
                "distance_label": category.display_name if category else distance_label,
                "phone_number": form.cleaned_data["phone_number"],
                "emergency_contact_name": form.cleaned_data["emergency_contact_name"],
                "emergency_contact_phone": form.cleaned_data["emergency_contact_phone"],
                "medical_notes": form.cleaned_data.get("medical_notes", ""),
                "status": status,
                "form_payload": {
                    "submitted_via": "web",
                },
            },
        )
        if created:
            message = "Registration submitted successfully."
        else:
            message = "Registration updated successfully."
        if waitlisted:
            message += " You have been placed on the waitlist due to limited slots."
        messages.success(self.request, message)
        return redirect("registrations:detail", reference=registration.reference_code)


class RegistrationDetailView(LoginRequiredMixin, DetailView):
    model = EventRegistration
    slug_url_kwarg = "reference"
    slug_field = "reference_code"
    template_name = "registrations/detail.html"
    context_object_name = "registration"

    def get_queryset(self):
        return EventRegistration.objects.select_related("event", "category", "user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_url"] = self.object.event.get_absolute_url()
        context["dashboard_url"] = reverse("profiles:dashboard")
        return context


class MyRegistrationsView(LoginRequiredMixin, ListView):
    template_name = "registrations/my_registrations.html"
    context_object_name = "registrations"

    def get_queryset(self):
        return EventRegistration.objects.filter(user=self.request.user).select_related(
            "event", "category"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        context["profile"] = profile
        return context


@login_required
@require_GET
def my_registrations_json(request):
    registrations = EventRegistration.objects.filter(user=request.user).select_related(
        "event", "category"
    )
    results = []
    for registration in registrations:
        results.append(
            {
                "reference": registration.reference_code,
                "event": registration.event.title,
                "event_slug": registration.event.slug,
                "status": registration.status,
                "status_display": registration.get_status_display(),
                "category": (
                    registration.category.display_name
                    if registration.category
                    else registration.distance_label
                ),
                "created_at": registration.created_at.isoformat(),
                "url": reverse(
                    "registrations:detail", kwargs={"reference": registration.reference_code}
                ),
            }
        )
    return JsonResponse({"results": results})


@csrf_exempt # Tambahkan ini untuk memudahkan testing API dari mobile
@login_required
@require_POST
def register_ajax(request, slug):
    """AJAX/API endpoint for modal registration form submission."""
    event = get_object_or_404(Event.objects.prefetch_related("categories"), slug=slug)

    # Cek existing registration
    existing_registration = EventRegistration.objects.filter(
        user=request.user, event=event
    ).select_related("category").first()

    # Handle JSON data from Flutter or Form Data
    if request.content_type == 'application/json':
        import json
        data = json.loads(request.body)
        # Handle potential string 'null' values from Flutter serialization
        for key in data:
            if data[key] == 'null':
                data[key] = None
    else:
        data = request.POST

    # For open events (no categories), ensure category is None
    if event.categories.count() == 0:
        data['category'] = None

    form = RegistrationForm(data, event=event, user=request.user, instance=existing_registration)

    if form.is_valid():
        waitlisted = form.cleaned_data.pop("waitlisted", False)
        category = form.cleaned_data.get("category")
        distance_label = form.cleaned_data.get("distance_label") or ""
        status = (
            EventRegistration.Status.WAITLISTED
            if waitlisted
            else EventRegistration.Status.PENDING
        )
        
        # Simpan/Update
        registration, created = EventRegistration.objects.update_or_create(
            user=request.user,
            event=event,
            defaults={
                "category": category,
                "distance_label": category.display_name if category else distance_label,
                "phone_number": form.cleaned_data["phone_number"],
                "emergency_contact_name": form.cleaned_data["emergency_contact_name"],
                "emergency_contact_phone": form.cleaned_data["emergency_contact_phone"],
                "medical_notes": form.cleaned_data.get("medical_notes", ""),
                "status": status,
                "form_payload": {
                    "submitted_via": "api",
                },
            },
        )

        # Helper sederhana untuk serialize Event (agar Event.fromJson di Flutter tidak error)
        def serialize_event(evt):
            return {
                "id": evt.id,
                "title": evt.title,
                "slug": evt.slug,
                "description": evt.description,
                "city": evt.city,
                "country": evt.country,
                "venue": evt.venue,
                "start_date": evt.start_date.isoformat(),
                "end_date": evt.end_date.isoformat() if evt.end_date else None,
                "registration_open_date": evt.registration_open_date.isoformat() if evt.registration_open_date else None,
                "registration_deadline": evt.registration_deadline.isoformat(),
                "status": evt.status,
                "popularity_score": evt.popularity_score,
                "participant_limit": evt.participant_limit,
                "registered_count": evt.registered_count,
                "featured": evt.featured,
                "banner_image": evt.banner_image,
                "categories": [], # Kosongkan untuk ringkas, atau isi jika perlu
                "created_at": evt.created_at.isoformat(),
                "updated_at": evt.updated_at.isoformat(),
            }

        # Return JSON lengkap sesuai model Flutter EventRegistration
        return JsonResponse({
            "success": True,
            "message": "Registration submitted successfully." if created else "Registration updated successfully.",
            "registration_url": reverse("registrations:detail", kwargs={"reference": registration.reference_code}),
            # Data objek untuk Flutter:
            "id": str(registration.id),
            "reference_code": registration.reference_code,
            "user": registration.user.id,
            "user_username": registration.user.username,
            "event": serialize_event(event), # Nested Event Object
            "category": registration.category.id if registration.category else None,
            "category_display_name": registration.category.display_name if registration.category else None,
            "distance_label": registration.distance_label,
            "phone_number": registration.phone_number,
            "emergency_contact_name": registration.emergency_contact_name,
            "emergency_contact_phone": registration.emergency_contact_phone,
            "medical_notes": registration.medical_notes,
            "status": registration.status,
            "payment_status": registration.payment_status,
            "form_payload": registration.form_payload,
            "decision_note": registration.decision_note,
            "created_at": registration.created_at.isoformat(),
            "updated_at": registration.updated_at.isoformat(),
            "confirmed_at": registration.confirmed_at.isoformat() if registration.confirmed_at else None,
            "cancelled_at": registration.cancelled_at.isoformat() if registration.cancelled_at else None,
        })

    return JsonResponse({
        "success": False,
        "errors": form.errors,
        "non_field_errors": form.non_field_errors(),
    }, status=400)
