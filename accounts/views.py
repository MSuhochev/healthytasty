from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse

from .forms import RegistrationForm, CustomAuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/accounts/login/')
        else:
            # Отображаем сообщения об ошибках в форме
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistrationForm()

    context = {
        'title': 'Регистрация',
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                print("User authenticated successfully")
                return redirect('index')
        else:
            print("Form is not valid:", form.errors)
    else:
        form = CustomAuthenticationForm()
    context = {
        'title': 'Авторизация',
        'form': form,
    }
    return render(request, 'accounts/login.html', context)


def user_logout(request):
    logout(request)
    return redirect('index')
