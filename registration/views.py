from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import EventRegistrationForm
from django.apps import apps

MarathonEvent = apps.get_model('events', 'MarathonEvent')
EventRegistration = apps.get_model('events', 'EventRegistration')

@login_required
def registration_form(request, event_id):
    event = get_object_or_404(MarathonEvent, pk=event_id)

    # Check if user is already registered
    existing_registration = EventRegistration.objects.filter(user=request.user, event=event).first()
    if existing_registration:
        return redirect('registration:registration_status', registration_id=existing_registration.id)

    if request.method == 'POST':
        form = EventRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.user = request.user
            registration.event = event
            registration.save()

            # Update participant count
            event.current_participants += 1
            event.save()

            messages.success(request, f'Successfully registered for {event.name}!')
            return redirect('registration:registration_status', registration_id=registration.id)
    else:
        form = EventRegistrationForm()

    context = {
        'form': form,
        'event': event,
    }
    return render(request, 'registration/registration_form.html', context)

@login_required
def upload_payment_proof(request, registration_id):
    registration = get_object_or_404(EventRegistration, pk=registration_id, user=request.user)

    if request.method == 'POST' and request.FILES.get('payment_proof'):
        registration.payment_proof = request.FILES['payment_proof']
        registration.save()
        messages.success(request, 'Payment proof uploaded successfully!')
        return redirect('registration:registration_status', registration_id=registration.id)

    context = {
        'registration': registration,
    }
    return render(request, 'registration/upload_payment.html', context)

@login_required
def registration_status(request, registration_id):
    registration = get_object_or_404(EventRegistration, pk=registration_id, user=request.user)

    context = {
        'registration': registration,
    }
    return render(request, 'registration/registration_status.html', context)
