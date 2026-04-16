from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Car, Wishlist, VehicleMake, VehicleModel, Region


class CarBaseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.make = VehicleMake.objects.create(make_id=1, make_name="Toyota")
        self.model = VehicleModel.objects.create(
            model_id=1, make=self.make, model_name="Camry"
        )
        self.region = Region.objects.create(region_id=1, name="Kyiv", code="KV")

        self.car1 = Car.objects.create(
            brand=self.make,
            model=self.model,
            year=2020,
            price=15000,
            description="Good condition",
            condition="used",
            owner=self.user,
            region=self.region,
        )

        self.make2 = VehicleMake.objects.create(make_id=2, make_name="Honda")
        self.model2 = VehicleModel.objects.create(
            model_id=2, make=self.make2, model_name="Civic"
        )
        self.car2 = Car.objects.create(
            brand=self.make2,
            model=self.model2,
            year=2021,
            price=18000,
            description="Great condition",
            condition="used",
            region=self.region,
        )


class WishlistTests(CarBaseTests):
    def test_toggle_wishlist_add(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(reverse("toggle_wishlist", args=[self.car1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "added")
        self.assertTrue(Wishlist.objects.filter(user=self.user, car=self.car1).exists())

    def test_toggle_wishlist_remove(self):
        Wishlist.objects.create(user=self.user, car=self.car1)
        self.client.login(username="testuser", password="testpassword")
        response = self.client.post(reverse("toggle_wishlist", args=[self.car1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "removed")
        self.assertFalse(
            Wishlist.objects.filter(user=self.user, car=self.car1).exists()
        )

    def test_toggle_wishlist_unauthenticated(self):
        response = self.client.post(reverse("toggle_wishlist", args=[self.car1.id]))
        self.assertEqual(response.status_code, 302)

    def test_wishlist_view(self):
        Wishlist.objects.create(user=self.user, car=self.car1)
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("wishlist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Toyota Camry 2020")

    def test_home_view_wishlist_context(self):
        Wishlist.objects.create(user=self.user, car=self.car1)
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("wishlist_car_ids", response.context)
        self.assertIn(self.car1.id, response.context["wishlist_car_ids"])
        self.assertNotIn(self.car2.id, response.context["wishlist_car_ids"])

    def test_car_detail_view_wishlist_context(self):
        Wishlist.objects.create(user=self.user, car=self.car1)
        self.client.login(username="testuser", password="testpassword")

        response1 = self.client.get(reverse("car_detail", args=[self.car1.id]))
        self.assertTrue(response1.context["in_wishlist"])

        response2 = self.client.get(reverse("car_detail", args=[self.car2.id]))
        self.assertFalse(response2.context["in_wishlist"])


class MyAdsTests(CarBaseTests):
    def test_my_ads_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("my_ads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Toyota Camry 2020")
        self.assertNotContains(response, "Honda Civic 2021")

    def test_my_ads_unauthenticated(self):
        response = self.client.get(reverse("my_ads"))
        self.assertEqual(response.status_code, 302)
