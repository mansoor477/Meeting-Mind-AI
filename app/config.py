"""
Configuration loader for Meeting Mind AI.
Loads environment variables from .env for Azure OpenAI API configuration.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_deployment_name: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    def validate(self) -> None:
        """Ensure required Azure OpenAI configuration is present."""
        missing = []
        if not self.azure_openai_api_key:
            missing.append("AZURE_OPENAI_API_KEY")
        if not self.azure_openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if missing:
            raise ValueError(f"Missing required environment variables in .env: {', '.join(missing)}")


def get_config() -> Config:
    return Config()
