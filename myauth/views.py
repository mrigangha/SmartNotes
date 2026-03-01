from django.http.response import JsonResponse
from django.shortcuts import redirect, render

from . import services

# Create your views here.


def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password != confirm_password:
            return render(request, "register.html", {"error": "Passwords do not match"})
        status = services.Register(username, email, password)
        if status == -1:
            return render(request, "register.html", {"error": "Username already exist"})
    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        status = services.Login(request, username, password)
        if status == 0:
            return redirect("/dashboard")
        else:
            return render(request, "login.html", {"error": "Invalid Credentials"})
    return render(request, "login.html")


def logout_view(request):
    services.Logout(request)
    return JsonResponse({"message": "SuccessFully logged in."})
