"""Application configuration settings."""

import os
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "Casio Watches E-commerce"
    app_version: str = "1.0.0"
    app_description: str = "Premium Casio Watches Online Store"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Database settings
    database_url: str = "sqlite:///./data/casio_watches.db"
    
    # External services
    unsplash_access_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    
    # Email settings (for order notifications)
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-in-production":
            import secrets
            return secrets.token_urlsafe(32)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()