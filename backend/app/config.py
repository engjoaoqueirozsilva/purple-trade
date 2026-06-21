import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "development"
    freqtrade_url: str = "http://freqtrade:8080"
    freqtrade_user: str = "freqtrader"
    freqtrade_password: str = "password"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
