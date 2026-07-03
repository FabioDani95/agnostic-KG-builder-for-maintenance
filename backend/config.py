from pydantic_settings import BaseSettings

DEFAULT_MODEL_NAME = "gpt-5.4"


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    MODEL_NAME: str = DEFAULT_MODEL_NAME

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
