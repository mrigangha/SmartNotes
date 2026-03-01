import json

from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse

# Create your views here.
from django.shortcuts import get_object_or_404, redirect, render

from .lservices import ask, invalidate_embedding
from .models import Note


@login_required
def delete_note(request, note_id):
    if request.method == "POST":
        note = get_object_or_404(Note, id=note_id, user=request.user)
        note.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if not title:
            data_json = {
                "error": "Title is required",
                "note": {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "created_at": note.created_at.isoformat(),
                },
            }

            return render(request, "edit_note.html", {"data": data_json})
        note.title = title
        note.content = content
        note.save()
        invalidate_embedding(note.id)
        return redirect("notes")

    data_json = {
        "error": "",
        "note": {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "created_at": note.created_at.isoformat(),
        },
    }
    return render(request, "edit_note.html", {"data": data_json})


@login_required
def create_note(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")

        # basic validation
        if not title:
            return render(request, "create_note.html", {"error": "Title is required"})

        note = Note.objects.create(user=request.user, title=title, content=content)

        return redirect("notes")

    return render(request, "create_note.html")


@login_required
def get_notes(request):
    notes = Note.objects.filter(user=request.user)
    return render(request, "list_note.html", {"data": {"notes": list(notes.values())}})


def test(request):
    return render(request, "test.html", {"data": {"message": "Hello from JSON"}})


@login_required
def get_response(request):
    print("get data")
    text = ask("What is django.", request.user, [])
    return JsonResponse({"message": text})
