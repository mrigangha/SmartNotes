from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.shortcuts import render

from .models import Note

# Create your views here.


@login_required
def create_note(request):
    note = Note.objects.create(user=request.user, title="Hello", content="jawnd")
    return JsonResponse({"message": "created"})


@login_required
def get_notes(request):
    notes = Note.objects.filter(user=request.user)
    return JsonResponse({"notes": list(notes.values())})


def test(request):
    return render(request, "test.html", {"data": {"message": "Hello from JSON"}})
