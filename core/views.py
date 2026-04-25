import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .supabase_client import upload_image, supabase
from .utils import create_notification

from core.forms import CarForm, UserProfileForm, UserRegistrationForm, AdminUserEditForm
from .models import (
    Car,
    Profile,
    Wishlist,
    VehicleMake,
    VehicleModel,
    Region,
    VehicleType,
    Purchase,
)


def handle_image_upload(request, field_name, bucket, folder):
    image_file = request.FILES.get(field_name)
    if image_file:
        return upload_image(image_file, bucket=bucket, folder=folder)
    return None


@login_required
def profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.phone = form.cleaned_data.get("phone")
            profile.wallet_address = form.cleaned_data.get("wallet_address")

            avatar_url = handle_image_upload(
                request, field_name="avatar", bucket="avatars", folder=f"user_{user.id}"
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

        return render(request, "core/profile.html", {"form": form, "is_admin": True if request.user.is_staff else False })


def auth_callback_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            access_token = data.get("access_token")

            user_response = supabase.auth.get_user(access_token)
            if not user_response or not user_response.user:
                return JsonResponse(
                    {"status": "error", "message": "Invalid token"}, status=401
                )

            email = user_response.user.email
            full_name = user_response.user.user_metadata.get("full_name", "")

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
    cars = (
        Car.objects.all()
        .select_related("brand", "model", "region", "model__vehicle_type")
        .filter_by_params(request.GET)
    )

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

    brand_id = request.GET.get("brand")
    type_id = request.GET.get("type")

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
        "query_condition": request.GET.get("condition"),
        "query_type": request.GET.get("type"),
        "query_brand": request.GET.get("brand"),
        "query_model": request.GET.get("model"),
        "query_region": request.GET.get("region"),
        "query_price_from": request.GET.get("price_from"),
        "query_price_to": request.GET.get("price_to"),
        "query_year_from": request.GET.get("year_from"),
        "query_year_to": request.GET.get("year_to"),
        "query_fuel_type": request.GET.get("fuel_type"),
        "query_transmission": request.GET.get("transmission"),
        "query_mileage_to": request.GET.get("mileage_to"),
        "query_sort": request.GET.get("sort", "-created_at"),
        "wishlist_car_ids": wishlist_car_ids,
        "FUEL_CHOICES": Car.FUEL_CHOICES,
        "TRANSMISSION_CHOICES": Car.TRANSMISSION_CHOICES,
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

            currency = form.cleaned_data.get("currency")
            if currency == "UAH":
                from .utils import get_usd_uah_rate

                rate = get_usd_uah_rate()
                car.price = int(car.price / rate)

            image_url = handle_image_upload(request, "image", "cars", "listings")
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
def edit_auto(request, car_id):
    if request.user.is_staff:
        car = get_object_or_404(Car, id=car_id)
    else:
        car = get_object_or_404(Car, id=car_id, owner=request.user)

    if car.status in ["pending", "sold"] and not request.user.is_staff:
        messages.error(
            request,
            "Ви не можете редагувати оголошення, яке знаходиться в процесі продажу або вже продано.",
        )
        return redirect("my_ads")
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            car = form.save(commit=False)

            currency = form.cleaned_data.get("currency")
            if currency == "UAH":
                from .utils import get_usd_uah_rate

                rate = get_usd_uah_rate()
                car.price = int(car.price / rate)

            image_url = handle_image_upload(
                request, field_name="image", bucket="cars", folder="listings"
            )
            if image_url:
                car.image = image_url

            new_phone = form.cleaned_data.get("phone")
            if new_phone:
                profile = request.user.profile
                profile.phone = new_phone
                profile.save()

            car.save()
            messages.success(request, "Оголошення успішно оновлено!")
            return redirect("my_ads")
    else:
        initial = {"phone": request.user.profile.phone}
        form = CarForm(instance=car, initial=initial)

    return render(request, "core/edit_auto.html", {"form": form, "car": car})


@login_required
def delete_auto(request, car_id):
    if request.user.is_staff:
        car = get_object_or_404(Car, id=car_id)
    else:
        car = get_object_or_404(Car, id=car_id, owner=request.user)

    if car.status in ["pending", "sold"] and not request.user.is_staff:
        messages.error(
            request,
            "Ви не можете видалити оголошення, яке знаходиться в процесі продажу або вже продано.",
        )
        return redirect("my_ads")
    if request.method == "POST":
        car.delete()
        messages.success(request, "Оголошення успішно видалено!")
        return redirect(request.META.get("HTTP_REFERER", "home"))
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def my_ads(request):
    if request.user.is_staff:
        query = request.GET.get("q", "")
        sort = request.GET.get("sort", "-created_at")

        purchases = Purchase.objects.all().select_related(
            "car", "car__brand", "car__model", "buyer", "seller", "buyer__profile"
        )

        if query:
            from django.db.models import Q

            purchases = purchases.filter(
                Q(buyer__username__icontains=query)
                | Q(buyer__email__icontains=query)
                | Q(buyer__profile__phone__icontains=query)
                | Q(deal_id__icontains=query)
                | Q(transaction_hash__icontains=query)
            )

        if sort == "price_asc":
            purchases = purchases.order_by("car__price")
        elif sort == "price_desc":
            purchases = purchases.order_by("-car__price")
        elif sort == "created_at":
            purchases = purchases.order_by("created_at")
        else:
            purchases = purchases.order_by("-created_at")

        return render(
            request,
            "core/my_ads.html",
            {"purchases": purchases, "is_admin": True, "query": query, "sort": sort},
        )

    tab = request.GET.get("tab", "active")
    cars = Car.objects.filter(owner=request.user).select_related(
        "brand", "model", "region"
    )

    if tab == "active":
        cars = cars.filter(status="active")
    elif tab == "inactive":
        cars = cars.filter(status="inactive")
    elif tab == "pending":
        cars = cars.filter(status="pending")
        for car in cars:
            car.current_purchase = Purchase.objects.filter(
                car=car, status="pending"
            ).first()
    elif tab == "sold":
        cars = cars.filter(status="sold")

    return render(request, "core/my_ads.html", {"cars": cars, "active_tab": tab})


@login_required
def toggle_car_status(request, car_id):
    if request.user.is_staff:
        car = get_object_or_404(Car, id=car_id)
    else:
        car = get_object_or_404(Car, id=car_id, owner=request.user)

    if car.status == "active":
        car.status = "inactive"
        messages.success(request, "Оголошення деактивовано.")
        create_notification(
            user=car.owner,
            text=f"Ваше оголошення {car.brand.make_name} {car.model.model_name} було деактивовано.",
            link="/profile/my-ads/?tab=inactive",
        )
    elif car.status == "inactive":
        car.status = "active"
        messages.success(request, "Оголошення активовано.")
        create_notification(
            user=car.owner,
            text=f"Ваше оголошення {car.brand.make_name} {car.model.model_name} тепер знову активне!",
            link="/profile/my-ads/?tab=active",
        )
    else:
        messages.error(request, "Неможливо змінити статус оголошення в даному стані.")
    car.save()
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def checkout_view(request, car_id):
    if request.user.is_staff:
        messages.error(request, "Адміністратори не можуть купувати авто.")
        return redirect("car_detail", car_id=car_id)

    car = get_object_or_404(Car, id=car_id)
    if car.status != "active":
        messages.error(request, "Це авто зараз недоступне для купівлі.")
        return redirect("car_detail", car_id=car.id)

    if car.owner == request.user:
        messages.warning(request, "Ви не можете купити власне авто.")
        return redirect("car_detail", car_id=car.id)

    eth_usd_rate = cache.get("eth_usd_rate")
    if not eth_usd_rate:
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
                timeout=5,
            )
            data = response.json()
            eth_usd_rate = data["ethereum"]["usd"]
            cache.set("eth_usd_rate", eth_usd_rate, 300)
        except Exception:
            eth_usd_rate = 3200.0

    eth_price = car.price / eth_usd_rate
    context = {
        "car": car,
        "eth_price_str": "{:.6f}".format(eth_price),
        "eth_price": round(eth_price, 6),
        "seller_wallet": car.owner.profile.wallet_address if car.owner else None,
    }
    return render(request, "core/checkout.html", context)


@csrf_exempt
@login_required
def payment_success_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        car_id = data.get("car_id")
        tx_hash = data.get("tx_hash")
        amount_eth = data.get("amount_eth")
        deal_id = data.get("deal_id")

        car = get_object_or_404(Car, id=car_id)
        car.status = "pending"
        car.save()

        purchase = Purchase.objects.create(
            car=car,
            buyer=request.user,
            seller=car.owner,
            amount_eth=amount_eth,
            transaction_hash=tx_hash,
            deal_id=deal_id,
            status="pending",
        )

        create_notification(
            user=car.owner,
            text=f"Ваше авто {car.brand.make_name} {car.model.model_name} було куплено! Очікуйте на підтвердження отримання від покупця.",
            link="/profile/my-ads/?tab=pending",
        )

        return JsonResponse({"status": "success", "purchase_id": purchase.id})
    return JsonResponse({"status": "error"}, status=400)


@csrf_exempt
@login_required
def confirm_delivery_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        purchase_id = data.get("purchase_id")

        purchase = get_object_or_404(Purchase, id=purchase_id, buyer=request.user)
        purchase.status = "completed"
        purchase.save()

        if purchase.car:
            purchase.car.status = "sold"
            purchase.car.save()

        create_notification(
            user=purchase.seller,
            text=f"Покупець {purchase.buyer.username} підтвердив отримання авто {purchase.car}. Кошти вивільнено!",
            link="/profile/my-ads/?tab=sold",
        )

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)


@csrf_exempt
@login_required
def cancel_order_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        purchase_id = data.get("purchase_id")

        purchase = get_object_or_404(Purchase, id=purchase_id)

        if request.user != purchase.buyer and request.user != purchase.seller:
            return JsonResponse(
                {"status": "error", "message": "Unauthorized"}, status=403
            )

        purchase.status = "cancelled"
        purchase.save()

        if purchase.car:
            purchase.car.status = "active"
            purchase.car.save()

        # Notify the other party
        if request.user == purchase.buyer:
            create_notification(
                user=purchase.seller,
                text=f"Покупець скасував замовлення на авто {purchase.car}.",
                link="/profile/my-ads/",
            )
        elif request.user == purchase.seller:
            create_notification(
                user=purchase.buyer,
                text=f"Продавець скасував ваше замовлення на авто {purchase.car}.",
                link="/profile/purchases/",
            )

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)


@login_required
def purchase_history(request):
    if request.user.is_staff:
        messages.error(request, "У вас немає доступу до цієї сторінки.")
        return redirect("home")

    purchases = request.user.purchases.all().select_related(
        "car", "car__brand", "car__model", "seller"
    )
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
    owner_ads_count = 0
    if car.owner:
        owner_ads_count = car.owner.cars.count()

    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, car=car).exists()
    return render(
        request,
        "core/car_detail.html",
        {
            "car": car,
            "in_wishlist": in_wishlist,
            "owner_ads_count": owner_ads_count,
        },
    )


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related(
        "car", "car__brand", "car__model"
    )
    return render(request, "core/wishlist.html", {"wishlist_items": wishlist_items})


@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    return render(
        request, "core/notifications.html", {"notifications": notifications}
    )


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification, id=notification_id, user=request.user
    )
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect("notifications")


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


@login_required
def admin_users_list(request):
    if not request.user.is_staff:
        messages.error(request, "У вас немає доступу до цієї сторінки.")
        return redirect("home")

    query = request.GET.get("q", "")
    users = User.objects.all().select_related("profile").order_by("-date_joined")

    if query:
        from django.db.models import Q

        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(profile__phone__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )

    return render(
        request, "core/admin_users_list.html", {"users": users, "query": query}
    )


@login_required
def admin_user_detail(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "У вас немає доступу до цієї сторінки.")
        return redirect("home")

    managed_user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = AdminUserEditForm(
            request.POST,
            request.FILES,
            instance=managed_user,
            is_superuser=request.user.is_superuser,
        )
        if form.is_valid():
            user = form.save(commit=False)

            new_pwd = form.cleaned_data.get("new_password")
            if new_pwd:
                user.set_password(new_pwd)

            user.save()

            profile = user.profile
            profile.phone = form.cleaned_data.get("phone")
            profile.wallet_address = form.cleaned_data.get("wallet_address")

            avatar_url = handle_image_upload(
                request, field_name="avatar", bucket="avatars", folder=f"user_{user.id}"
            )
            if avatar_url:
                profile.avatar = avatar_url

            profile.save()

            messages.success(request, f"Профіль користувача {user.username} оновлено!")
            return redirect("admin_user_detail", user_id=user.id)
    else:
        initial = {
            "phone": managed_user.profile.phone,
            "wallet_address": managed_user.profile.wallet_address,
        }
        form = AdminUserEditForm(
            instance=managed_user,
            initial=initial,
            is_superuser=request.user.is_superuser,
        )

    purchases = managed_user.purchases.all().select_related("car", "seller")
    sales = managed_user.sales.all().select_related("car", "buyer")

    return render(
        request,
        "core/admin_user_detail.html",
        {
            "managed_user": managed_user,
            "form": form,
            "purchases": purchases,
            "sales": sales,
        },
    )
