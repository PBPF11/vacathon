from django.db import models
from django.conf import settings # Cara terbaik untuk merujuk ke User model
from django.utils.crypto import get_random_string
import uuid # Untuk reference_code yang unik

# --- ASUMSI FINAL ---
# 1. App 'events' memiliki model 'Event'.
# 2. App 'events' juga memiliki model 'EventCategory' (misal: 5K, 10K).
# 3. Model Registration akan terhubung ke 'events.EventCategory'.
# --------------------

def generate_reference_code():
    """Generates a unique reference code."""
    return f"{uuid.uuid4().hex[:8].upper()}-{get_random_string(4).upper()}"

class Registration(models.Model):
    """
    Model ini menyimpan data pendaftaran user untuk sebuah kategori lomba.
    """
    # === Pilihan Status ===
    STATUS_PENDING_PAYMENT = 'PENDING_PAYMENT'
    STATUS_PENDING_CONFIRMATION = 'PENDING_CONFIRMATION'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, 'Menunggu Pembayaran'),
        (STATUS_PENDING_CONFIRMATION, 'Menunggu Konfirmasi Admin'),
        (STATUS_CONFIRMED, 'Pendaftaran Diterima'),
        (STATUS_REJECTED, 'Pendaftaran Ditolak'),
        (STATUS_CANCELLED, 'Dibatalkan'),
        (STATUS_COMPLETED, 'Selesai'),
    ]

    # === Pilihan Jenis Kelamin ===
    GENDER_CHOICES = [
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ]

    # === Pilihan Ukuran Baju ===
    SHIRT_SIZE_CHOICES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('NS', 'Tidak Ada/Tidak Perlu'),
    ]

    # === FIELD DATABASE ===

    reference_code = models.CharField(
        max_length=15, 
        default=generate_reference_code, 
        unique=True, 
        editable=False,
        help_text="Kode referensi unik pendaftaran."
    )

    # Relasi
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='registrations',
        help_text="User yang mendaftar."
    )
    # --- PERBAIKAN DI SINI ---
    # Merujuk ke model EventCategory di app events
    category = models.ForeignKey(
        'events.EventCategory', # <-- SUDAH BENAR SEKARANG
        on_delete=models.PROTECT, 
        related_name='registrations',
        help_text="Kategori lomba yang dipilih."
    )
    # Untuk mendapatkan Event: Perlu query terpisah karena ManyToMany
    # Contoh: event = Event.objects.filter(categories=self.category, <filter_lain>).first()
    # Atau jika hanya ada satu event per category (tidak mungkin): self.category.events.first()

    # Data Pribadi Peserta (Snapshot)
    full_name = models.CharField(max_length=255, help_text="Nama lengkap.")
    date_of_birth = models.DateField(help_text="Tanggal lahir.")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, help_text="Jenis kelamin.")
    phone_number = models.CharField(max_length=20, help_text="Nomor HP aktif.")
    email = models.EmailField(help_text="Alamat email aktif.")
    address = models.TextField(help_text="Alamat lengkap.")

    # Data Tambahan Lomba
    emergency_contact_name = models.CharField(max_length=255, help_text="Nama kontak darurat.")
    emergency_contact_phone = models.CharField(max_length=20, help_text="Nomor HP kontak darurat.")
    shirt_size = models.CharField(
        max_length=3, 
        choices=SHIRT_SIZE_CHOICES, 
        default='NS',
        help_text="Ukuran baju (jika ada)."
    )
    agreed_to_waiver = models.BooleanField(
        default=False, 
        help_text="Setuju syarat & ketentuan?"
    )

    # Status dan Pembayaran
    status = models.CharField(
        max_length=25, 
        choices=STATUS_CHOICES, 
        default=STATUS_PENDING_PAYMENT,
        help_text="Status pendaftaran."
    )
    payment_proof = models.ImageField(
        upload_to='payment_proofs/', 
        blank=True, 
        null=True,
        help_text="Bukti pembayaran (jika perlu)."
    )

    # Data dari Admin
    bib_number = models.CharField(max_length=20, blank=True, null=True, help_text="Nomor BIB.")
    finish_time = models.DurationField(blank=True, null=True, help_text="Waktu finish.")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pendaftaran Event"
        verbose_name_plural = "Pendaftaran Event"

    def __str__(self):
        return f'{self.full_name} - {self.category.display_name} ({self.reference_code})'
    
    # Perlu cara lain untuk mendapatkan Event spesifik yang didaftar
    # karena hubungan Event <-> Category adalah ManyToMany
    def get_associated_event(self):
        """
        Mencoba mendapatkan Event yang relevan. Ini asumsi, mungkin perlu
        disesuaikan tergantung bagaimana relasi Event-Category digunakan.
        Jika satu Category bisa dipakai di banyak Event, kita butuh info tambahan
        untuk tahu Event mana yang dimaksud saat pendaftaran.
        """
        # Asumsi paling sederhana: Category ini hanya terkait satu Event aktif saat ini?
        # Ini mungkin tidak selalu benar.
        active_events = self.category.events.filter(status__in=['upcoming', 'ongoing'])
        if active_events.count() == 1:
            return active_events.first()
        # Jika tidak jelas, kembalikan None atau perlu logika lain
        return None

