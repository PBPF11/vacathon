from django import forms
from .models import Registration

class RegistrationForm(forms.ModelForm):
    """
    Form untuk user mengisi data pendaftaran event.
    """
    agreed_to_waiver = forms.BooleanField(
        required=True, 
        label="Saya telah membaca dan menyetujui Syarat & Ketentuan serta Pernyataan Medis yang berlaku."
    )

    class Meta:
        model = Registration
        fields = [
            'full_name', 
            'date_of_birth', 
            'gender', 
            'phone_number', 
            'email', 
            'address', 
            'emergency_contact_name', 
            'emergency_contact_phone', 
            'shirt_size', 
            'payment_proof', 
            'agreed_to_waiver', 
        ]
        
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}), 
            'gender': forms.RadioSelect, 
            'address': forms.Textarea(attrs={'rows': 3}), 
        }
        
        labels = {
            'full_name': "Nama Lengkap",
            'date_of_birth': "Tanggal Lahir",
            'gender': "Jenis Kelamin",
            'phone_number': "Nomor HP",
            'email': "Alamat Email",
            'address': "Alamat Lengkap",
            'emergency_contact_name': "Nama Kontak Darurat",
            'emergency_contact_phone': "Nomor HP Kontak Darurat",
            'shirt_size': "Ukuran Baju (jika ada)",
            'payment_proof': "Unggah Bukti Pembayaran (jika perlu)",
        }
        
        help_texts = {
            'phone_number': "Contoh: 081234567890",
            'payment_proof': "Upload file gambar (JPG, PNG). Kosongkan jika event gratis.",
        }

