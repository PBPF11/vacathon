from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import MarathonEvent, EventRegistration
from django.apps import apps

Question = apps.get_model('forum', 'Question')

def event_list(request):
    events = MarathonEvent.objects.all()
    search_query = request.GET.get('search', '')
    distance_filter = request.GET.get('distance', '')
    location_filter = request.GET.get('location', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'event_date')

    # Search functionality
    if search_query:
        events = events.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    # Filters
    if distance_filter:
        events = events.filter(distance=distance_filter)
    if location_filter:
        events = events.filter(location__icontains=location_filter)
    if status_filter:
        events = events.filter(status=status_filter)

    # Sorting
    if sort_by == 'popularity':
        events = events.annotate(participant_count=Count('eventregistration')).order_by('-participant_count')
    elif sort_by == 'date':
        events = events.order_by('event_date')
    else:
        events = events.order_by('event_date')

    # Pagination
    paginator = Paginator(events, 12)  # 12 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'events': page_obj,
        'search_query': search_query,
        'distance_filter': distance_filter,
        'location_filter': location_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
    }
    return render(request, 'events/event_list.html', context)

def event_detail(request, event_id):
    event = get_object_or_404(MarathonEvent, pk=event_id)
    is_registered = False
    registration = None

    if request.user.is_authenticated:
        try:
            registration = EventRegistration.objects.get(user=request.user, event=event)
            is_registered = True
        except EventRegistration.DoesNotExist:
            pass

    context = {
        'event': event,
        'is_registered': is_registered,
        'registration': registration,
    }
    return render(request, 'events/event_detail.html', context)

@login_required
def register_for_event(request, event_id):
    event = get_object_or_404(MarathonEvent, pk=event_id)

    if not event.is_registration_open:
        messages.error(request, 'Registration for this event is closed.')
        return redirect('events:event_detail', event_id=event_id)

    # Check if user is already registered
    if EventRegistration.objects.filter(user=request.user, event=event).exists():
        messages.info(request, 'You are already registered for this event.')
        return redirect('events:event_detail', event_id=event_id)

    # Create registration
    registration = EventRegistration.objects.create(
        user=request.user,
        event=event,
        payment_status='pending' if event.registration_fee > 0 else 'paid'
    )

    # Update participant count
    event.current_participants += 1
    event.save()

    messages.success(request, f'Successfully registered for {event.name}!')
    return redirect('registration:registration_form', event_id=event_id)

@login_required
def event_forum(request, event_id):
    event = get_object_or_404(MarathonEvent, pk=event_id)
    questions = Question.objects.filter(event=event).order_by('-created_at')

    context = {
        'event': event,
        'questions': questions,
    }
    return render(request, 'events/event_forum.html', context)
