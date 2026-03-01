from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("create/", views.create_note, name="create_note"),
    path("", views.get_notes, name="notes"),  # ← remove 'notes/' prefix
    path("test/", views.test, name="test"),
    path("<int:note_id>/delete/", views.delete_note, name="delete_note"),
    path("edit/<int:note_id>/", views.edit_note, name="edit_note"),
    path("ai/chat/", views.get_response, name="ask"),
]
