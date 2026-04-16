import requests
from django.core.management.base import BaseCommand
from core.models import VehicleMake, VehicleModel, VehicleType
import time


class Command(BaseCommand):
    help = "Fetches vehicle makes, types and models from NHTSA API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--makes", action="store_true", help="Fetch/Update popular makes"
        )
        parser.add_argument(
            "--types",
            action="store_true",
            help="Fetch vehicle types for existing makes",
        )
        parser.add_argument("--models", action="store_true", help="Fetch models")
        parser.add_argument(
            "--year",
            type=int,
            help="Specific year for models (e.g. 2020)",
            default=None,
        )

    def handle(self, *args, **options):
        POPULAR_MAKES_LIST = [
            "Toyota",
            "Honda",
            "Ford",
            "Chevrolet",
            "Volkswagen",
            "BMW",
            "Mercedes-Benz",
            "Audi",
            "Nissan",
            "Hyundai",
            "Kia",
            "Subaru",
            "Mazda",
            "Lexus",
            "Volvo",
            "Mitsubishi",
            "Land Rover",
            "Jaguar",
            "Porsche",
            "Tesla",
            "Jeep",
            "Dodge",
            "Ram",
            "GMC",
            "Cadillac",
        ]

        if not any([options["makes"], options["types"], options["models"]]):
            self.stdout.write(
                self.style.WARNING(
                    "Please specify an argument: --makes, --types, or --models"
                )
            )
            return

        if options["makes"]:
            self.fetch_makes(POPULAR_MAKES_LIST)

        if options["types"]:
            self.fetch_types()

        if options["models"]:
            self.fetch_models(POPULAR_MAKES_LIST, options["year"])

    def fetch_makes(self, popular_list):
        self.stdout.write("Fetching all makes from NHTSA to find IDs...")
        try:
            response = requests.get(
                "https://vpic.nhtsa.dot.gov/api/vehicles/GetAllMakes?format=json",
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch makes: {e}"))
            return

        all_makes_map = {
            make["Make_Name"].strip().upper(): make for make in data.get("Results", [])
        }

        for make_name in popular_list:
            make_data = all_makes_map.get(make_name.strip().upper())
            if not make_data:
                self.stdout.write(
                    self.style.WARNING(
                        f"Make {make_name} not found in NHTSA API master list"
                    )
                )
                continue

            make_obj, created = VehicleMake.objects.update_or_create(
                make_id=make_data["Make_ID"],
                defaults={"make_name": make_data["Make_Name"].strip()},
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created Make: {make_obj.make_name}")
                )
            else:
                self.stdout.write(f"Updated Make: {make_obj.make_name}")

    def fetch_types(self):
        self.stdout.write("Fetching vehicle types for existing makes...")
        makes = VehicleMake.objects.all()
        for make in makes:
            self.stdout.write(f"  Fetching types for {make.make_name}...")
            try:
                url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetVehicleTypesForMakeId/{make.make_id}?format=json"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()

                for t in data.get("Results", []):
                    v_type, _ = VehicleType.objects.get_or_create(
                        name=t["VehicleTypeName"].strip()
                    )

                time.sleep(0.2)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    Error: {e}"))

    def fetch_models(self, popular_list, year=None):
        upper_popular_list = [m.upper() for m in popular_list]
        makes = VehicleMake.objects.filter(make_name__in=upper_popular_list)

        if not makes.exists():
            self.stdout.write(
                self.style.WARNING(
                    "No makes found matching the popular list. Try running --makes first."
                )
            )
            return

        for make_obj in makes:
            self.stdout.write(f"Fetching types for {make_obj.make_name}...")
            try:
                type_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetVehicleTypesForMakeId/{make_obj.make_id}?format=json"
                type_response = requests.get(type_url, timeout=30)
                type_response.raise_for_status()
                vehicle_types = type_response.json().get("Results", [])
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  Error fetching types for {make_obj.make_name}: {e}"
                    )
                )
                continue

            for vt in vehicle_types:
                type_name = vt.get("VehicleTypeName", "").strip()
                if not type_name:
                    continue

                v_type, _ = VehicleType.objects.get_or_create(name=type_name)

                self.stdout.write(
                    f"  Fetching {type_name} models for {make_obj.make_name}..."
                )

                if year:
                    model_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeIdYear/makeId/{make_obj.make_id}/modelyear/{year}/vehicletype/{type_name}?format=json"
                else:
                    model_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeIdYear/makeId/{make_obj.make_id}/vehicletype/{type_name}?format=json"

                try:
                    model_response = requests.get(model_url, timeout=30)
                    model_response.raise_for_status()
                    model_results = model_response.json().get("Results", [])

                    models_count = 0
                    for m in model_results:
                        _, m_created = VehicleModel.objects.update_or_create(
                            model_id=m["Model_ID"],
                            defaults={
                                "make": make_obj,
                                "model_name": m["Model_Name"].strip(),
                                "vehicle_type": v_type,
                            },
                        )
                        if m_created:
                            models_count += 1

                    if models_count > 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"    Processed {len(model_results)} models ({models_count} new)"
                            )
                        )
                    else:
                        self.stdout.write(
                            f"    Processed {len(model_results)} models (0 new)"
                        )

                    time.sleep(0.2)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"    Error fetching {type_name} models: {e}")
                    )

            time.sleep(0.5)
