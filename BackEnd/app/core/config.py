from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    后端服务全局配置，使用 pydantic-settings 支持环境变量注入。
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
    template_root_relative: Path = Field(default=Path("BackEnd/templates"))
    task_expiry_minutes: int = Field(default=60)
    dependency_commands: tuple[str, ...] = Field(
        default=(
            "pandoc",
            "libreoffice",
            "qpdf",
            "gs",
        )
    )
    command_timeout_seconds: int = Field(default=180)

    @computed_field
    @property
    def template_root(self) -> Path:
        """
        模板根目录，根据 `template_root_relative` 计算绝对路径。
        """

        if self.template_root_relative.is_absolute():
            return self.template_root_relative
        return (BASE_DIR / self.template_root_relative).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Settings 工厂函数，配合 lru_cache 保证全局单例。
    """

    return Settings()


settings = get_settings()

