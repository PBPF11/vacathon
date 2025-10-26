from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Notification  # Pastikan path import model Notification benar
import json

class NotificationViewTests(TestCase):

    def setUp(self):
        """
        Setup data tes awal untuk setiap metode tes.
        Membuat dua user dan beberapa notifikasi.
        """
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        
        # Notifikasi untuk user1
        self.note1_user1 = Notification.objects.create(recipient=self.user1, title='Note 1 U1', message='Message 1', is_read=False)
        self.note2_user1 = Notification.objects.create(recipient=self.user1, title='Note 2 U1', message='Message 2', is_read=True)
        
        # Notifikasi untuk user2
        self.note1_user2 = Notification.objects.create(recipient=self.user2, title='Note 1 U2', message='Message 3', is_read=False)

        # Client untuk simulasi request
        self.client = Client()

    # --- Tes untuk NotificationListView ---

    def test_notification_list_view_requires_login(self):
        """Tes: Pengguna anonim harus di-redirect ke login."""
        response = self.client.get(reverse('notifications:inbox')) 
        # Asumsi 'notifications:inbox' adalah nama URL untuk NotificationListView
        self.assertEqual(response.status_code, 302) # 302 = Redirect
        # PERBAIKAN: Cek redirect ke URL login custom dari app profiles
        # Menggunakan setting LOGIN_URL default Django jika tidak ada custom
        login_url = reverse('login') # Default Django login URL name
        try:
            # Coba gunakan URL login custom jika ada
            login_url = reverse('profiles:login') # Ganti 'profiles:login' jika nama URL login berbeda
        except:
             pass # Gunakan default jika tidak ada
        self.assertTrue(response.url.startswith(login_url)) 

    def test_notification_list_view_logged_in_user(self):
        """Tes: Pengguna login bisa akses dan melihat notifikasinya."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('notifications:inbox'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications/inbox.html')
        
        # Cek context
        # Untuk ListView Paginasi, nama default context adalah object_list
        self.assertIn('object_list', response.context) 
        self.assertIn('unread_count', response.context)
        
        # Cek notifikasi yang ditampilkan hanya milik user1
        notifications_in_context = response.context['object_list'] 
        self.assertEqual(len(notifications_in_context), 2)
        self.assertTrue(all(note.recipient == self.user1 for note in notifications_in_context))
        
        # Cek unread_count
        self.assertEqual(response.context['unread_count'], 1) 

    # --- Tes untuk notifications_json ---

    def test_notifications_json_requires_login(self):
        """Tes: JSON view butuh login."""
        # PERBAIKAN: Ganti nama URL menjadi 'inbox-json'
        url_name = 'notifications:inbox-json' 
        try:
            url = reverse(url_name)
        except Exception as e:
            self.fail(f"Could not reverse URL '{url_name}'. Check notifications/urls.py. Original error: {e}")
            
        response = self.client.get(url) 
        # Biasanya API view mengembalikan 403 Forbidden atau 401 Unauthorized jika tidak login
        # Atau redirect ke login
        self.assertIn(response.status_code, [302, 401, 403]) 

    def test_notifications_json_structure_and_content(self):
        """Tes: Struktur JSON dan kontennya benar."""
        self.client.login(username='user1', password='password123')
        # PERBAIKAN: Ganti nama URL menjadi 'inbox-json'
        url_name = 'notifications:inbox-json' 
        try:
            url = reverse(url_name)
        except Exception as e:
            self.fail(f"Could not reverse URL '{url_name}'. Check notifications/urls.py. Original error: {e}")

        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        
        data = json.loads(response.content)
        
        self.assertIn('results', data)
        self.assertIn('unread', data)
        
        self.assertEqual(len(data['results']), 2) # Ada 2 notif untuk user1
        self.assertEqual(data['unread'], 1) # Hanya 1 yang belum dibaca
        
        # Cek detail notifikasi pertama (harusnya note2_user1 karena order by created_at desc)
        # Urutan bisa tergantung implementasi database, lebih aman cek ID
        note_ids_in_response = {note['id'] for note in data['results']}
        self.assertIn(self.note1_user1.id, note_ids_in_response)
        self.assertIn(self.note2_user1.id, note_ids_in_response)

        # Cari data note1_user1 (yang unread)
        note1_data = next((note for note in data['results'] if note['id'] == self.note1_user1.id), None)
        self.assertIsNotNone(note1_data)
        self.assertFalse(note1_data['is_read'])


    def test_notifications_json_allows_only_get(self):
        """Tes: Hanya metode GET yang diizinkan."""
        self.client.login(username='user1', password='password123')
        # PERBAIKAN: Ganti nama URL menjadi 'inbox-json'
        url_name = 'notifications:inbox-json' 
        try:
            url = reverse(url_name)
        except Exception as e:
            self.fail(f"Could not reverse URL '{url_name}'. Check notifications/urls.py. Original error: {e}")
            
        response = self.client.post(url) # Coba POST
        self.assertEqual(response.status_code, 405) # 405 = Method Not Allowed

    # --- Tes untuk mark_notification_read ---
        
    def test_mark_read_requires_login(self):
        """Tes: Mark read butuh login."""
        # Asumsi nama URL adalah 'mark-read' (ini sudah benar sesuai urls.py Anda)
        url_name = 'notifications:mark-read' 
        try:
            url = reverse(url_name, kwargs={'pk': self.note1_user1.pk})
        except Exception as e:
            self.fail(f"Could not reverse URL '{url_name}'. Check notifications/urls.py. Original error: {e}")
            
        response = self.client.post(url)
        self.assertIn(response.status_code, [302, 401, 403])

    def test_mark_read_allows_only_post(self):
        """Tes: Hanya metode POST yang diizinkan."""
        self.client.login(username='user1', password='password123')
        # Asumsi nama URL adalah 'mark-read'
        url_name = 'notifications:mark-read' 
        try:
            url = reverse(url_name, kwargs={'pk': self.note1_user1.pk})
        except Exception as e:
            self.fail(f"Could not reverse URL '{url_name}'. Check notifications/urls.py. Original error: {e}")

        response = self.client.get(url) # Coba GET
        self.assertEqual(response.status_code, 405)

    def test_mark_read_success(self):
        """Tes: Berhasil menandai notifikasi sebagai sudah dibaca."""
        self.client.login(username='user1', password='password123')
        
        # Pastikan notifikasi awalnya belum dibaca
        self.note1_user1.refresh_from_db()
        self.assertFalse(self.note1_user1.is_read)

        # Asumsi nama URL adalah 'mark-read'
        url_name = 'notifications:mark-read' 
        try:
            url = reverse(url_name, kwargs={'pk': self.note1_user1.pk})
        except Exception as e:
            self.fail(f"Could not reverse URL '{url_name}'. Check notifications/urls.py. Original error: {e}")

        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Cek di database apakah sudah ditandai read
        self.note1_user1.refresh_from_db()
        self.assertTrue(self.note1_user1.is_read)

    def test_mark_read_not_found(self):
        """Tes: Error 404 jika notifikasi tidak ada."""
        self.client.login(username='user1', password='password123')
        # Asumsi nama URL adalah 'mark-read'
        url_name = 'notifications:mark-read' 
        try:
            url = reverse(url_name, kwargs={'pk': 9999}) # ID yang tidak ada
        except Exception as e:
            self.fail(f"Could not reverse URL '{url_name}'. Check notifications/urls.py. Original error: {e}")
            
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_mark_read_forbidden_for_other_user(self):
        """Tes: Error 404 jika mencoba mark notifikasi user lain."""
        self.client.login(username='user1', password='password123')
        # Coba mark notifikasi milik user2
        # Asumsi nama URL adalah 'mark-read'
        url_name = 'notifications:mark-read' 
        try:
            url = reverse(url_name, kwargs={'pk': self.note1_user2.pk}) 
        except Exception as e:
            self.fail(f"Could not reverse URL '{url_name}'. Check notifications/urls.py. Original error: {e}")

        response = self.client.post(url)
        # Seharusnya 404 karena get_object_or_404 tidak akan menemukannya untuk user1
        self.assertEqual(response.status_code, 404) 

