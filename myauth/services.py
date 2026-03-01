from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


def Login(request, username, password):
    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)  # Creates session
        return 0
    else:
        return -1


def Register(username, email, password):
    if User.objects.filter(username=username).exists():
        return -1
    User.objects.create_user(username=username, email=email, password=password)
    return 0


def Logout(request):
    logout(request)
    return redirect("login")
