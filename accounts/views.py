from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserProfileForm
from django.apps import apps

EventRegistration = apps.get_model('events', 'EventRegistration')
Question = apps.get_model('forum', 'Question')
Answer = apps.get_model('forum', 'Answer')

@login_required
def account_dashboard(request):
    # Get user's registrations
    registrations = EventRegistration.objects.filter(user=request.user).select_related('event')

    # Get statistics
    total_registrations = registrations.count()
    completed_events = registrations.filter(event__status='completed').count()
    upcoming_events = registrations.filter(event__status='upcoming').count()

    context = {
        'registrations': registrations,
        'total_registrations': total_registrations,
        'completed_events': completed_events,
        'upcoming_events': upcoming_events,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def profile(request):
    user_profile = request.user.userprofile

    context = {
        'user_profile': user_profile,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    user_profile = request.user.userprofile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user_profile)

    context = {
        'form': form,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def my_registrations(request):
    registrations = EventRegistration.objects.filter(user=request.user).select_related('event').order_by('-registration_date')

    context = {
        'registrations': registrations,
    }
    return render(request, 'accounts/my_registrations.html', context)

@login_required
def forum_activity(request):
    # Get user's questions and answers
    questions = Question.objects.filter(user=request.user).select_related('event')
    answers = Answer.objects.filter(user=request.user).select_related('question__event')

    context = {
        'questions': questions,
        'answers': answers,
    }
    return render(request, 'accounts/forum_activity.html', context)
