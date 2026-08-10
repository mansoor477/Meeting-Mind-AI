"""
Unit tests for Pydantic schemas in app/schemas.py.
Tests validation of valid objects, invalid enum values, and missing required fields.
"""

import pytest
from pydantic import ValidationError
from app.schemas import (
    MeetingResult, ExecutiveSummary, ActionItem, Decision, Risk,
    PriorityEnum, ComplexityEnum
)


def test_valid_action_item():
    item = ActionItem(
        title="Deploy Redis operator",
        assignee="Amit",
        role="DevOps Lead",
        priority=PriorityEnum.HIGH,
        complexity=ComplexityEnum.MODERATE,
        timeline="Sprint 4",
        acceptance_criteria=["Operator installed", "Cluster configured"]
    )
    assert item.title == "Deploy Redis operator"
    assert item.priority == PriorityEnum.HIGH
    assert item.complexity == ComplexityEnum.MODERATE
    assert len(item.acceptance_criteria) == 2


def test_invalid_priority_enum():
    with pytest.raises(ValidationError) as excinfo:
        ActionItem(
            title="Task with bad priority",
            assignee="Rahul",
            priority="URGENT",  # Invalid priority
            complexity=ComplexityEnum.SIMPLE,
            timeline="Today"
        )
    assert "priority" in str(excinfo.value)


def test_invalid_complexity_enum():
    with pytest.raises(ValidationError) as excinfo:
        ActionItem(
            title="Task with bad complexity",
            assignee="Rahul",
            priority=PriorityEnum.LOW,
            complexity="VERY_HARD",  # Invalid complexity
            timeline="Today"
        )
    assert "complexity" in str(excinfo.value)


def test_missing_required_fields():
    with pytest.raises(ValidationError) as excinfo:
        ActionItem(
            title="Incomplete task"
            # missing assignee, priority, complexity, timeline
        )
    errors = str(excinfo.value)
    assert "assignee" in errors
    assert "priority" in errors
    assert "complexity" in errors
    assert "timeline" in errors


def test_valid_meeting_result_schema():
    result = MeetingResult(
        meeting_title="Sprint Planning",
        summary=ExecutiveSummary(
            title="Sprint Planning",
            overview="Planning key deliverables for Sprint 4.",
            key_takeaways=["Migrate caching"],
            participants=["Rahul", "Amit"]
        ),
        action_items=[
            ActionItem(
                title="Redis setup",
                assignee="Amit",
                priority=PriorityEnum.HIGH,
                complexity=ComplexityEnum.MODERATE,
                timeline="Thursday"
            )
        ],
        decisions=[
            Decision(
                topic="Caching",
                decision="Use Redis",
                reason="Performance limits with Memcached"
            )
        ],
        risks=[
            Risk(
                risk="Rate limits",
                description="OAuth rate limits exceeded under load",
                severity=PriorityEnum.HIGH,
                impact="Auth system",
                mitigation_strategy="Token caching"
            )
        ]
    )

    assert result.meeting_title == "Sprint Planning"
    assert len(result.action_items) == 1
    assert len(result.decisions) == 1
    assert len(result.risks) == 1
