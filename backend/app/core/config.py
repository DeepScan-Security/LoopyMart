from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Flipkart Clone API"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./app.db"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"


settings = Settings()
