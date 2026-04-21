import os
from django.conf import settings

def supabase_config(request):
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
        "ESCROW_CONTRACT_ADDRESS": settings.ESCROW_CONTRACT_ADDRESS,
    }
