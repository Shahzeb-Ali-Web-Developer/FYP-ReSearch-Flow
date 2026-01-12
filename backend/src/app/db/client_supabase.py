from supabase import create_client, Client
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Get Supabase client (creates if needed)"""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase credentials not configured. Database features will be disabled.")
        return None
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Singleton instance (lazy initialization)
_supabase_client = None

def get_supabase():
    """Get or create Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client

# For backward compatibility
supabase = get_supabase()