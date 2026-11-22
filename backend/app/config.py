"""Central configuration. Values come from environment variables / backend/.env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NutriAgent"
    app_tagline: str = "AI-powered personalized nutrition & meal planning"
    currency_symbol: str = "$"

    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 720
    algorithm: str = "HS256"

    database_url: str = "sqlite:///./nutriagent.db"

    admin_email: str = "admin@nutriagent.dev"
    admin_password: str = "Admin@123"
    demo_email: str = "demo@nutriagent.dev"
    demo_password: str = "Demo@123"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    tax_rate: float = 0.08
    shipping_flat: float = 4.99
    free_shipping_over: float = 50.0

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
