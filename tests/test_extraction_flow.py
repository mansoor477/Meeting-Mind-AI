"""
Unit tests for Meeting Mind AI full extraction flow.
Verifies the trace: who said what -> who owns task -> deadline -> priority -> decisions -> risks.
"""

import pytest
from meeting_mind.preprocessor import Preprocessor
from meeting_mind.engine import MeetingMindEngine
from meeting_mind.models import MeetingIntelligenceOutput, PriorityEnum
from app.azure_engine import AzureOpenAIEngine
from app.config import Config
from app.schemas import MeetingResult


SAMPLE_TRANSCRIPT = """
[00:00:15] Speaker 1: Hi everyone, welcome to today's architecture sync. I'm Rahul, Backend Lead.
[00:00:25] Speaker 2: Hey Rahul! Priya here from Product. Let's finalize the tickets for Sprint 4.
[00:00:40] Speaker 3: Hey folks, Alex from DevOps here.
[00:01:05] Speaker 1: We decided to use Redis for session caching instead of Memcached. I'll own this choice.
[00:02:45] Speaker 2: Rahul (Backend Lead) will implement the Payment Intent API endpoints by Thursday.
[00:04:00] Speaker 3: On my side, Alex, I will setup the Redis Sentinel Cluster Infrastructure by Wednesday.
[00:05:15] Speaker 3: High severity risk: database schema migration script lock time on main user table. Mitigation: run non-blocking gh-ost online migration.
"""


def test_meeting_mind_engine_extraction_flow():
    preprocessor = Preprocessor()
    pre_res = preprocessor.process(SAMPLE_TRANSCRIPT)
    cleaned = pre_res["cleaned_transcript"]

    engine = MeetingMindEngine(force_mock=True)
    output = engine.process_transcript(cleaned)

    assert isinstance(output, MeetingIntelligenceOutput)
    assert len(output.action_items) > 0

    # Verify task assignment vs speaker attribution vs deadline vs priority
    first_task = output.action_items[0]
    assert first_task.assignee != ""
    assert first_task.target_timeline != ""
    assert first_task.priority in [PriorityEnum.HIGH, PriorityEnum.MEDIUM, PriorityEnum.LOW]

    # Verify decision extraction
    assert len(output.decisions) > 0
    dec = output.decisions[0]
    assert dec.topic != ""
    assert dec.decision != ""

    # Verify risk extraction
    assert len(output.risks) > 0
    risk = output.risks[0]
    assert risk.risk_description != ""
    assert risk.severity in [PriorityEnum.HIGH, PriorityEnum.MEDIUM, PriorityEnum.LOW]


def test_azure_engine_fallback_flow():
    config = Config(
        azure_openai_api_key="mock",
        azure_openai_endpoint="https://your-resource-name.openai.azure.com/",
        azure_openai_deployment_name="gpt-4o"
    )
    engine = AzureOpenAIEngine(config)
    result = engine.extract(SAMPLE_TRANSCRIPT)

    assert isinstance(result, MeetingResult)
    assert len(result.action_items) > 0
    assert len(result.decisions) > 0
    assert len(result.risks) > 0
