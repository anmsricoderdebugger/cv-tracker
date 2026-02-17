from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://cvtracker:cvtracker_pass@localhost:5432/cvtracker"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "change-me-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"
    DEFAULT_SKILL_WEIGHT: float = 0.4
    DEFAULT_EXPERIENCE_WEIGHT: float = 0.3
    DEFAULT_PROJECT_WEIGHT: float = 0.2
    DEFAULT_KEYWORD_WEIGHT: float = 0.1
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
