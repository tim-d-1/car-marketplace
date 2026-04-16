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

    brand = models.ForeignKey(VehicleMake, on_delete=models.PROTECT)
    model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cars", null=True, blank=True)
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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand.make_name} {self.model.model_name}"

    @property
    def price_uah(self):
        return self.price * 41  # Approximate rate

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
        ("pending", "В очікуванні"),
        ("completed", "Завершено"),
        ("failed", "Помилка"),
    ]

    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sales")
    amount_eth = models.DecimalField(max_digits=20, decimal_places=10)
    transaction_hash = models.CharField(max_length=66, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Купівля {self.car} від {self.buyer.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
