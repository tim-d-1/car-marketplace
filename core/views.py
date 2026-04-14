from django.shortcuts import render, get_object_or_404
from .models import Car

def home(request):
    cars = Car.objects.all()
    return render(request, 'core/index.html', {'cars': cars})

# def car_detail(request, car_id):
#     car = get_object_or_404(Car, id=car_id)
#     return render(request, 'core/car_detail.html', {'car': car})