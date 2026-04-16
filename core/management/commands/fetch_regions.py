import os
import requests
from django.core.management.base import BaseCommand
from core.models import Region


class Command(BaseCommand):
    help = "Fetches Ukrainian states from countrystatecity.in API and populates Region model"

    def handle(self, *args, **options):
        api_key = os.getenv("COUNTRY_STATE_CITY_API")
        if not api_key:
            self.stdout.write(
                self.style.ERROR(
                    "COUNTRY_STATE_CITY_API not found in environment variables"
                )
            )
            return

        url = "https://api.countrystatecity.in/v1/countries/UA/states"
        headers = {"X-CSCAPI-KEY": api_key}

        self.stdout.write("Fetching states from API...")
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            states = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch states: {e}"))
            return

        self.stdout.write(f"Found {len(states)} states. Populating database...")

        for state in states:
            region, created = Region.objects.update_or_create(
                region_id=state["id"],
                defaults={"name": state["name"], "code": state["iso2"]},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created region: {region.name}"))
            else:
                self.stdout.write(f"Updated region: {region.name}")

        self.stdout.write(self.style.SUCCESS("Successfully populated Region model"))
