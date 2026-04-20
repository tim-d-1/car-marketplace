import os
import django
from django.urls import reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autoria.settings")
django.setup()

try:
    url = reverse("edit_auto", args=[1])
    print(f"URL: {url}")
except Exception as e:
    print(f"Error: {e}")
