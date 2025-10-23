from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.show_main, name='show_main'),
    path('choose-event/', views.choose_event, name='choose_event'),
    path('add-question/', views.add_question, name='add_question'),
    path('add-answer/', views.add_answer, name='add_answer'),
    path('get-questions/', views.get_questions, name='get_questions'),
    path('get-questions/<int:event_id>/', views.get_questions_by_event, name='get_questions_by_event'),
]
