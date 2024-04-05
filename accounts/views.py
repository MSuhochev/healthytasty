from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
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
        form = CustomAuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Вы успешно вошли в систему.")
            return redirect('index')
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
