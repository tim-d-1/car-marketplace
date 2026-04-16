from django import forms
from .models import Car, VehicleMake, VehicleModel, VehicleType, Region


class CarForm(forms.ModelForm):
    vehicle_type = forms.ModelChoiceField(
        queryset=VehicleType.objects.all().order_by("name"),
        label="Тип транспорту",
        empty_label="Обрати",
        widget=forms.Select(
            attrs={
                "class": "ria-select",
                "id": "type-select",
                "onchange": 'updateFilters("type")',
            }
        ),
    )

    brand = forms.ModelChoiceField(
        queryset=VehicleMake.objects.all().order_by("make_name"),
        label="Марка",
        empty_label="Обрати",
        widget=forms.Select(
            attrs={
                "class": "ria-select",
                "id": "brand-select",
                "onchange": 'updateFilters("brand")',
            }
        ),
    )

    model = forms.ModelChoiceField(
        queryset=VehicleModel.objects.none(),
        label="Модель",
        empty_label="Обрати",
        widget=forms.Select(attrs={"class": "ria-select", "id": "model-select"}),
    )

    region = forms.ModelChoiceField(
        queryset=Region.objects.all().order_by("name"),
        label="Регіон",
        empty_label="Обрати",
        widget=forms.Select(attrs={"class": "ria-select"}),
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
                "class": "ria-select",
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
            "year": forms.NumberInput(
                attrs={
                    "class": "ria-select",
                    "min": 1900,
                    "max": 2100,
                }
            ),
            "price": forms.NumberInput(attrs={"class": "ria-select"}),
            "description": forms.Textarea(
                attrs={
                    "class": "ria-select",
                    "rows": 4,
                }
            ),
            "mileage": forms.NumberInput(attrs={"class": "ria-select"}),
            "transmission": forms.Select(attrs={"class": "ria-select"}),
            "fuel_type": forms.Select(attrs={"class": "ria-select"}),
            "engine_volume": forms.NumberInput(
                attrs={
                    "class": "ria-select",
                    "step": "0.1",
                }
            ),
            "condition": forms.Select(attrs={"class": "ria-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["transmission"].choices = [("", "Обрати")] + list(
            self.fields["transmission"].choices
        )
        self.fields["fuel_type"].choices = [("", "Обрати")] + list(
            self.fields["fuel_type"].choices
        )
        self.fields["condition"].choices = [("", "Обрати")] + list(
            self.fields["condition"].choices
        )

        if not self.instance.pk:
            self.initial["transmission"] = ""
            self.initial["fuel_type"] = ""
            self.initial["condition"] = ""

        if "brand" in self.data:
            try:
                brand_id = int(self.data.get("brand"))
                self.fields["model"].queryset = VehicleModel.objects.filter(
                    make_id=brand_id
                ).order_by("model_name")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields["model"].queryset = self.instance.brand.models.order_by(
                "model_name"
            )
