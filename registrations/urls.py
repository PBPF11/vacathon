from django.urls import path

# Impor views dari file views.py di app ini
from .views import (
    MyRegistrationsView,
    RegistrationDetailView,
    RegistrationStartView,
    my_registrations_json, # Jika menggunakan API
)

app_name = "registrations" # Namespace untuk URL (contoh: {% url 'registrations:mine' %})

urlpatterns = [
    # --- URL INI DIUBAH ---
    # URL untuk memulai pendaftaran BARU untuk event DAN kategori tertentu
    # Contoh: /register/jakarta-marathon-2025/10k-run/start/
    path(
        "<slug:event_slug>/<slug:category_slug>/start/", # Menangkap slug event DAN kategori
        RegistrationStartView.as_view(), 
        name="start" # Nama URL ini tetap 'start'
    ),
    # ----------------------
    
    # URL untuk halaman "My Registrations" (daftar pendaftaran user)
    # Contoh: /register/account/registrations/
    path(
        "account/registrations/", 
        MyRegistrationsView.as_view(), 
        name="mine" # Nama URL ini adalah 'mine'
    ),
    
    # URL untuk melihat detail SATU pendaftaran spesifik
    # Contoh: /register/account/registrations/REG-ABCDE12345/
    path(
        "account/registrations/<slug:reference>/", # Menangkap reference_code dari URL
        RegistrationDetailView.as_view(),
        name="detail", # Nama URL ini adalah 'detail'
    ),
    
    # (Opsional) URL untuk API JSON daftar pendaftaran
    # Contoh: /register/account/registrations/api/
    path(
        "account/registrations/api/", 
        my_registrations_json, 
        name="mine-json" # Nama URL ini adalah 'mine-json'
    ),
]

