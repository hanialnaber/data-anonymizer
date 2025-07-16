"""Configuration management for data anonymizer."""

import os
from pathlib import Path
from typing import Any, Dict, List


class Config:
    """Configuration class for data anonymizer."""

    # Application settings
    APP_NAME: str = "Data Anonymizer"
    APP_VERSION: str = "0.1.0"

    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # Streamlit settings
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))

    # Privacy settings
    DEFAULT_K_ANONYMITY: int = int(os.getenv("DEFAULT_K_ANONYMITY", "5"))
    DEFAULT_EPSILON: float = float(os.getenv("DEFAULT_EPSILON", "1.0"))

    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
    CONFIG_DIR: Path = PROJECT_ROOT / "config"
    SAMPLES_DIR: Path = PROJECT_ROOT / "samples"

    # File settings
    ALLOWED_EXTENSIONS: Dict[str, list] = {"csv": [".csv"], "excel": [".xlsx", ".xls"]}

    # CORS settings
    CORS_ORIGINS: list = ["*"]

    @classmethod
    def get_samples_dir(cls) -> str:
        """Get the samples directory path."""
        cls.SAMPLES_DIR.mkdir(exist_ok=True)
        return str(cls.SAMPLES_DIR)

    @classmethod
    def get_config_file(cls, filename: str) -> Path:
        """Get path to a config file."""
        return cls.CONFIG_DIR / filename
