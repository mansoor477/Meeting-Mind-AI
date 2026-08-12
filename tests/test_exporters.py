"""
Unit tests for JSONExporter and MarkdownExporter in app/exporters.py.
"""

import json
from pathlib import Path
import pytest
from app.schemas import (
    MeetingResult, ExecutiveSummary, ActionItem, Decision, Risk,
    PriorityEnum, ComplexityEnum
)
from app.exporters import JSONExporter, MarkdownExporter


@pytest.fixture
def sample_meeting_result():
    return MeetingResult(
        meeting_title="Architecture Session",
        summary=ExecutiveSummary(
            title="Architecture & Caching Session",
            overview="Decided to move from Memcached to Redis.",
            key_takeaways=["Redis migration approved"],
            participants=["Rahul (Backend Lead)", "Amit (DevOps Lead)"]
        ),
        action_items=[
            ActionItem(
                title="Configure Redis cluster",
                assignee="Amit",
                role="DevOps Lead",
                who_said="Rahul (Backend Lead)",
                context_snippet="We should set up Redis for sessions.",
                priority=PriorityEnum.HIGH,
                complexity=ComplexityEnum.MODERATE,
                timeline="Thursday",
                acceptance_criteria=["Redis deployed"]
            )
        ],
        decisions=[
            Decision(
                topic="Session Store",
                decision="Migrate to Redis",
                reason="Memcached connection limit bottlenecks",
                owner="Rahul",
                who_said="Rahul (Backend Lead)",
                impacted_systems=["Backend API"]
            )
        ],
        risks=[
            Risk(
                risk="OAuth rate limits",
                description="Potential login failures under heavy load",
                severity=PriorityEnum.HIGH,
                impact="Auth Service",
                mitigation_strategy="Request backoff"
                ,
                who_said="Amit (DevOps Lead)"
            )
        ]
    )


def test_json_exporter(tmp_path, sample_meeting_result):
    output_file = tmp_path / "meeting_result.json"
    exported_str = JSONExporter.export(sample_meeting_result, output_file)

    assert output_file.exists()
    parsed_json = json.loads(output_file.read_text(encoding="utf-8"))

    assert parsed_json["meeting_title"] == "Architecture Session"
    assert parsed_json["action_items"][0]["assignee"] == "Amit"
    assert parsed_json["action_items"][0]["priority"] == "High"
    assert parsed_json["action_items"][0]["complexity"] == "Moderate"


def test_markdown_exporter(tmp_path, sample_meeting_result):
    output_file = tmp_path / "meeting_digest.md"
    exported_md = MarkdownExporter.export(sample_meeting_result, output_file)

    assert output_file.exists()

    # Check Markdown titles and table headers
    assert "# Meeting Digest" in exported_md
    assert "## Executive Summary" in exported_md
    assert "## Decisions" in exported_md
    assert "| Decision | Reason | Owner | Who Said |" in exported_md
    assert "Migrate to Redis" in exported_md
    assert "Memcached connection limit bottlenecks" in exported_md

    assert "## Risks & Blockers" in exported_md
    assert "| Risk | Impact | Severity | Who Said |" in exported_md
    assert "OAuth rate limits" in exported_md

    assert "## Action Items" in exported_md
    assert "| Task | Task Owner (Assignee) | Who Said | Priority | Complexity | Timeline |" in exported_md
    assert "Configure Redis cluster" in exported_md
    assert "Amit (DevOps Lead)" in exported_md
