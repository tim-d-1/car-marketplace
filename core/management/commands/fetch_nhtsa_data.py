import requests
from django.core.management.base import BaseCommand
from core.models import VehicleMake, VehicleModel
import time

class Command(BaseCommand):
    help = 'Fetches vehicle makes and models from NHTSA API'

    def handle(self, *args, **options):
        POPULAR_MAKES_LIST = [
            'Toyota', 'Honda', 'Ford', 'Chevrolet', 'Volkswagen', 
            'BMW', 'Mercedes-Benz', 'Audi', 'Nissan', 'Hyundai', 
            'Kia', 'Subaru', 'Mazda', 'Lexus', 'Volvo', 
            'Mitsubishi', 'Land Rover', 'Jaguar', 'Porsche', 'Tesla'
        ]
        
        self.stdout.write("Fetching all makes from NHTSA to find IDs...")
        try:
            response = requests.get('https://vpic.nhtsa.dot.gov/api/vehicles/GetAllMakes?format=json', timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch makes: {e}"))
            return
        
        all_makes_map = {make['Make_Name'].strip().upper(): make for make in data.get('Results', [])}
        
        for make_name in POPULAR_MAKES_LIST:
            make_data = all_makes_map.get(make_name.strip().upper())
            if not make_data:
                self.stdout.write(self.style.WARNING(f"Make {make_name} not found in NHTSA API master list"))
                continue
            
            make_obj, created = VehicleMake.objects.update_or_create(
                make_id=make_data['Make_ID'],
                defaults={'make_name': make_data['Make_Name'].strip()}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Make: {make_obj.make_name} (ID: {make_obj.make_id})"))
            else:
                self.stdout.write(f"Updated Make: {make_obj.make_name} (ID: {make_obj.make_id})")
            
            self.stdout.write(f"   Fetching modern passenger models for {make_obj.make_name}...")
            try:

                model_url = (
                    f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeIdYear/"
                    f"makeId/{make_obj.make_id}/modelyear/2017/vehicletype/car?format=json"
                )
                model_response = requests.get(model_url, timeout=30)
                model_response.raise_for_status()
                model_data = model_response.json()

                time.sleep(0.5)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to fetch models for {make_name}: {e}"))
                continue
            
            models_created = 0
            for m in model_data.get('Results', []):
                _, m_created = VehicleModel.objects.update_or_create(
                    model_id=m['Model_ID'],
                    defaults={
                        'make': make_obj,
                        'model_name': m['Model_Name'].strip()
                    }
                )
                if m_created:
                    models_created += 1
            
            self.stdout.write(self.style.SUCCESS(f"  Processed {len(model_data.get('Results', []))} models ({models_created} new)"))
        
        self.stdout.write(self.style.SUCCESS("Successfully populated vehicle makes and models"))
