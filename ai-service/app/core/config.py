from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str

    # PostgreSQL
    database_url: str
    postgres_db: str = "jikimi"
    postgres_user: str = "jikimi"
    postgres_password: str = "jikimi1234"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Clova OCR (Phase 2~)
    clova_ocr_api_key: str = ""
    clova_ocr_api_url: str = ""

    # AWS S3 (Phase 3~)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = "jikimi-contracts"
    aws_region: str = "ap-northeast-2"

    model_config = SettingsConfigDict(
        env_file="../.env",      # 로컬: 루트 .env 참조
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
