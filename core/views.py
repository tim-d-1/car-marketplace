import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

from core.forms import CarForm, UserProfileForm, UserRegistrationForm
from .supabase_client import upload_image
from .models import (
    Car,
    Profile,
    Wishlist,
    VehicleMake,
    VehicleModel,
    Region,
    VehicleType,
)


@login_required
def profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.phone = form.cleaned_data.get("phone")
            profile.wallet_address = form.cleaned_data.get("wallet_address")

            avatar_file = request.FILES.get("avatar")
            if avatar_file:
                avatar_url = upload_image(
                    avatar_file, bucket="avatars", folder=f"user_{user.id}"
                )
                if avatar_url:
                    profile.avatar = avatar_url

            profile.save()
            messages.success(request, "Ваш профіль успішно оновлено!")
            return redirect("profile")
    else:
        initial_data = {
            "phone": request.user.profile.phone,
            "wallet_address": request.user.profile.wallet_address,
        }
        form = UserProfileForm(instance=request.user, initial=initial_data)

    return render(request, "core/profile.html", {"form": form})


def auth_callback_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            full_name = data.get("full_name", "")

            user, created = User.objects.get_or_create(username=email, email=email)

            if created:
                user.set_unusable_password()
            if full_name:
                name_parts = full_name.split(" ", 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
            else:
                user.first_name = email.split("@")[0].capitalize()

            user.save()
            login(request, user)
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return render(request, "core/auth_callback.html")


def home(request):
    cars = Car.objects.all().select_related(
        "brand", "model", "region", "model__vehicle_type"
    )
    condition = request.GET.get("condition")
    type_id = request.GET.get("type")
    brand_id = request.GET.get("brand")
    model_id = request.GET.get("model")
    region_id = request.GET.get("region")

    if condition and condition != "all":
        cars = cars.filter(condition=condition)
    if type_id and type_id != "all":
        cars = cars.filter(model__vehicle_type_id=type_id)
    if brand_id and brand_id != "all":
        cars = cars.filter(brand_id=brand_id)
    if model_id and model_id != "all":
        cars = cars.filter(model_id=model_id)
    if region_id and region_id != "all":
        cars = cars.filter(region_id=region_id)

    types = cache.get("vehicle_types")
    if not types:
        types = list(VehicleType.objects.all().order_by("name"))
        cache.set("vehicle_types", types, 3600)

    brands = cache.get("vehicle_brands")
    if not brands:
        brands = list(VehicleMake.objects.all().order_by("make_name"))
        cache.set("vehicle_brands", brands, 3600)

    regions = cache.get("ukraine_regions")
    if not regions:
        regions = list(Region.objects.all().order_by("name"))
        cache.set("ukraine_regions", regions, 3600)

    models = VehicleModel.objects.none()
    if brand_id and brand_id != "all":
        models = VehicleModel.objects.filter(make_id=brand_id)
        if type_id and type_id != "all":
            models = models.filter(vehicle_type_id=type_id)
        models = models.order_by("model_name")

    wishlist_car_ids = []
    if request.user.is_authenticated:
        wishlist_car_ids = list(
            Wishlist.objects.filter(user=request.user).values_list("car_id", flat=True)
        )

    context = {
        "cars": cars,
        "types": types,
        "brands": brands,
        "models": models,
        "regions": regions,
        "query_condition": condition,
        "query_type": type_id,
        "query_brand": brand_id,
        "query_model": model_id,
        "query_region": region_id,
        "wishlist_car_ids": wishlist_car_ids,
    }
    return render(request, "core/index.html", context)


def get_filter_options(request):
    type_id = request.GET.get("type_id")
    make_id = request.GET.get("make_id")

    response_data = {}

    if type_id:
        if type_id == "all":
            makes = VehicleMake.objects.all()
        else:
            make_ids = (
                VehicleModel.objects.filter(vehicle_type_id=type_id)
                .values_list("make_id", flat=True)
                .distinct()
            )
            makes = VehicleMake.objects.filter(make_id__in=make_ids)
        response_data["makes"] = list(
            makes.order_by("make_name").values("make_id", "make_name")
        )

    if make_id:
        if make_id == "all":
            types = VehicleType.objects.all()
        else:
            type_ids = (
                VehicleModel.objects.filter(make_id=make_id)
                .values_list("vehicle_type_id", flat=True)
                .distinct()
            )
            types = VehicleType.objects.filter(id__in=type_ids)
        response_data["types"] = list(types.order_by("name").values("id", "name"))

    if make_id and make_id != "all":
        models_qs = VehicleModel.objects.filter(make_id=make_id)
        if type_id and type_id != "all":
            models_qs = models_qs.filter(vehicle_type_id=type_id)
        response_data["models"] = list(
            models_qs.order_by("model_name").values(
                "model_id", "model_name", "vehicle_type_id"
            )
        )

    return JsonResponse(response_data)


@login_required
def add_auto(request):
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)

            image_file = request.FILES.get("image")
            if image_file:
                image_url = upload_image(image_file, bucket="cars", folder="listings")
                if image_url:
                    car.image = image_url

            new_phone = form.cleaned_data.get("phone")
            if request.user.is_authenticated:
                car.owner = request.user
                if new_phone and not request.user.profile.phone:
                    profile = request.user.profile
                    profile.phone = new_phone
                    profile.save()

            car.save()
            messages.success(request, "Оголошення успішно додано!")
            return redirect("home")
    else:
        initial = {}
        if request.user.is_authenticated and request.user.profile.phone:
            initial["phone"] = request.user.profile.phone
        form = CarForm(initial=initial)

    return render(request, "core/add_auto.html", {"form": form})


@login_required
def my_ads(request):
    cars = Car.objects.filter(owner=request.user).select_related(
        "brand", "model", "region"
    )
    return render(request, "core/my_ads.html", {"cars": cars})


@login_required
def checkout_view(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if car.owner == request.user:
        messages.warning(request, "Ви не можете купити власне авто.")
        return redirect("car_detail", car_id=car.id)

    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
            timeout=5,
        )
        data = response.json()
        eth_usd_rate = data["ethereum"]["usd"]
    except Exception as e:
        print(f"Error fetching ETH price: {e}")
        eth_usd_rate = 3200.0

    eth_price = car.price / eth_usd_rate
    context = {
        "car": car,
        "eth_price_str": "{:.6f}".format(eth_price),
        "eth_price": round(eth_price, 6),
        "seller_wallet": car.owner.profile.wallet_address if car.owner else None,
    }
    return render(request, "core/checkout.html", context)


@login_required
def payment_success_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        car_id = data.get("car_id")
        tx_hash = data.get("tx_hash")
        amount_eth = data.get("amount_eth")

        car = get_object_or_404(Car, id=car_id)
        from .models import Purchase

        purchase = Purchase.objects.create(
            car=car,
            buyer=request.user,
            seller=car.owner,
            amount_eth=amount_eth,
            transaction_hash=tx_hash,
            status="completed",  # In a real app, we'd verify on-chain
        )
        return JsonResponse({"status": "success", "purchase_id": purchase.id})
    return JsonResponse({"status": "error"}, status=400)


@login_required
def purchase_history(request):
    purchases = request.user.purchases.all().select_related("car", "car__brand", "car__model", "seller")
    return render(request, "core/purchase_history.html", {"purchases": purchases})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
        messages.error(request, "Невірне ім'я користувача або пароль.")
    else:
        form = AuthenticationForm()
    return render(request, "core/login.html", {"form": form})


def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        messages.error(request, "Помилка при реєстрації. Будь ласка, перевірте дані.")
    else:
        form = UserRegistrationForm()
    return render(request, "core/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("home")


def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, car=car).exists()
    return render(
        request, "core/car_detail.html", {"car": car, "in_wishlist": in_wishlist}
    )


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related(
        "car", "car__brand", "car__model"
    )
    return render(request, "core/wishlist.html", {"wishlist_items": wishlist_items})


@login_required
def toggle_wishlist(request, car_id):
    if request.method == "POST":
        car = get_object_or_404(Car, id=car_id)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user, car=car
        )
        if not created:
            wishlist_item.delete()
            return JsonResponse({"status": "removed"})
        return JsonResponse({"status": "added"})
    return JsonResponse({"status": "error"}, status=400)
