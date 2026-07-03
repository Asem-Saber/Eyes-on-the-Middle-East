from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Chronos Intelligence API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Constructed from POSTGRES_* vars in .env; fallback for local dev
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/aljazeera_articles"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
