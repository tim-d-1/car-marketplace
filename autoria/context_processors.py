import os
from django.conf import settings

def supabase_config(request):
    notifications_count = 0
    if request.user.is_authenticated:
        notifications_count = request.user.notifications.filter(is_read=False).count()

    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
        "ESCROW_CONTRACT_ADDRESS": settings.ESCROW_CONTRACT_ADDRESS,
        "unread_notifications_count": notifications_count,
    }
