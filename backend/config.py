import os


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://3dshape:SecurePass2026@localhost:5432/3dshape"
    )


settings = Settings()
