from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    
    smtp_host: str
    smtp_port: str
    smtp_user: str
    smtp_pass: str
    smtp_from: str
    
    class Config:
        env_file = ".env"

settings = Settings()