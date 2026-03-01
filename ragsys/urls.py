from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("create/", views.create_note),
    path("notes/", views.get_notes),
    path("test/", views.test),
]
