import requests
from django.core.cache import cache


def get_usd_uah_rate():
    rate = cache.get("usd_uah_rate")
    if rate:
        return rate

    try:
        response = requests.get(
            "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5",
            timeout=5,
        )
        data = response.json()

        for item in data:
            if item["ccy"] == "USD" and item["base_ccy"] == "UAH":
                rate = float(item["sale"])
                cache.set("usd_uah_rate", rate, 3600)
                return rate
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")

    return 41.5
