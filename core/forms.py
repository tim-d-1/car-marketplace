from django import forms
from .models import Car, VehicleMake, VehicleModel, VehicleType, Region


class CarForm(forms.ModelForm):
    vehicle_type = forms.ModelChoiceField(
        queryset=VehicleType.objects.all().order_by("name"),
        label="Тип транспорту",
        widget=forms.Select(
            attrs={
                "class": "ria-select",
                "id": "type-select",
                "onchange": 'updateFilters("type")',
            }
        ),
    )

    currency = forms.ChoiceField(
        choices=[("USD", "$"), ("EUR", "€"), ("UAH", "грн")],
        initial="USD",
        widget=forms.Select(attrs={"class": "ria-select w-24"}),
    )

    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Номер телефону",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-ria-red focus:border-ria-red",
                "placeholder": "+380...",
            }
        ),
    )

    class Meta:
        model = Car
        fields = [
            "brand",
            "model",
            "year",
            "price",
            "description",
            "image",
            "condition",
            "region",
            "mileage",
            "transmission",
            "fuel_type",
            "engine_volume",
        ]
        widgets = {
            "brand": forms.Select(
                attrs={
                    "class": "ria-select",
                    "id": "brand-select",
                    "onchange": 'updateFilters("brand")',
                }
            ),
            "model": forms.Select(attrs={"class": "ria-select", "id": "model-select"}),
            "region": forms.Select(attrs={"class": "ria-select"}),
            "year": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg border border-gray-300",
                    "min": 1900,
                    "max": 2100,
                }
            ),
            "price": forms.NumberInput(
                attrs={"class": "flex-1 px-4 py-3 rounded-lg border border-gray-300"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg border border-gray-300",
                    "rows": 4,
                }
            ),
            "mileage": forms.NumberInput(
                attrs={"class": "w-full px-4 py-3 rounded-lg border border-gray-300"}
            ),
            "transmission": forms.Select(attrs={"class": "ria-select"}),
            "fuel_type": forms.Select(attrs={"class": "ria-select"}),
            "engine_volume": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg border border-gray-300",
                    "step": "0.1",
                }
            ),
            "condition": forms.Select(attrs={"class": "ria-select"}),
        }
