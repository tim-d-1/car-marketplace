import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django import forms
from .models import Car, Profile, Wishlist, VehicleMake, VehicleModel, Region

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
            full_name = data.get('full_name', '')
            
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
    cars = Car.objects.all().select_related('brand', 'model', 'region')
    condition = request.GET.get('condition')
    brand_id = request.GET.get('brand')
    model_id = request.GET.get('model')
    region_id = request.GET.get('region')

    if condition and condition != 'all':
        cars = cars.filter(condition=condition)
    if brand_id and brand_id != 'all':
        cars = cars.filter(brand_id=brand_id)
    if model_id and model_id != 'all':
        cars = cars.filter(model_id=model_id)
    if region_id and region_id != 'all':
        cars = cars.filter(region_id=region_id)

    # Caching filtering options
    brands = cache.get('vehicle_brands')
    if not brands:
        brands = list(VehicleMake.objects.all().order_by('make_name'))
        cache.set('vehicle_brands', brands, 3600) # Cache for 1 hour

    regions = cache.get('ukraine_regions')
    if not regions:
        regions = list(Region.objects.all().order_by('name'))
        cache.set('ukraine_regions', regions, 3600)

    models = VehicleModel.objects.none()
    if brand_id and brand_id != 'all':
        models = VehicleModel.objects.filter(make_id=brand_id).order_by('model_name')
        
    wishlist_car_ids = []
    if request.user.is_authenticated:
        wishlist_car_ids = list(Wishlist.objects.filter(user=request.user).values_list('car_id', flat=True))

    context = {
        'cars': cars, 
        'brands': brands, 
        'models': models, 
        'regions': regions,
        'query_condition': condition, 
        'query_brand': brand_id, 
        'query_model': model_id, 
        'query_region': region_id,
        'wishlist_car_ids': wishlist_car_ids,
    }
    return render(request, 'core/index.html', context)

def get_models(request):
    make_id = request.GET.get('make_id')
    if make_id and make_id != 'all':
        models = VehicleModel.objects.filter(make_id=make_id).order_by('model_name').values('model_id', 'model_name')
        return JsonResponse(list(models), safe=False)
    return JsonResponse([], safe=False)

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
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        messages.error(request, "Помилка при реєстрації. Будь ласка, перевірте дані.")
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, car=car).exists()
    return render(request, 'core/car_detail.html', {'car': car, 'in_wishlist': in_wishlist})

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('car', 'car__brand', 'car__model')
    return render(request, 'core/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def toggle_wishlist(request, car_id):
    if request.method == 'POST':
        car = get_object_or_404(Car, id=car_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, car=car)
        if not created:
            wishlist_item.delete()
            return JsonResponse({'status': 'removed'})
        return JsonResponse({'status': 'added'})
    return JsonResponse({'status': 'error'}, status=400)
