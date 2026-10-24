from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("rooms:lobby")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to LexiSync, {user.username}!")
            return redirect("rooms:lobby")
    else:
        form = UserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("rooms:lobby")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("rooms:lobby")
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")
