import os
from dotenv import load_dotenv
from redis import Redis
from pathlib import Path

load_dotenv()

class Settings:
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASS: str = os.getenv("DB_PASS", "admin")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "monitoring_jalan")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    #set session
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    JABAR_SESSION_EXPIRE_DAYS: int = int(os.getenv("JABAR_SESSION_EXPIRE_DAYS", "30"))
    SESSION_INACTIVITY_HOURS: int = int(os.getenv("SESSION_INACTIVITY_HOURS", "1"))

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    SESSION_EXPIRE_MINUTES: int = int(os.getenv("SESSION_EXPIRE_MINUTES", "60"))
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("RESET_PASSWORD_TOKEN_EXPIRE_MINUTES", "60"))

    PASSWORD_RESET_TOKEN_EXP_HOURS: int = int(os.getenv("PASSWORD_RESET_TOKEN_EXP_HOURS", "1"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")

    # REDIS Settings
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6390")
    REDIS = Redis(
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            decode_responses=True
        )

    # SMTP Resend Configuration
    MAIL_MAILER: str = os.getenv("MAIL_MAILER", "smtp")
    MAIL_HOST: str = os.getenv("MAIL_HOST", "smtp.resend.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "465"))
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "resend")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")  # API Key Resend
    MAIL_FROM_ADDRESS: str = os.getenv("MAIL_FROM_ADDRESS", "info@ekosistemdata.dev")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "Monitoring Jalan")
    

    ADMIN_NOTIFICATION_EMAIL: str = os.getenv("ADMIN_NOTIFICATION_EMAIL", "ekosistemdatajabar@digitalservice.id")


    # Integrasi
    BASE_URL_ADUAN: str = os.getenv("BASE_URL_ADUAN", "http://localhost:3000")
    BASE_URL_TJ: str = os.getenv("BASE_URL_TJ", "https://tj.temanjabar.net/api/komf")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # CORS Settings
    CORS_ORIGINS: list = ["*"]

    #raster
    BASE_RASTER_DIR = Path(__file__).parent.parent / "app" / "data" / "tif"

    @staticmethod
    def get_tj_endpoint(endpoint: str) -> str:

        base_url = os.getenv("BASE_URL_TJ", "https://tj.temanjabar.net/api/komf")

        base_url = base_url.rstrip('/')

        endpoint = endpoint.lstrip('/')
        return f"{base_url}/{endpoint}"

settings = Settings()
