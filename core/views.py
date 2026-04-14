import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Car, Profile

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Ім'я")
    last_name = forms.CharField(max_length=30, required=False, label="Прізвище (необов'язково)")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

class UserProfileForm(forms.ModelForm):
    phone = forms.CharField(max_length=20, label="Номер телефону", required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        labels = {
            'first_name': "Ім'я",
            'last_name': "Прізвище",
            'username': "Ім'я користувача (ID)",
            'email': "Електронна пошта",
        }

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.phone = form.cleaned_data.get('phone')
            profile.save()
            messages.success(request, "Ваш профіль успішно оновлено!")
            return redirect('profile')
    else:
        initial_data = {'phone': request.user.profile.phone}
        form = UserProfileForm(instance=request.user, initial=initial_data)
    
    return render(request, 'core/profile.html', {'form': form})

def auth_callback_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            full_name = data.get('full_name', '') # Get name from JS
            
            user, created = User.objects.get_or_create(username=email, email=email)
            
            if created:
                user.set_unusable_password()
            if full_name:
                name_parts = full_name.split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
            else:
                user.first_name = email.split('@')[0].capitalize()
                
            user.save()
            login(request, user)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

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
        'cars': cars, 'brands': brands, 'models': models, 'regions': regions,
        'query_condition': condition, 'query_brand': brand, 'query_model': model, 'query_region': region,
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
        form = UserRegistrationForm(request.POST) # Use custom form
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        messages.error(request, "Помилка при реєстрації. Будь ласка, перевірте дані.")
    else:
        form = UserRegistrationForm() # Use custom form
    return render(request, 'core/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    return render(request, 'core/car_detail.html', {'car': car})
