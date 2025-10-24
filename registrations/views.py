from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, View
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages

# --- Impor Event DAN EventCategory dari app 'events' ---
from events.models import Event, EventCategory 
# --------------------------------------------------------

# Impor model Registration
from .models import Registration 
# Impor form RegistrationForm
from .forms import RegistrationForm

@method_decorator(login_required, name="dispatch")
class RegistrationStartView(View):
    """Menangani GET (tampil form) & POST (proses form) pendaftaran baru."""
    template_name = "registrations/registration_form.html"

    # Helper method untuk mengambil event dan category dari slug di URL
    def get_event_and_category(self, event_slug, category_slug):
        event = get_object_or_404(Event, slug=event_slug)
        # Pastikan kategori yang dipilih memang ada di event tersebut
        # Kita pakai event.categories.get() karena ini ManyToMany
        category = get_object_or_404(event.categories, slug=category_slug) 
        return event, category

    def get(self, request, *args, **kwargs):
        event_slug = kwargs.get("event_slug")
        category_slug = kwargs.get("category_slug")
        
        try:
            event, category = self.get_event_and_category(event_slug, category_slug)
        # Tangkap error jika event/category tidak ditemukan ATAU jika category tidak ada di event itu
        except (Event.DoesNotExist, EventCategory.DoesNotExist, Exception) as e: 
             messages.error(request, "Invalid event or category specified.")
             return redirect('core:home') # Arahkan ke home jika link salah

        # Cek jika user sudah terdaftar di event ini (di kategori manapun)
        # Kita cek berdasarkan event saja
        existing_registration = Registration.objects.filter(user=request.user, category__event=event).first()
        if existing_registration:
             messages.info(request, f"You are already registered for an event category in {event.title}.")
             # Arahkan ke detail pendaftaran yang sudah ada
             return redirect('registrations:detail', reference=existing_registration.reference_code)

        # Cek jika pendaftaran masih buka
        if not event.is_registration_open:
             messages.warning(request, f"Sorry, registration for {event.title} is closed.")
             # Arahkan ke detail event atau daftar event
             return redirect(event.get_absolute_url() if event else 'events:list') 

        # Buat form, coba isi data awal dari profil user
        initial_data = {
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            # Tambahkan field lain jika ada di model User atau Profile
        }
        form = RegistrationForm(initial=initial_data)
        
        context = {
            'form': form,
            'category': category,
            'event': event, # Kirim event ke template
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        event_slug = kwargs.get("event_slug")
        category_slug = kwargs.get("category_slug")

        try:
            event, category = self.get_event_and_category(event_slug, category_slug)
        except (Event.DoesNotExist, EventCategory.DoesNotExist, Exception) as e:
             messages.error(request, "Invalid event or category specified.")
             return redirect('core:home')
        
        # Cek lagi jika pendaftaran masih buka saat POST
        if not event.is_registration_open:
             messages.warning(request, f"Sorry, registration for {event.title} closed.")
             return redirect(event.get_absolute_url() if event else 'events:list')

        # Proses data form yang dikirim user
        form = RegistrationForm(request.POST, request.FILES) # Tambahkan request.FILES untuk upload gambar

        if form.is_valid():
            registration = form.save(commit=False) # Jangan simpan dulu
            registration.user = request.user # Set user yang login
            registration.category = category # Set kategori yang dipilih
            # Status awal (MENUNGGU) sudah di-set di default model
            registration.save() # Simpan ke database
            
            messages.success(request, f"Successfully registered for {event.title} ({category.display_name})! Your registration is pending confirmation.")
            # Redirect ke halaman 'My Registrations' setelah berhasil
            return redirect('registrations:mine') 
        else:
            # Jika form tidak valid, tampilkan kembali halaman form dengan error
            messages.error(request, "Please correct the errors below.")
            context = {
                'form': form, # Kirim form yang berisi error
                'category': category,
                'event': event,
            }
            return render(request, self.template_name, context) # Render ulang template


# --- Views lain (MyRegistrationsView, RegistrationDetailView) tetap sama ---
@method_decorator(login_required, name="dispatch")
class MyRegistrationsView(ListView):
    model = Registration
    template_name = "registrations/my_registrations.html"
    context_object_name = "registrations"

    def get_queryset(self):
        # Ambil event dari category untuk order_by
        # Perhatikan: Karena ManyToMany, kita perlu path '__event'
        return Registration.objects.filter(user=self.request.user)\
                                   .select_related('category', 'category__event')\
                                   .order_by('-category__event__start_date', '-created_at') # Order by event date first


@method_decorator(login_required, name="dispatch")
class RegistrationDetailView(DetailView):
    model = Registration
    template_name = "registrations/registration_detail.html"
    context_object_name = "registration"
    slug_field = "reference_code" 
    slug_url_kwarg = "reference"

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user)


# --- API View (Opsional, jika diperlukan oleh Javascript) ---
@login_required
def my_registrations_json(request):
    """Returns user's registrations as JSON."""
    registrations = Registration.objects.filter(user=request.user)\
                                      .select_related('category', 'category__event')\
                                      .order_by('-category__event__start_date', '-created_at')\
                                      .values(
                                          'reference_code', 
                                          'status', 
                                          'category__display_name', 
                                          'category__event__title',
                                          'category__event__start_date',
                                          'category__event__city',
                                          'category__event__country'
                                      )
    data = list(registrations) # Convert QuerySet to list for JSON serialization
    return JsonResponse(data, safe=False)

