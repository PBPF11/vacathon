from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.account_dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('registrations/', views.my_registrations, name='my_registrations'),
    path('forum-activity/', views.forum_activity, name='forum_activity'),
]