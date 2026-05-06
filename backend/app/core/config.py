from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List
import os


class Settings(BaseSettings):
    APP_NAME: str = "SchoolSaaS"
    APP_ENV: str = "development"
    SECRET_KEY: str
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    JWT_PRIVATE_KEY_PATH: str = "./keys/private.pem"
    JWT_PUBLIC_KEY_PATH: str = "./keys/public.pem"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email
    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@schoolsaas.com"

    # Cloudflare R2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "school-saas-files"
    R2_PUBLIC_URL: str = ""

    # YouTube
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""

    # Cloudflare Stream
    CF_STREAM_TOKEN: str = ""
    CF_ACCOUNT_ID: str = ""
    CF_STREAM_SIGNING_KEY: str = ""
    CF_STREAM_SIGNING_SECRET: str = ""

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # Encryption
    FERNET_KEY: str = ""

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
