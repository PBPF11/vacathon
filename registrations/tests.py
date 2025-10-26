import json # Ditambahkan untuk tes JSON view
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch # Tambahkan NoReverseMatch
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import uuid # Untuk membuat reference_code jika diperlukan

from events.models import Event, EventCategory 
# --- PERBAIKAN: Impor nama model yang benar ---
from .models import EventRegistration 
# ----------------------------------------------
# Asumsi nama form ini benar, jika beda, ganti di sini
try:
    from .forms import RegistrationForm 
except ImportError:
    # Fallback jika .forms belum ada atau nama form beda
    RegistrationForm = None 

class RegistrationViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Setup data awal yang tidak berubah antar tes."""
        cls.user = User.objects.create_user(username='reguser', password='password123', email='reg@example.com')
        cls.other_user = User.objects.create_user(username='otheruser', password='password123')

        cls.category = EventCategory.objects.create(
            name="10K", 
            distance_km=10.0, 
            display_name="10 Kilometer Race"
        )
        
        cls.open_event = Event.objects.create(
            title="Open Event", 
            description="Event masih buka", 
            city="Test City",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            registration_deadline=timezone.now().date() + datetime.timedelta(days=15),
            status=Event.Status.UPCOMING
        )
        cls.open_event.categories.add(cls.category)
        # Panggil save() secara eksplisit jika slug tidak auto-update di create
        cls.open_event.save() 

        cls.closed_event = Event.objects.create(
            title="Closed Event", 
            description="Event sudah tutup", 
            city="Test City",
            start_date=timezone.now().date() + datetime.timedelta(days=30),
            registration_deadline=timezone.now().date() - datetime.timedelta(days=1), # Kemarin
            status=Event.Status.UPCOMING
        )
        cls.closed_event.categories.add(cls.category)
        cls.closed_event.save()

    def setUp(self):
        """Setup client dan data yang mungkin berubah antar tes."""
        self.client = Client()
        # Buat dummy registration SEGAR untuk setiap tes yang membutuhkannya
        # Ini mencegah state bocor antar tes
        self.existing_reg = EventRegistration.objects.create(
            user=self.user,
            event=self.open_event,
            category=self.category,
            phone_number='111',
            emergency_contact_name='Em',
            emergency_contact_phone='222',
            status=EventRegistration.Status.CONFIRMED 
        )

        # URL untuk start registration (sesuai urls.py temanmu)
        self.start_url = reverse('registrations:start', kwargs={'slug': self.open_event.slug}) 
        self.closed_url = reverse('registrations:start', kwargs={'slug': self.closed_event.slug})

        # --- PERBAIKAN: Sesuaikan valid_post_data dengan field EventRegistration & RegistrationForm ---
        self.valid_post_data = {
            'category': self.category.pk, # Wajib ada di form
            'phone_number': '08123456789', # Wajib ada
            'emergency_contact_name': 'Jane Doe', # Wajib ada
            'emergency_contact_phone': '08987654321', # Wajib ada
            'medical_notes': 'None', # Opsional (blank=True)
            # --- PERBAIKAN: Tambahkan field accept_terms (atau agreed_to_waiver) ---
            # Ganti 'accept_terms' dengan nama field sebenarnya di form jika beda
            'accept_terms': 'on', # Nilai 'on' untuk checkbox HTML
            # --------------------------------------------------------------------------
        }
        # ------------------------------------------------------------------------------------------

    # --- Tes untuk RegistrationStartView ---

    def test_start_view_requires_login(self):
        """Tes: Halaman form registrasi butuh login."""
        response = self.client.get(self.start_url)
        self.assertEqual(response.status_code, 302) 
        # Cek redirect ke URL login (sesuaikan jika custom)
        try:
            # Ganti 'profiles:login' jika nama URL login berbeda di profiles/urls.py
            login_url = reverse('profiles:login') 
        except NoReverseMatch:
             try:
                 login_url = reverse('login') # Fallback ke default
             except NoReverseMatch:
                 self.fail("Could not reverse login URL. Check settings.LOGIN_URL and relevant urls.py")
        
        # Periksa apakah URL redirect dimulai dengan URL login yang diharapkan
        self.assertTrue(response.url.startswith(login_url), f"Redirect URL '{response.url}' does not start with expected login URL '{login_url}'")


    def test_start_view_get_success(self):
        """Tes: User login bisa akses form GET."""
        self.client.login(username='reguser', password='password123')
        response = self.client.get(self.start_url)
        self.assertEqual(response.status_code, 200)
        # Sesuaikan nama template jika berbeda (register.html sesuai view temanmu)
        self.assertTemplateUsed(response, 'registrations/register.html') 
        self.assertIn('form', response.context)
        self.assertIn('event', response.context)
        self.assertEqual(response.context['event'], self.open_event)

    def test_start_view_get_registration_closed(self):
        """Tes: Harusnya redirect jika pendaftaran event sudah tutup."""
        # --- CATATAN: Tes ini GAGAL (200 != 302) karena view temanmu tidak redirect ---
        # --- Anda perlu memperbaiki RegistrationStartView.dispatch atau get ---
        self.client.login(username='reguser', password='password123')
        response = self.client.get(self.closed_url)
        
        # Assertion yang SEHARUSNYA (jika view benar):
        self.assertEqual(response.status_code, 302, "View should redirect (302) when registration is closed, but returned 200.") 
        if hasattr(self.closed_event, 'get_absolute_url'):
             # Redirect mungkin ke detail event atau daftar event
             # Cek salah satu kemungkinan
             try:
                 expected_redirect_url = self.closed_event.get_absolute_url()
                 self.assertIn(expected_redirect_url, response.url)
             except AttributeError:
                 # Jika get_absolute_url tidak ada, coba redirect ke daftar event
                 try:
                     expected_redirect_url = reverse('events:list')
                     self.assertIn(expected_redirect_url, response.url)
                 except NoReverseMatch:
                     pass # Tidak bisa cek redirect target dengan pasti
        
        # Assertion SEMENTARA agar tes tidak gagal total (opsional):
        # self.assertEqual(response.status_code, 200)
        # self.assertContains(response, "Registration is currently closed") # Cek pesan error di template

    def test_start_view_get_already_registered(self):
        """Tes: Menampilkan form pre-filled jika user sudah terdaftar."""
        self.client.login(username='reguser', password='password123')
        response = self.client.get(self.start_url) 
        self.assertEqual(response.status_code, 200) 
        self.assertTemplateUsed(response, 'registrations/register.html')
        self.assertIn('existing_registration', response.context)
        self.assertEqual(response.context['existing_registration'], self.existing_reg)
        form = response.context['form']
        
        # --- PERBAIKAN: Bandingkan dengan PK category ---
        # Pastikan field 'category' ada di initial data form
        self.assertIn('category', form.initial)
        self.assertEqual(form.initial.get('category'), self.existing_reg.category.pk) 
        # ---------------------------------------------
        # Pastikan field 'phone_number' ada di initial data form
        self.assertIn('phone_number', form.initial) 
        self.assertEqual(form.initial.get('phone_number'), self.existing_reg.phone_number)


    def test_start_view_post_valid_create(self):
        """Tes: Submit form registrasi baru dengan data valid."""
        # Hapus dulu registrasi yang dibuat di setUp
        EventRegistration.objects.filter(user=self.user, event=self.open_event).delete()
        
        self.client.login(username='reguser', password='password123')
        response = self.client.post(self.start_url, self.valid_post_data)
        
        # --- CATATAN: Tes ini GAGAL (200 != 302) kemungkinan karena form invalid ---
        # --- Perbaikan valid_post_data sudah dilakukan ---
        
        # Cek apakah form valid (untuk debugging)
        if response.status_code == 200 and 'form' in response.context:
             form_in_context = response.context['form']
             # Tampilkan error jika form tidak valid
             if not form_in_context.is_valid():
                 print("\nDEBUG (test_start_view_post_valid_create): Form errors:", form_in_context.errors.as_json()) # Tampilkan sebagai JSON
             print("DEBUG: Submitted data:", self.valid_post_data)


        # Assertion yang SEHARUSNYA:
        self.assertEqual(response.status_code, 302, f"Expected redirect (302) after valid POST, got {response.status_code}. Check form errors above.") 
        
        # Cek data HANYA jika redirect berhasil
        if response.status_code == 302:
            self.assertTrue(EventRegistration.objects.filter(user=self.user, event=self.open_event).exists())
            registration = EventRegistration.objects.get(user=self.user, event=self.open_event)
            # Cek redirect ke halaman detail registrasi
            self.assertRedirects(response, reverse('registrations:detail', kwargs={'reference': registration.reference_code}))
            self.assertEqual(registration.phone_number, '08123456789')
            self.assertEqual(registration.status, EventRegistration.Status.PENDING)

    def test_start_view_post_valid_update(self):
        """Tes: Submit form untuk mengupdate registrasi yang ada."""
        self.client.login(username='reguser', password='password123')
        update_data = self.valid_post_data.copy()
        update_data['phone_number'] = '999888777' 
        
        response = self.client.post(self.start_url, update_data)

        # --- CATATAN: Tes ini GAGAL (200 != 302) kemungkinan karena form invalid ---
        # --- Perbaikan valid_post_data sudah dilakukan ---
        
        # Cek apakah form valid (untuk debugging)
        if response.status_code == 200 and 'form' in response.context:
             form_in_context = response.context['form']
             # Tampilkan error jika form tidak valid
             if not form_in_context.is_valid():
                print("\nDEBUG (test_start_view_post_valid_update): Form errors:", form_in_context.errors.as_json()) # Tampilkan sebagai JSON
             print("DEBUG: Submitted data:", update_data)

        # Assertion yang SEHARUSNYA:
        self.assertEqual(response.status_code, 302, f"Expected redirect (302) after valid update POST, got {response.status_code}. Check form errors above.") 

        # Cek data HANYA jika redirect berhasil
        if response.status_code == 302:
            self.assertRedirects(response, reverse('registrations:detail', kwargs={'reference': self.existing_reg.reference_code}))
            self.existing_reg.refresh_from_db()
            self.assertEqual(self.existing_reg.phone_number, '999888777')


    def test_start_view_post_invalid(self):
        """Tes: Submit form registrasi dengan data tidak valid."""
        self.client.login(username='reguser', password='password123')
        invalid_data = self.valid_post_data.copy()
        # Hapus field yang required (sesuaikan dengan form asli)
        if 'phone_number' in invalid_data: 
            del invalid_data['phone_number'] 
        else:
             self.fail("Setup error: 'phone_number' not in valid_post_data")

        response = self.client.post(self.start_url, invalid_data)
        
        self.assertEqual(response.status_code, 200) # Tetap di halaman form
        self.assertTemplateUsed(response, 'registrations/register.html')
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid()) # Form tidak valid
        self.assertIn('phone_number', form.errors) # Ada error di field phone_number

    # --- Tes untuk MyRegistrationsView ---

    def test_my_registrations_view_requires_login(self):
        """Tes: My Registrations butuh login."""
        url_name = 'registrations:mine'
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
        except NoReverseMatch as e:
            self.fail(f"Could not reverse URL '{url_name}'. Check registrations/urls.py. Original error: {e}")


    def test_my_registrations_view_logged_in(self):
        """Tes: Menampilkan daftar registrasi user."""
        self.client.login(username='reguser', password='password123')
        url_name = 'registrations:mine'
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'registrations/my_registrations.html')
            self.assertIn('registrations', response.context) # Nama context object
            registrations = response.context['registrations']
            # Pastikan registrasi yang dibuat di setUp ada di daftar
            self.assertIn(self.existing_reg, registrations)
            # Periksa apakah user benar
            if registrations: # Cek jika list tidak kosong
                self.assertEqual(registrations[0].user, self.user)
        except NoReverseMatch as e:
             self.fail(f"Could not reverse URL '{url_name}'. Check registrations/urls.py. Original error: {e}")


    # --- Tes untuk RegistrationDetailView ---
    
    def test_registration_detail_view_requires_login(self):
        """Tes: Detail registrasi butuh login."""
        url_name = 'registrations:detail'
        try:
            # Pastikan reference_code ada sebelum reverse
            ref_code = self.existing_reg.reference_code 
            url = reverse(url_name, kwargs={'reference': ref_code})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
        except NoReverseMatch as e:
             self.fail(f"Could not reverse URL '{url_name}' with reference '{ref_code}'. Check registrations/urls.py. Original error: {e}")
        except AttributeError:
             self.fail("self.existing_reg might not have reference_code yet.")
        

    def test_registration_detail_view_success(self):
        """Tes: User bisa melihat detail registrasinya."""
        self.client.login(username='reguser', password='password123')
        url_name = 'registrations:detail'
        try:
            ref_code = self.existing_reg.reference_code
            url = reverse(url_name, kwargs={'reference': ref_code})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'registrations/detail.html')
            self.assertIn('registration', response.context)
            self.assertEqual(response.context['registration'], self.existing_reg)
        except NoReverseMatch as e:
             self.fail(f"Could not reverse URL '{url_name}' with reference '{ref_code}'. Check registrations/urls.py. Original error: {e}")
        except AttributeError:
             self.fail("self.existing_reg might not have reference_code yet.")

    def test_registration_detail_view_forbidden_for_other_user(self):
        """Tes: User tidak bisa melihat detail registrasi user lain."""
        # --- CATATAN: Tes ini GAGAL (200 != 404) karena view temanmu tidak memfilter user ---
        # --- Anda perlu memperbaiki RegistrationDetailView.get_queryset ---
        other_reg = EventRegistration.objects.create(
            user=self.other_user, 
            event=self.open_event,
            category=self.category,
            phone_number='333',
            emergency_contact_name='Other Em',
            emergency_contact_phone='444',
        )
        
        self.client.login(username='reguser', password='password123') # Login sebagai user utama
        url_name = 'registrations:detail'
        try:
            ref_code = other_reg.reference_code
            url = reverse(url_name, kwargs={'reference': ref_code})
            response = self.client.get(url)
            # Assertion yang SEHARUSNYA (jika view benar):
            self.assertEqual(response.status_code, 404, "View should return 404 for other user's registration, but returned 200.") 
        except NoReverseMatch as e:
             self.fail(f"Could not reverse URL '{url_name}' with reference '{ref_code}'. Check registrations/urls.py. Original error: {e}")
        except AttributeError:
             self.fail("other_reg might not have reference_code yet.")


    # --- Tes untuk my_registrations_json ---

    def test_my_registrations_json_requires_login(self):
        """Tes: JSON view butuh login."""
        url_name = 'registrations:mine-json'
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertIn(response.status_code, [302, 401, 403])
        except NoReverseMatch as e:
             self.fail(f"Could not reverse URL '{url_name}'. Check registrations/urls.py. Original error: {e}")


    def test_my_registrations_json_success(self):
        """Tes: JSON view mengembalikan data yang benar."""
        # --- CATATAN: Tes ini GAGAL (404 != 200). Penyebab belum jelas. ---
        self.client.login(username='reguser', password='password123')
        url_name = 'registrations:mine-json'
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            
            # Debugging tambahan:
            if response.status_code != 200:
                print(f"\nDEBUG (test_my_registrations_json_success): Status code was {response.status_code}")
                # Coba decode content jika memungkinkan, hati-hati jika bukan text
                try:
                    print("DEBUG: Response content:", response.content.decode('utf-8'))
                except UnicodeDecodeError:
                    print("DEBUG: Response content is not UTF-8 decodable.")
            
            self.assertEqual(response.status_code, 200, f"Expected 200 OK for {url}, got {response.status_code}") 
            # Periksa Content-Type dengan lebih fleksibel
            self.assertTrue(response.has_header('Content-Type'))
            self.assertIn('application/json', response['content-type'].lower())
            
            try:
                data = response.json() # Gunakan response.json()
                self.assertIn('results', data)
                self.assertIsInstance(data['results'], list)
                # Pastikan registrasi yang dibuat di setUp ada di hasil
                # Perlu konversi UUID ke string untuk perbandingan JSON
                existing_ref_code_str = str(self.existing_reg.reference_code)
                found = any(item.get('reference') == existing_ref_code_str for item in data['results'])
                self.assertTrue(found, f"Existing registration ref '{existing_ref_code_str}' not found in JSON results: {data['results']}")
                # Periksa field lain hanya jika hasil tidak kosong
                if data['results']:
                    self.assertEqual(data['results'][0].get('event'), self.open_event.title)
            except json.JSONDecodeError:
                self.fail("Response was not valid JSON.")
            except AttributeError:
                 self.fail("self.existing_reg might not have reference_code yet.")
        except NoReverseMatch as e:
             self.fail(f"Could not reverse URL '{url_name}'. Check registrations/urls.py. Original error: {e}")

    # Tes untuk register_ajax bisa ditambahkan jika fitur itu aktif digunakan

