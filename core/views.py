from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from .models import Car

def home(request):
    cars = Car.objects.all()
    return render(request, 'core/index.html', {'cars': cars})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
        messages.error(request, "Невірне ім'я користувача або пароль.")
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        messages.error(request, "Помилка при реєстрації. Будь ласка, перевірте дані.")
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    return render(request, 'core/car_detail.html', {'car': car})