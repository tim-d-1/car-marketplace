from django.db import models
from django.contrib.auth.models import User

from django.db.models.signals import post_save
from django.dispatch import receiver


class VehicleMake(models.Model):
    make_id = models.IntegerField(primary_key=True)
    make_name = models.CharField(max_length=255)

    def __str__(self):
        return self.make_name


class VehicleType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class VehicleModel(models.Model):
    model_id = models.IntegerField(primary_key=True)
    make = models.ForeignKey(
        VehicleMake, on_delete=models.CASCADE, related_name="models"
    )
    model_name = models.CharField(max_length=255)
    vehicle_type = models.ForeignKey(
        VehicleType, on_delete=models.SET_NULL, null=True, related_name="models"
    )

    def __str__(self):
        return self.model_name


class Region(models.Model):
    region_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class CarQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status="active")

    def filter_by_params(self, params):
        qs = self.active()
        condition = params.get("condition")
        type_id = params.get("type")
        brand_id = params.get("brand")
        model_id = params.get("model")
        region_id = params.get("region")
        price_from = params.get("price_from")
        price_to = params.get("price_to")
        year_from = params.get("year_from")
        year_to = params.get("year_to")
        fuel_type = params.get("fuel_type")
        transmission = params.get("transmission")
        mileage_to = params.get("mileage_to")
        sort_by = params.get("sort", "-created_at")

        if condition and condition != "all":
            qs = qs.filter(condition=condition)
        if type_id and type_id != "all":
            qs = qs.filter(model__vehicle_type_id=type_id)
        if brand_id and brand_id != "all":
            qs = qs.filter(brand_id=brand_id)
        if model_id and model_id != "all":
            qs = qs.filter(model_id=model_id)
        if region_id and region_id != "all":
            qs = qs.filter(region_id=region_id)

        if price_from:
            qs = qs.filter(price__gte=price_from)
        if price_to:
            qs = qs.filter(price__lte=price_to)
        if year_from:
            qs = qs.filter(year__gte=year_from)
        if year_to:
            qs = qs.filter(year__lte=year_to)
        if fuel_type and fuel_type != "all":
            qs = qs.filter(fuel_type=fuel_type)
        if transmission and transmission != "all":
            qs = qs.filter(transmission=transmission)
        if mileage_to:
            qs = qs.filter(mileage__lte=mileage_to)

        if sort_by == "price_asc":
            qs = qs.order_by("price")
        elif sort_by == "price_desc":
            qs = qs.order_by("-price")
        elif sort_by == "year_desc":
            qs = qs.order_by("-year")
        elif sort_by == "created_at":
            qs = qs.order_by("created_at")
        else:
            qs = qs.order_by("-created_at")

        return qs


class Car(models.Model):
    CONDITION_CHOICES = [
        ("new", "Нові"),
        ("used", "Вживані"),
    ]
    TRANSMISSION_CHOICES = [
        ("manual", "Ручна / Механіка"),
        ("automatic", "Автомат"),
        ("CVT", "Варіатор"),  # Continuously Variable
        ("DCT", "Робот"),  # Dual-Clutch
    ]
    FUEL_CHOICES = [
        ("petrol", "Бензин"),
        ("diesel", "Дизель"),
        ("electric", "Електро"),
        ("hybrid", "Гібрид"),
        ("gas", "Газ"),
    ]

    objects = CarQuerySet.as_manager()

    brand = models.ForeignKey(VehicleMake, on_delete=models.PROTECT)
    model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cars", null=True, blank=True
    )
    year = models.IntegerField()
    price = models.IntegerField()
    description = models.TextField()
    image = models.URLField(max_length=500, blank=True, null=True)
    condition = models.CharField(
        max_length=10, choices=CONDITION_CHOICES, default="used"
    )
    region = models.ForeignKey(Region, on_delete=models.PROTECT, null=True, blank=True)

    mileage = models.IntegerField(default=0)
    transmission = models.CharField(
        max_length=20, choices=TRANSMISSION_CHOICES, default="manual"
    )
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default="petrol")
    engine_volume = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Активне"),
            ("inactive", "Неактивне"),
            ("pending", "В очікуванні"),
            ("sold", "Продано"),
        ],
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand.make_name} {self.model.model_name}"

    @property
    def price_uah(self):
        from .utils import get_usd_uah_rate
        rate = get_usd_uah_rate()
        return int(self.price * rate)

    @property
    def mileage_info(self):
        if self.condition == "new" or self.mileage == 0:
            return "Без пробігу"
        return f"{self.mileage} тис. км"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "car")


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.URLField(max_length=500, blank=True, null=True)
    wallet_address = models.CharField(max_length=42, blank=True, null=True)

    def __str__(self):
        return f"Профіль {self.user.username}"


class Purchase(models.Model):
    STATUS_CHOICES = [
        ("pending", "В очікуванні (Сплачено)"),
        ("completed", "Завершено (Кошти вивільнено)"),
        ("failed", "Помилка"),
        ("cancelled", "Скасовано"),
    ]

    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sales")
    amount_eth = models.DecimalField(max_digits=20, decimal_places=10)
    transaction_hash = models.CharField(max_length=66, unique=True)
    deal_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Купівля {self.car} від {self.buyer.username}"


@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)
    instance.profile.save()
