"""
Unit tests for Meeting Mind AI Pydantic Schemas.
"""

import pytest
from pydantic import ValidationError

from meeting_mind.models import (
    MeetingIntelligenceOutput,
    ExecutiveSummary,
    ActionItem,
    ArchitectureDecision,
    ProjectRisk,
    PriorityEnum,
    EffortEnum
)


def test_action_item_model():
    item = ActionItem(
        task_id="ACTION-001",
        title="Implement JWT Refresh Token Rotation",
        assignee="Rahul (Backend Lead)",
        who_said="Rahul (Backend Lead)",
        context_snippet="Implement rotation for security",
        priority=PriorityEnum.HIGH,
        effort=EffortEnum.MODERATE,
        target_timeline="End of Sprint 4",
        acceptance_criteria=["Tokens expire in 7 days", "Add unit test suite"]
    )
    assert item.task_id == "ACTION-001"
    assert item.priority == PriorityEnum.HIGH
    assert len(item.acceptance_criteria) == 2


def test_invalid_priority_enum():
    with pytest.raises(ValidationError):
        ActionItem(
            task_id="ACTION-001",
            title="Invalid Task",
            assignee="Unknown",
            who_said="Unknown",
            context_snippet="Invalid",
            priority="CriticalAlert",  # Invalid enum value
            # type: ignore[arg-type]
            effort=EffortEnum.SIMPLE,
            target_timeline="Tomorrow"
        )


def test_meeting_intelligence_container():
    output = MeetingIntelligenceOutput(
        meeting_title="Architecture Review Sync",
        date="2026-08-10",
        summary=ExecutiveSummary(
            title="Architecture Review Sync",
            overview="Discussion on Redis and auth tokens.",
            key_takeaways=["Adopt Redis"],
            participants=["Rahul (Backend Lead)"]
        ),
        action_items=[],
        decisions=[],
        risks=[]
    )

    dumped = output.model_dump()
    assert dumped["meeting_title"] == "Architecture Review Sync"
    assert dumped["summary"]["participants"] == ["Rahul (Backend Lead)"]
