from django import forms
from events.models import EventRegistration

class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ['payment_proof']
        widgets = {
            'payment_proof': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'payment_proof': 'Upload Payment Proof (if required)',
        }