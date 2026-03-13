from os import environ

from pydantic_settings import BaseSettings


class DefaultSettings(BaseSettings):
    PATH_PREFIX: str = environ.get("PATH_PREFIX", "")
    DATABASE_URL: str = environ.get("DATABASE_URL")
    YANDEX_API_KEY: str = environ.get("YANDEX_API_KEY")
    YANDEX_FOLDER_ID: str = environ.get("YANDEX_FOLDER_ID")
    CONFLUENCE_USER: str = environ.get("CONFLUENCE_USER")
    CONFLUENCE_PASSWORD: str = environ.get("CONFLUENCE_PASSWORD")



def get_settings() -> DefaultSettings:
    return DefaultSettings()


settings = get_settings()
