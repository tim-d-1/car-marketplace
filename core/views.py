import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from .models import Car

def auth_callback_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            user, created = User.objects.get_or_create(username=email, email=email)
            if created:
                user.set_unusable_password()
                user.save()
            
            login(request, user)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    # On GET, we show the "waiting" template
    return render(request, 'core/auth_callback.html')

def home(request):
    cars = Car.objects.all()

    condition = request.GET.get('condition')
    brand = request.GET.get('brand')
    model = request.GET.get('model')
    region = request.GET.get('region')

    if condition and condition != 'all':
        cars = cars.filter(condition=condition)
    if brand and brand != 'all':
        cars = cars.filter(brand=brand)
    if model and model != 'all':
        cars = cars.filter(model=model)
    if region and region != 'all':
        cars = cars.filter(region=region)

    brands = Car.objects.values_list('brand', flat=True).distinct().order_by('brand')
    models = Car.objects.values_list('model', flat=True).distinct().order_by('model')
    regions = Car.objects.values_list('region', flat=True).distinct().order_by('region')

    context = {
        'cars': cars,
        'brands': brands,
        'models': models,
        'regions': regions,
        # Preserve search queries
        'query_condition': condition,
        'query_brand': brand,
        'query_model': model,
        'query_region': region,
    }
    return render(request, 'core/index.html', context)

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
