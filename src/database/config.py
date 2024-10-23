from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"  # This will tell pydantic to load variables from .env
        extra = 'allow'  # Allow extra environment variables
settings = Settings()
