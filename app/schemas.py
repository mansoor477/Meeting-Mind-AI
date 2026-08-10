"""
Pydantic schemas for Meeting Mind AI.
Strict typing and enum validation for structured meeting intelligence.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PriorityEnum(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ComplexityEnum(str, Enum):
    SIMPLE = "Simple"
    MODERATE = "Moderate"
    COMPLEX = "Complex"


class ActionItem(BaseModel):
    title: str = Field(
        ...,
        description="Concise, action-oriented task summary",
        examples=["Implement Redis Session Store"]
    )
    assignee: str = Field(
        ...,
        description="Name of assigned team member responsible for task execution",
        examples=["Rahul"]
    )
    who_said: Optional[str] = Field(
        None,
        description="Name and role of speaker who assigned or stated this task",
        examples=["Priya (Product Manager)"]
    )
    role: Optional[str] = Field(
        None,
        description="Role of assigned team member (e.g. Backend Lead)",
        examples=["Backend Lead"]
    )
    priority: PriorityEnum = Field(
        ...,
        description="Priority level: High, Medium, or Low"
    )
    complexity: ComplexityEnum = Field(
        ...,
        description="Complexity level: Simple, Moderate, or Complex"
    )
    timeline: str = Field(
        ...,
        description="Extracted deadline or target timeline",
        examples=["End of Sprint 4"]
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="Bulleted list of precise completion conditions"
    )
    context_snippet: Optional[str] = Field(
        None,
        description="Brief transcript quote or context snippet that generated this task"
    )


class Decision(BaseModel):
    topic: str = Field(
        ...,
        description="Technical or product topic discussed",
        examples=["Session Caching Store"]
    )
    decision: str = Field(
        ...,
        description="Key choice or consensus reached",
        examples=["Migrate session caching from Memcached to Redis"]
    )
    reason: str = Field(
        ...,
        description="Underlying rationale for the decision",
        examples=["Memcached is hitting connection limits during peak hours"]
    )
    owner: Optional[str] = Field(
        None,
        description="Owner or driver of this decision"
    )
    who_said: Optional[str] = Field(
        None,
        description="Speaker who proposed or announced this decision"
    )
    impacted_systems: List[str] = Field(
        default_factory=list,
        description="List of services or architecture components impacted"
    )


class Risk(BaseModel):
    risk: str = Field(
        ...,
        description="Short summary of the risk or blocker",
        examples=["OAuth Rate Limiting Bottleneck"]
    )
    description: str = Field(
        ...,
        description="Detailed description of potential failure or bottleneck"
    )
    severity: PriorityEnum = Field(
        ...,
        description="Severity level: High, Medium, or Low"
    )
    impact: str = Field(
        ...,
        description="Affected component or process impacted by this risk"
    )
    mitigation_strategy: Optional[str] = Field(
        None,
        description="Proposed mitigation or workaround strategy"
    )
    who_said: Optional[str] = Field(
        None,
        description="Speaker who raised or identified this risk"
    )


class ExecutiveSummary(BaseModel):
    title: str = Field(
        ...,
        description="Descriptive title of the meeting"
    )
    overview: str = Field(
        ...,
        description="High-level summary of discussion topics and outcomes"
    )
    key_takeaways: List[str] = Field(
        default_factory=list,
        description="High-impact outcome bullet points"
    )
    participants: List[str] = Field(
        default_factory=list,
        description="List of participants identified with roles"
    )


class MeetingResult(BaseModel):
    meeting_title: str = Field(
        ...,
        description="Main title of the meeting"
    )
    summary: ExecutiveSummary = Field(
        ...,
        description="Executive summary details"
    )
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="Collection of validated action items"
    )
    decisions: List[Decision] = Field(
        default_factory=list,
        description="Collection of key decisions"
    )
    risks: List[Risk] = Field(
        default_factory=list,
        description="Collection of identified project risks and blockers"
    )
