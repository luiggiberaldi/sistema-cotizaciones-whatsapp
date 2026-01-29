"""
Configuración de la aplicación usando Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Información de la aplicación
    app_name: str = "Sistema de Cotizaciones"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"
    
    # Configuración de Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str = ""
    supabase_jwt_secret: str
    supabase_bucket_name: str = "invoices"
    
    # Configuración de API
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: List[str] = ["*"]
    
    # Configuración de seguridad
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Configuración de WhatsApp Cloud API
    whatsapp_verify_token: str = "mi_token_secreto_verificacion"
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v18.0"
    whatsapp_api_url: str = "https://graph.facebook.com"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Instancia global de configuración
settings = Settings()
