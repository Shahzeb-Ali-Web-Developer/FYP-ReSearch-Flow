from supabase import create_client, Client
from ..core.config import settings

def get_supabase_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Create a singleton instance
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)