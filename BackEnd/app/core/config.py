from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Global backend configuration using pydantic-settings for environment variable injection.
    """

    model_config = SettingsConfigDict(
        env_prefix="BACKEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="CirkidzDoc Backend")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    template_root_relative: Path = Field(default=Path("templates"))
    task_expiry_minutes: int = Field(default=60)
    database_url: str = Field(
        default=f"sqlite:///{(BASE_DIR / 'data' / 'backend.db').resolve()}",
    )
    database_echo: bool = Field(default=False)
    results_root_relative: Path = Field(default=Path("results"))
    dependency_commands: tuple[str, ...] = Field(
        default=(
            "pandoc",
            "libreoffice",
            "qpdf",
            "gs",
        )
    )
    command_timeout_seconds: int = Field(default=180)
    cors_allow_origins: tuple[str, ...] = Field(
        default=(
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        )
    )

    @computed_field
    @property
    def template_root(self) -> Path:
        """
        Absolute template root directory derived from `template_root_relative`.
        """

        if self.template_root_relative.is_absolute():
            return self.template_root_relative
        return (BASE_DIR / self.template_root_relative).resolve()

    @computed_field
    @property
    def results_root(self) -> Path:
        """
        Directory where rendered task results are stored.
        """

        root = self.results_root_relative
        if root.is_absolute():
            path = root
        else:
            path = (BASE_DIR / root).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Settings factory cached by lru_cache to guarantee a global singleton.
    """

    return Settings()


settings = get_settings()

