from pydantic import model_validator
from pydantic_settings import BaseSettings

DEFAULT_MODEL_NAME = "gpt-5.6-terra"


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    KG_GENERATION_MODEL: str = ""
    MODEL_NAME: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @model_validator(mode="after")
    def resolve_generation_model(self):
        """Keep the canonical generation setting and legacy fallback aligned."""
        self.MODEL_NAME = (
            str(self.KG_GENERATION_MODEL or "").strip()
            or str(self.MODEL_NAME or "").strip()
            or DEFAULT_MODEL_NAME
        )
        return self


settings = Settings()
