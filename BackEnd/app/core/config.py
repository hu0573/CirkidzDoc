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
    render_tmp_dir_relative: Path = Field(default=Path("../infra/tmp"))
    render_output_dir_relative: Path = Field(default=Path("../infra/output"))
    toolkit_compose_file: Path | None = Field(default=Path("../infra/docker-compose.yml"))
    toolkit_service_name: str = Field(default="toolkit")
    toolkit_tmp_dir: str = Field(default="/workspace/tmp")
    toolkit_output_dir: str = Field(default="/workspace/output")
    use_toolkit_container: bool = Field(default=True)
    toolkit_commands: tuple[str, ...] = Field(
        default=(
            "libreoffice",
            "pandoc",
            "qpdf",
            "gs",
        )
    )
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
            "http://141.148.141.184:9004",
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

    @computed_field
    @property
    def render_tmp_dir(self) -> Path:
        """
        Working directory shared with the rendering toolkit container.
        """

        return self._ensure_directory(self.render_tmp_dir_relative)

    @computed_field
    @property
    def render_output_dir(self) -> Path:
        """
        Output directory shared with the rendering toolkit container.
        """

        return self._ensure_directory(self.render_output_dir_relative)

    def _ensure_directory(self, raw: Path) -> Path:
        if raw.is_absolute():
            path = raw
        else:
            path = (BASE_DIR / raw).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Settings factory cached by lru_cache to guarantee a global singleton.
    """

    return Settings()


settings = get_settings()

