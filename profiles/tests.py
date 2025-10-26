import json
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.models import User
from django.contrib.messages import get_messages # Untuk cek messages
from django.contrib.auth.hashers import check_password # Untuk cek password change
# --- TAMBAHKAN IMPORT INI ---
from django.utils import timezone 
import datetime
# -----------------------------

# --- Impor Model & Form dari App Profiles ---
# (Pastikan UserProfile diimpor sebelum digunakan di setUpTestData)
from .models import UserProfile, RunnerAchievement, UserRaceHistory 
# Asumsi nama form ini benar
# Import form jika ada dan relevan untuk tes view
# --- PERBAIKAN: Tambahkan PasswordChangeForm ---
from django.contrib.auth.forms import PasswordChangeForm 
# ---------------------------------------------
try:
    from .forms import ProfileForm, AccountSettingsForm, ProfileAchievementForm 
    # Kita asumsikan AccountPasswordForm adalah PasswordChangeForm bawaan
    # Jika Anda punya form kustom, impor nama yang benar
    AccountPasswordForm = PasswordChangeForm 
except ImportError:
    ProfileForm = None
    AccountSettingsForm = None
    ProfileAchievementForm = None
    AccountPasswordForm = None # Handle jika form tidak ada

# Kita butuh UserCreationForm & AuthenticationForm untuk tes view register & login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# Impor model lain yang mungkin dibutuhkan (misal Event jika diperlukan di context)
from events.models import Event 

class ProfileViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """Setup data awal yang tidak berubah antar tes."""
        cls.user = User.objects.create_user(
            username='profileuser', 
            password='password123', 
            email='profile@example.com',
            first_name='Test',
            last_name='User'
        )
        # --- PERBAIKAN: Gunakan get_or_create untuk mengambil profil yang mungkin sudah dibuat signal ---
        cls.user_profile, created_user_profile = UserProfile.objects.get_or_create(
            user=cls.user, 
            defaults={'city': "Test City"} # Hanya set city jika baru dibuat
        )
        # Jika sudah ada, update city jika perlu (opsional)
        if not created_user_profile and not cls.user_profile.city:
            cls.user_profile.city = "Test City"
            cls.user_profile.save()
        # -----------------------------------------------------------------------------------------
        
        # Buat user admin untuk tes admin views (jika diperlukan nanti)
        cls.admin_user = User.objects.create_superuser(
            username='adminuser', 
            password='password123', 
            email='admin@example.com'
        )
        # --- PERBAIKAN: Gunakan get_or_create juga untuk profil admin ---
        cls.admin_profile, _ = UserProfile.objects.get_or_create(user=cls.admin_user)
        # -----------------------------------------------------------------

        
        # Buat data dummy lain jika perlu (misal Event, Achievement)
        cls.event = Event.objects.create(
            title="Test Event for History", 
            description="...", 
            city="History City",
            start_date=timezone.now().date() + datetime.timedelta(days=10),
            registration_deadline=timezone.now().date() + datetime.timedelta(days=5)
        )
        # Pastikan achievement dibuat setelah profile ada
        cls.achievement = RunnerAchievement.objects.create(
            profile=cls.user_profile, 
            title="First Achievement"
        )

    def setUp(self):
        """Setup client untuk setiap tes."""
        self.client = Client()
        # Refresh user dan profile object jika perlu (biasanya tidak perlu di setUp jika pakai setUpTestData)
        self.user.refresh_from_db()
        # Akses profile yang sudah pasti ada dari setUpTestData
        self.profile = self.user_profile 


    # --- Tes untuk view 'register' ---
    # Catatan: View 'register' Anda menggunakan UserCreationForm standar
    
    def test_register_view_get(self):
        """Tes: Halaman register GET menampilkan form."""
        url_name = 'profiles:register' # Asumsi nama URL
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'registration/register.html')
            self.assertIsInstance(response.context['form'], UserCreationForm)
        except NoReverseMatch:
            self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")

    def test_register_view_post_valid(self):
        """Tes: Submit form register valid membuat user baru."""
        url_name = 'profiles:register'
        # --- PERBAIKAN: Ganti 'password' menjadi 'password1' ---
        valid_data = {
            'username': 'newsignup',
            'password1': 'newpassword123', # Nama field UserCreationForm
            'password2': 'newpassword123',
        }
        # -------------------------------------------------------
        try:
            url = reverse(url_name)
            initial_user_count = User.objects.count()
            response = self.client.post(url, valid_data)
            
            # Harusnya redirect ke login setelah sukses
            self.assertEqual(response.status_code, 302, f"Expected redirect, got {response.status_code}. Response: {response.content.decode('utf-8')[:200]}") 
            try:
                login_url = reverse('profiles:login')
            except NoReverseMatch:
                 try:
                    login_url = reverse('login') # Fallback
                 except NoReverseMatch:
                     self.fail("Could not reverse login URL ('profiles:login' or 'login')")

            self.assertTrue(response.url.startswith(login_url), f"Redirect URL '{response.url}' does not start with expected login URL '{login_url}'")
            
            # Cek user baru ada di database
            self.assertEqual(User.objects.count(), initial_user_count + 1)
            self.assertTrue(User.objects.filter(username='newsignup').exists())
            
            # Cek pesan sukses
            messages = list(get_messages(response.wsgi_request))
            self.assertGreaterEqual(len(messages), 1, "No success message found.")
            self.assertEqual(str(messages[0]), 'Your account has been created. You can now log in.')

        except NoReverseMatch:
            self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")

    def test_register_view_post_invalid_password_mismatch(self):
        """Tes: Submit form register dengan password tidak cocok."""
        url_name = 'profiles:register'
        # --- PERBAIKAN: Ganti 'password' menjadi 'password1' ---
        invalid_data = {
            'username': 'badsignup',
            'password1': 'password123', # Nama field UserCreationForm
            'password2': 'password456', # Password tidak cocok
        }
        # -------------------------------------------------------
        try:
            url = reverse(url_name)
            response = self.client.post(url, invalid_data)
            
            self.assertEqual(response.status_code, 200) # Tetap di halaman form
            self.assertTemplateUsed(response, 'registration/register.html')
            form = response.context['form']
            self.assertFalse(form.is_valid())
            self.assertIn('password2', form.errors) # Error di konfirmasi password

        except NoReverseMatch:
            self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")

    # --- Tes untuk view 'login_view' ---
    
    def test_login_view_get(self):
        """Tes: Halaman login GET menampilkan form."""
        url_name = 'profiles:login' # Asumsi nama URL
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'registration/login.html')
            self.assertIsInstance(response.context['form'], AuthenticationForm)
        except NoReverseMatch:
             # Fallback ke URL login default jika profiles:login tidak ada
             try:
                 url_name = 'login'
                 url = reverse(url_name)
                 response = self.client.get(url)
                 self.assertEqual(response.status_code, 200)
                 self.assertTemplateUsed(response, 'registration/login.html')
                 self.assertIsInstance(response.context['form'], AuthenticationForm)
             except NoReverseMatch:
                self.fail(f"Could not reverse login URL ('profiles:login' or 'login'). Check urls.py and settings.LOGIN_URL.")

    def test_login_view_post_valid_user(self):
        """Tes: Login valid mengarahkan ke dashboard user."""
        url_name = 'profiles:login' # Asumsi nama URL
        login_data = {'username': 'profileuser', 'password': 'password123'}
        try:
            url = reverse(url_name)
        except NoReverseMatch:
            url_name = 'login' # Fallback
            url = reverse(url_name)
            
        response = self.client.post(url, login_data, follow=True) # Tambahkan follow=True
        self.assertEqual(response.status_code, 200) # Setelah redirect, status 200
        try:
            dashboard_url = reverse('profiles:dashboard')
            # Cek path terakhir setelah redirect
            # Periksa redirect chain bisa kosong jika tidak ada redirect
            if response.redirect_chain:
                self.assertEqual(response.redirect_chain[-1][0], dashboard_url) 
                self.assertEqual(response.redirect_chain[-1][1], 302)
            else:
                # Jika tidak ada redirect, pastikan kita ada di halaman dashboard
                self.assertEqual(response.request['PATH_INFO'], dashboard_url)

        except NoReverseMatch:
            self.fail("Could not reverse URL 'profiles:dashboard'. Check profiles/urls.py.")
        
        # Cek apakah user ter-login
        # Cara cek user setelah redirect dengan follow=True
        self.assertTrue('_auth_user_id' in self.client.session) 
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.id))

    def test_login_view_post_valid_admin(self):
        """Tes: Login admin valid mengarahkan ke dashboard admin."""
        url_name = 'profiles:login' # Asumsi nama URL
        login_data = {'username': 'adminuser', 'password': 'password123'}
        try:
            url = reverse(url_name)
        except NoReverseMatch:
            url_name = 'login' # Fallback
            url = reverse(url_name)

        response = self.client.post(url, login_data, follow=True)
        self.assertEqual(response.status_code, 200) 
        try:
            admin_dashboard_url = reverse('profiles:admin-dashboard')
            if response.redirect_chain:
                self.assertEqual(response.redirect_chain[-1][0], admin_dashboard_url)
                self.assertEqual(response.redirect_chain[-1][1], 302)
            else:
                 self.assertEqual(response.request['PATH_INFO'], admin_dashboard_url)

        except NoReverseMatch:
             self.fail("Could not reverse URL 'profiles:admin-dashboard'. Check profiles/urls.py.")
        
        # Cek apakah user admin ter-login
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.admin_user.id))
        logged_in_user = User.objects.get(pk=self.client.session['_auth_user_id'])
        self.assertTrue(logged_in_user.is_staff)

    def test_login_view_post_invalid_password(self):
        """Tes: Login dengan password salah."""
        url_name = 'profiles:login' # Asumsi nama URL
        login_data = {'username': 'profileuser', 'password': 'wrongpassword'}
        try:
            url = reverse(url_name)
        except NoReverseMatch:
            url_name = 'login' # Fallback
            url = reverse(url_name)

        response = self.client.post(url, login_data)
        self.assertEqual(response.status_code, 200) # Tetap di halaman login
        self.assertIn('form', response.context) # Pastikan form ada di context
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors) # Error global

    # --- Tes untuk DashboardView ---
    
    def test_dashboard_view_requires_login(self):
        """Tes: Dashboard butuh login."""
        url_name = 'profiles:dashboard'
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302) # Redirect ke login
        except NoReverseMatch:
             self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")

    def test_dashboard_view_logged_in(self):
        """Tes: User login bisa akses dashboard."""
        self.client.login(username='profileuser', password='password123')
        url_name = 'profiles:dashboard'
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'profiles/dashboard.html')
            self.assertIn('profile', response.context)
            self.assertIn('upcoming_history', response.context)
            self.assertIn('completed_history', response.context)
            self.assertIn('achievements', response.context)
            self.assertIn('stats', response.context)
            self.assertEqual(response.context['profile'], self.profile)
        except NoReverseMatch:
             self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")

    # --- Tes untuk ProfileUpdateView / AccountSettingsView ---
    
    def test_settings_view_requires_login(self):
        """Tes: Halaman settings butuh login."""
        url_name = 'profiles:settings' 
        try:
            url = reverse(url_name) 
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302) 
        except NoReverseMatch:
             self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")


    def test_settings_view_get(self):
        """Tes: GET ke settings view menampilkan form terisi."""
        self.client.login(username='profileuser', password='password123')
        url_name = 'profiles:settings' 
        try:
            url = reverse(url_name) 
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'profiles/account_settings.html') 
            self.assertIn('profile_form', response.context)
            self.assertIn('account_form', response.context)
            self.assertIn('password_form', response.context)
            # Pastikan form diimport sebelum cek instance
            if ProfileForm: 
                self.assertIsInstance(response.context['profile_form'], ProfileForm)
            self.assertEqual(response.context['profile_form'].instance, self.profile)
            # Cek instance password form (jika AccountPasswordForm adalah PasswordChangeForm)
            if AccountPasswordForm and isinstance(AccountPasswordForm(), PasswordChangeForm):
                self.assertIsInstance(response.context['password_form'], PasswordChangeForm)

        except NoReverseMatch:
             self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")


    def test_settings_view_post_valid_profile_action(self):
        """Tes: POST valid ke settings (action=profile) mengupdate profile."""
        self.client.login(username='profileuser', password='password123')
        url_name = 'profiles:settings' 
        update_data = {
            'action': 'profile', # Penting untuk view AccountSettingsView
            'profile-city': 'Updated City',
            'profile-country': 'Updated Country',
            'profile-bio': 'Updated Bio',
            # Tambahkan field lain dari ProfileForm jika ada, dengan prefix profile-
            # Contoh: 'profile-favorite_distance': '10K'
            # Perlu lihat ProfileForm untuk field yang pasti
            # Asumsi field city, country, bio ada di ProfileForm
        }
        # Tambahkan field lain yang mungkin required oleh ProfileForm
        if ProfileForm:
            # Dapatkan fields dari form (jika form bisa diimpor)
            form_fields = ProfileForm().fields.keys()
            for field_name in form_fields:
                prefixed_name = f'profile-{field_name}'
                if prefixed_name not in update_data:
                    # Coba ambil nilai awal dari instance
                    initial_value = getattr(self.profile, field_name, '')
                    update_data[prefixed_name] = initial_value if initial_value is not None else ''


        try:
            url = reverse(url_name)
            response = self.client.post(url, update_data, follow=True)
            self.assertEqual(response.status_code, 200, f"Expected 200 after redirect, got {response.status_code}") 
            # Pastikan redirect kembali ke halaman settings
            if response.redirect_chain:
                self.assertEqual(response.redirect_chain[-1][0], url) 
                self.assertEqual(response.redirect_chain[-1][1], 302)
            else:
                self.assertEqual(response.request['PATH_INFO'], url)

            # Cek data di database
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.city, 'Updated City')
            self.assertEqual(self.profile.bio, 'Updated Bio')
            
            # Cek pesan sukses
            messages = list(get_messages(response.wsgi_request))
            self.assertGreaterEqual(len(messages), 1)
            self.assertEqual(str(messages[0]), 'Profile information updated.') 

        except NoReverseMatch:
             self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")

    # Tes untuk action='account' dan action='password' di AccountSettingsView
    # Contoh tes untuk action='account'
    def test_settings_view_post_valid_account_action(self):
        """Tes: POST valid ke settings (action=account) mengupdate User."""
        self.client.login(username='profileuser', password='password123')
        url = reverse('profiles:settings')
        update_data = {
            'action': 'account',
            'account-first_name': 'NewFirst',
            'account-last_name': 'NewLast',
            'account-email': 'newemail@example.com',
            # Pastikan field ini ada di AccountSettingsForm Anda
        }
        # Tambahkan field lain yang mungkin required oleh AccountSettingsForm
        if AccountSettingsForm:
             form_fields = AccountSettingsForm().fields.keys()
             for field_name in form_fields:
                 prefixed_name = f'account-{field_name}'
                 if prefixed_name not in update_data:
                     initial_value = getattr(self.user, field_name, '')
                     update_data[prefixed_name] = initial_value if initial_value is not None else ''


        response = self.client.post(url, update_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewFirst')
        self.assertEqual(self.user.email, 'newemail@example.com')
        
        messages = list(get_messages(response.wsgi_request))
        self.assertGreaterEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Account details updated.')

    # Tes untuk API Views (json, achievements) bisa ditambahkan
    # dengan pola yang mirip: cek login, GET, POST (valid/invalid), response content/redirect.
    # Ingat pakai client.post(url, data=json.dumps(payload), content_type='application/json') untuk API JSON
    # Contoh tes untuk profile_json API
    def test_profile_json_requires_login(self):
        """Tes: API profile JSON butuh login."""
        url_name = 'profiles:profile-json' # Asumsi nama URL
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            # API biasanya mengembalikan 401 atau 403 jika tidak login
            self.assertIn(response.status_code, [302, 401, 403]) 
        except NoReverseMatch:
             self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")

    def test_profile_json_success(self):
        """Tes: API profile JSON mengembalikan data benar."""
        self.client.login(username='profileuser', password='password123')
        url_name = 'profiles:profile-json' # Asumsi nama URL
        try:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn('application/json', response['content-type'].lower())
            data = response.json()
            self.assertEqual(data.get('username'), 'profileuser')
            self.assertEqual(data.get('city'), 'Test City') # Sesuai get_or_create di setup
            self.assertIsInstance(data.get('achievements'), list)
            # Cek jumlah achievement sesuai setUpTestData
            self.assertEqual(len(data.get('achievements')), 1) 
            self.assertEqual(data['achievements'][0]['title'], 'First Achievement')
        except NoReverseMatch:
             self.fail(f"Could not reverse URL '{url_name}'. Check profiles/urls.py.")

        