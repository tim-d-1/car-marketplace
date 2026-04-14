from django.db import models
from django.contrib.auth.models import User

from django.db.models.signals import post_save
from django.dispatch import receiver

class Car(models.Model):
    CONDITION_CHOICES = [
        ('new', 'Нові'),
        ('used', 'Вживані'),
    ]
    TRANSMISSION_CHOICES = [
        ('manual', 'Ручна / Механіка'),
        ('automatic', 'Автомат'),
        ('robot', 'Робот'),
        ('variator', 'Варіатор'),
    ]
    FUEL_CHOICES = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
        ('electric', 'Електро'),
        ('hybrid', 'Гібрид'),
        ('gas', 'Газ / Бензин'),
    ]

    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    price = models.IntegerField()  # USD
    description = models.TextField()
    image = models.URLField(blank=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used')
    region = models.CharField(max_length=100, default='Київ')
    
    mileage = models.IntegerField(default=0)
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='manual')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='petrol')
    engine_volume = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model}"

    @property
    def price_uah(self):
        return self.price * 41  # Approximate rate

    @property
    def mileage_info(self):
        if self.condition == 'new' or self.mileage == 0:
            return "Без пробігу"
        return f"{self.mileage} тис. км"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'car') # Prevents duplicate wishlist items

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"Профіль {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()