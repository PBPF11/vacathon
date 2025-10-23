from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib import messages
from .models import Question, Answer
from events.models import MarathonEvent
import json

@login_required
def show_main(request):
    # Get all questions across all events
    questions = Question.objects.select_related('event', 'user__userprofile').order_by('-created_at')

    context = {
        'questions': questions,
    }
    return render(request, 'forum/forum_main.html', context)

@login_required
def choose_event(request):
    events = MarathonEvent.objects.filter(status__in=['upcoming', 'ongoing'])
    context = {
        'events': events,
    }
    return render(request, 'forum/choose_event.html', context)

@csrf_exempt
def add_question(request):
    if request.method == "POST":
        data = json.loads(request.body)
        title = data.get("title")
        question_text = data.get("question")
        event_id = data.get("event_id")
        user = request.user

        try:
            event = MarathonEvent.objects.get(pk=event_id)
            new_question = Question(
                user=user,
                event=event,
                title=title,
                question=question_text
            )
            new_question.save()

            return JsonResponse({
                "status": True,
                "message": "Question added successfully!"
            }, status=201)
        except MarathonEvent.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Event not found."
            }, status=404)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

    return JsonResponse({
        "status": False,
        "message": "Invalid method."
    }, status=405)

@csrf_exempt
def add_answer(request):
    if request.method == "POST":
        data = json.loads(request.body)
        answer_text = data.get("answer")
        question_id = data.get("question_id")
        user = request.user

        try:
            question = Question.objects.get(pk=question_id)
            new_answer = Answer(
                user=user,
                question=question,
                answer=answer_text
            )
            new_answer.save()

            question.answered = True
            question.save()

            return JsonResponse({
                "status": True,
                "message": "Answer added successfully!"
            }, status=201)
        except Question.DoesNotExist:
            return JsonResponse({
                "status": False,
                "message": "Question not found."
            }, status=404)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

    return JsonResponse({
        "status": False,
        "message": "Invalid method."
    }, status=405)

def get_questions(request):
    questions = Question.objects.select_related('event', 'user__userprofile').order_by('-created_at')
    data = []

    for question in questions:
        each_data = {
            "id": question.pk,
            "title": question.title,
            "question": question.question,
            "full_name": question.user.userprofile.full_name,
            "event_name": question.event.name,
            "event_location": question.event.location,
            "answered": question.answered,
            "created_at": question.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "pinned": question.pinned,
        }
        if question.answered:
            answer = question.answer
            each_data["answer"] = answer.answer
            each_data["user_answer"] = answer.user.userprofile.full_name
            each_data["answer_created_at"] = answer.created_at.strftime("%Y-%m-%d %H:%M:%S")
        data.append(each_data)

    return JsonResponse(data, safe=False)

def get_questions_by_event(request, event_id):
    try:
        event = MarathonEvent.objects.get(pk=event_id)
        questions = Question.objects.filter(event=event).select_related('user__userprofile').order_by('-created_at')
        data = []

        for question in questions:
            each_data = {
                "id": question.pk,
                "title": question.title,
                "question": question.question,
                "full_name": question.user.userprofile.full_name,
                "answered": question.answered,
                "created_at": question.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "pinned": question.pinned,
            }
            if question.answered:
                answer = question.answer
                each_data["answer"] = answer.answer
                each_data["user_answer"] = answer.user.userprofile.full_name
                each_data["answer_created_at"] = answer.created_at.strftime("%Y-%m-%d %H:%M:%S")
            data.append(each_data)

        return JsonResponse(data, safe=False)
    except MarathonEvent.DoesNotExist:
        return JsonResponse({
            "status": False,
            "message": "Event not found."
        }, status=404)
