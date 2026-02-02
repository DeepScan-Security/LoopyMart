import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_yaml_config() -> dict[str, Any]:
    """Load configuration from config.local.yml if it exists."""
    config_path = Path(__file__).parent.parent.parent / "config.local.yml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def get_yaml_value(yaml_config: dict, *keys: str, default: Any = None) -> Any:
    """Get a nested value from YAML config."""
    value = yaml_config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value if value is not None else default


# Load YAML config once at module load
_yaml_config = load_yaml_config()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All values can be overridden via .env file or environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(
        default_factory=lambda: get_yaml_value(_yaml_config, "app", "name", default=os.getenv("APP_NAME", "Flipkart Clone API"))
    )
    debug: bool = Field(
        default_factory=lambda: get_yaml_value(_yaml_config, "app", "debug", default=os.getenv("DEBUG", "false").lower() == "true")
    )

    # SQL Database (PostgreSQL for users only)
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    # Falls back to SQLite for development if not set
    database_url: str = Field(
        default_factory=lambda: get_yaml_value(
            _yaml_config, "database", "url",
            default=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
        )
    )

    # MongoDB (for products, categories, cart, orders)
    mongodb_url: str = Field(
        default_factory=lambda: get_yaml_value(
            _yaml_config, "mongodb", "url",
            default=os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        )
    )
    mongodb_db_name: str = Field(
        default_factory=lambda: get_yaml_value(
            _yaml_config, "mongodb", "db_name",
            default=os.getenv("MONGODB_DB_NAME", "flipkart_clone")
        )
    )

    # JWT Authentication
    # IMPORTANT: Change this in production!
    secret_key: str = Field(
        default_factory=lambda: get_yaml_value(
            _yaml_config, "app", "secret_key",
            default=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        )
    )
    algorithm: str = Field(
        default_factory=lambda: get_yaml_value(
            _yaml_config, "app", "algorithm",
            default=os.getenv("ALGORITHM", "HS256")
        )
    )
    access_token_expire_minutes: int = Field(
        default_factory=lambda: int(get_yaml_value(
            _yaml_config, "app", "access_token_expire_minutes",
            default=os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")  # 7 days
        ))
    )

    # Razorpay (optional): set for payment gateway
    razorpay_key_id: str = Field(
        default_factory=lambda: get_yaml_value(
            _yaml_config, "razorpay", "key_id",
            default=os.getenv("RAZORPAY_KEY_ID", "")
        )
    )
    razorpay_key_secret: str = Field(
        default_factory=lambda: get_yaml_value(
            _yaml_config, "razorpay", "key_secret",
            default=os.getenv("RAZORPAY_KEY_SECRET", "")
        )
    )

    # CORS settings
    cors_origins: str = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )

    # Static files directory (relative to backend folder)
    static_dir: str = Field(
        default_factory=lambda: os.getenv("STATIC_DIR", "static")
    )
    uploads_dir: str = Field(
        default_factory=lambda: os.getenv("UPLOADS_DIR", "static/uploads")
    )

    # Admin seed credentials (for initial setup only)
    admin_email: str = Field(
        default_factory=lambda: os.getenv("ADMIN_EMAIL", "")
    )
    admin_password: str = Field(
        default_factory=lambda: os.getenv("ADMIN_PASSWORD", "")
    )
    admin_name: str = Field(
        default_factory=lambda: os.getenv("ADMIN_NAME", "Admin")
    )

    # API settings
    api_products_default_limit: int = Field(
        default_factory=lambda: int(os.getenv("API_PRODUCTS_DEFAULT_LIMIT", "50"))
    )
    api_products_max_limit: int = Field(
        default_factory=lambda: int(os.getenv("API_PRODUCTS_MAX_LIMIT", "100"))
    )

    # Payment settings
    min_payment_amount_paise: int = Field(
        default_factory=lambda: int(os.getenv("MIN_PAYMENT_AMOUNT_PAISE", "100"))
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_required(self) -> None:
        """Validate settings and warn about insecure defaults."""
        import warnings
        
        # Warn about development defaults in production
        if not self.debug:
            if "sqlite" in self.database_url.lower():
                warnings.warn(
                    "Using SQLite database in production is not recommended. "
                    "Set DATABASE_URL to a PostgreSQL connection string.",
                    UserWarning
                )
            if self.secret_key == "dev-secret-key-change-in-production":
                warnings.warn(
                    "Using default SECRET_KEY is insecure. "
                    "Set SECRET_KEY to a strong random value in production.",
                    UserWarning
                )


settings = Settings()
