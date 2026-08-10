"""
Pydantic schemas and guardrails for Meeting Mind AI.
Enforces strict structured outputs for downstream intelligence processing.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PriorityEnum(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class EffortEnum(str, Enum):
    SIMPLE = "Simple"
    MODERATE = "Moderate"
    COMPLEX = "Complex"


class ActionItem(BaseModel):
    task_id: str = Field(
        ...,
        description="Unique task identifier, e.g., ACTION-001",
        examples=["ACTION-001"]
    )
    title: str = Field(
        ...,
        description="Concise, action-oriented task summary (e.g., 'Implement JWT Refresh Token Rotation')",
        examples=["Implement JWT Refresh Token Rotation"]
    )
    assignee: str = Field(
        ...,
        description="Full name and role of assigned team member responsible for executing the task (e.g., 'Rahul (Backend Lead)')",
        examples=["Rahul (Backend Lead)"]
    )
    who_said: Optional[str] = Field(
        None,
        description="Full name and role of the speaker who spoke or introduced this task in the transcript (e.g., 'Priya (Product Manager)')",
        examples=["Priya (Product Manager)"]
    )
    priority: PriorityEnum = Field(
        ...,
        description="Priority level inferred from discussion urgency cues (High, Medium, Low)"
    )
    effort: EffortEnum = Field(
        ...,
        description="Estimated effort or complexity (Simple, Moderate, Complex)"
    )
    target_timeline: str = Field(
        ...,
        description="Extracted deadline or implied timeframe (e.g., 'End of Sprint 4', 'By Friday')",
        examples=["End of Sprint 4"]
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="Bulleted list of precise conditions defining task completion based on discussion"
    )
    context_snippet: Optional[str] = Field(
        None,
        description="Brief transcript quote or context snippet that generated this task"
    )


class ArchitectureDecision(BaseModel):
    decision_id: str = Field(
        ...,
        description="Unique decision identifier, e.g., DEC-001",
        examples=["DEC-001"]
    )
    topic: str = Field(
        ...,
        description="Core technical or product topic (e.g., 'Session Caching Store')",
        examples=["Session Caching Store"]
    )
    decision: str = Field(
        ...,
        description="Key choice agreed upon by the team (e.g., 'Decided to use Redis for session caching instead of Memcached')",
        examples=["Decided to use Redis for session caching instead of Memcached"]
    )
    rationale: str = Field(
        ...,
        description="Underlying technical or business reason for the decision"
    )
    impacted_systems: List[str] = Field(
        default_factory=list,
        description="List of services, modules, or infrastructure components impacted"
    )
    owner: Optional[str] = Field(
        None,
        description="Key decision maker or owner driving this architecture choice"
    )
    who_said: Optional[str] = Field(
        None,
        description="Speaker who announced or stated this decision in the meeting"
    )


class ProjectRisk(BaseModel):
    risk_id: str = Field(
        ...,
        description="Unique risk identifier, e.g., RISK-001",
        examples=["RISK-001"]
    )
    risk_description: str = Field(
        ...,
        description="Technical bottleneck, external dependency, or potential failure point identified"
    )
    severity: PriorityEnum = Field(
        ...,
        description="Risk severity level (High, Medium, Low)"
    )
    mitigation_strategy: Optional[str] = Field(
        None,
        description="Proposed risk mitigation approach discussed during the meeting"
    )
    affected_component: str = Field(
        ...,
        description="System or process affected by this risk"
    )
    who_said: Optional[str] = Field(
        None,
        description="Speaker who raised or identified this risk in the meeting"
    )


class ExecutiveSummary(BaseModel):
    title: str = Field(
        ...,
        description="Descriptive meeting title based on transcript topic"
    )
    overview: str = Field(
        ...,
        description="High-level narrative summary of core discussion topics and goals"
    )
    key_takeaways: List[str] = Field(
        default_factory=list,
        description="High-impact bullet points summarizing the outcome of the meeting"
    )
    participants: List[str] = Field(
        default_factory=list,
        description="List of identified team members and roles (e.g., ['Rahul (Backend Lead)', 'Priya (Product Manager)'])"
    )


class MeetingIntelligenceOutput(BaseModel):
    meeting_title: str = Field(
        ...,
        description="Title of the meeting"
    )
    date: Optional[str] = Field(
        None,
        description="Date of the meeting if mentioned or inferred"
    )
    summary: ExecutiveSummary = Field(
        ...,
        description="Executive summary and attendee insights"
    )
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="Collection of schema-validated action items"
    )
    decisions: List[ArchitectureDecision] = Field(
        default_factory=list,
        description="Collection of architectural and technical decisions"
    )
    risks: List[ProjectRisk] = Field(
        default_factory=list,
        description="Collection of project risks and blockers"
    )
