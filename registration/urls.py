from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('<int:event_id>/', views.registration_form, name='registration_form'),
    path('<int:registration_id>/upload-payment/', views.upload_payment_proof, name='upload_payment_proof'),
    path('<int:registration_id>/status/', views.registration_status, name='registration_status'),
]