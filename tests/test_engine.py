"""
Unit tests for AzureOpenAIEngine in app/azure_engine.py.
"""

from app.azure_engine import AzureOpenAIEngine
from app.config import Config
from app.schemas import MeetingResult, PriorityEnum, ComplexityEnum


def test_azure_engine_fallback_extraction():
    config = Config(
        azure_openai_api_key="mock_key",
        azure_openai_endpoint="https://your-resource-name.openai.azure.com/",
        azure_openai_deployment_name="gpt-4o"
    )
    engine = AzureOpenAIEngine(config)

    transcript = "Rahul (Backend Lead): We should migrate session caching to Redis by end of Sprint 4."
    result = engine.extract(transcript)

    assert isinstance(result, MeetingResult)
    assert result.meeting_title != ""
    assert len(result.action_items) > 0
    assert result.action_items[0].priority in [PriorityEnum.HIGH, PriorityEnum.MEDIUM, PriorityEnum.LOW]
    assert result.action_items[0].complexity in [ComplexityEnum.SIMPLE, ComplexityEnum.MODERATE, ComplexityEnum.COMPLEX]
