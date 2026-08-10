"""
Multi-format Exporter Engine for Meeting Mind AI.
Generates JSON payloads and formatted Markdown digests for Slack/Teams/Wikis.
"""

import json
from typing import Union, Dict, Any
from meeting_mind.models import MeetingIntelligenceOutput, PriorityEnum


class JSONExporter:
    @staticmethod
    def export_string(data: MeetingIntelligenceOutput, indent: int = 2) -> str:
        """Serializes MeetingIntelligenceOutput to formatted JSON string."""
        return data.model_dump_json(indent=indent)

    @staticmethod
    def export_file(data: MeetingIntelligenceOutput, filepath: str, indent: int = 2) -> str:
        """Writes MeetingIntelligenceOutput to JSON file."""
        json_str = JSONExporter.export_string(data, indent=indent)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_str)
        return filepath


class MarkdownExporter:
    @staticmethod
    def _priority_badge(priority: PriorityEnum) -> str:
        p_str = priority.value if hasattr(priority, 'value') else str(priority)
        if p_str.lower() == "high":
            return "🔴 **High**"
        elif p_str.lower() == "medium":
            return "🟡 **Medium**"
        else:
            return "🟢 **Low**"

    @staticmethod
    def export_string(data: MeetingIntelligenceOutput) -> str:
        """Generates Executive Markdown Digest."""
        md_lines = []

        # Document Title
        md_lines.append(f"# 🧠 Executive Digest: {data.meeting_title}")
        if data.date:
            md_lines.append(f"**Date:** {data.date}")
        md_lines.append("")

        # 1. Executive Summary
        md_lines.append("## 📌 Executive Summary")
        md_lines.append(f"{data.summary.overview}")
        md_lines.append("")
        
        md_lines.append("### 🔑 Key Takeaways")
        for takeaway in data.summary.key_takeaways:
            md_lines.append(f"- {takeaway}")
        md_lines.append("")

        if data.summary.participants:
            md_lines.append("### 👥 Identified Participants")
            md_lines.append(", ".join([f"`{p}`" for p in data.summary.participants]))
            md_lines.append("")

        md_lines.append("---")

        # 2. Action Items Master Table & Details
        md_lines.append("## ⚡ Action Items Matrix")
        if data.action_items:
            md_lines.append("| ID | Task Title | Who Said (Speaker) | Task Owner (Assignee) | Priority | Complexity | Deadline / Timeline |")
            md_lines.append("|---|---|---|---|---|---|---|")
            for item in data.action_items:
                p_badge = MarkdownExporter._priority_badge(item.priority)
                effort = item.effort.value if hasattr(item.effort, 'value') else str(item.effort)
                who_said_str = f"`{item.who_said}`" if item.who_said else "`Discussion`"
                md_lines.append(f"| **{item.task_id}** | {item.title} | {who_said_str} | `{item.assignee}` | {p_badge} | `{effort}` | {item.target_timeline} |")
            md_lines.append("")

            md_lines.append("### 📋 Task Acceptance Criteria Breakdown")
            for item in data.action_items:
                p_badge = MarkdownExporter._priority_badge(item.priority)
                who_said_info = f" | **Who Said:** `{item.who_said}`" if item.who_said else ""
                md_lines.append(f"#### [{item.task_id}] {item.title}")
                md_lines.append(f"- **Task Owner:** `{item.assignee}`{who_said_info} | **Priority:** {p_badge} | **Deadline:** {item.target_timeline}")
                if item.context_snippet:
                    md_lines.append(f"- **Discussion Context:** *\"{item.context_snippet}\"*")
                if item.acceptance_criteria:
                    md_lines.append("- **Acceptance Criteria:**")
                    for ac in item.acceptance_criteria:
                        md_lines.append(f"  - [ ] {ac}")
                md_lines.append("")
        else:
            md_lines.append("*No action items identified in this session.*")
            md_lines.append("")

        md_lines.append("---")

        # 3. Architecture & Design Decisions
        md_lines.append("## 🏗️ Architecture & Design Decisions")
        if data.decisions:
            md_lines.append("| ID | Topic | Decision & Agreed Choice | Rationale | Impacted Systems | Decision Owner | Raised By |")
            md_lines.append("|---|---|---|---|---|---|---|")
            for dec in data.decisions:
                systems = ", ".join([f"`{s}`" for s in dec.impacted_systems]) if dec.impacted_systems else "N/A"
                owner = f"`{dec.owner}`" if dec.owner else "Team"
                who_said = f"`{dec.who_said}`" if dec.who_said else "Team"
                md_lines.append(f"| **{dec.decision_id}** | **{dec.topic}** | {dec.decision} | {dec.rationale} | {systems} | {owner} | {who_said} |")
            md_lines.append("")
        else:
            md_lines.append("*No explicit architectural decisions recorded.*")
            md_lines.append("")

        md_lines.append("---")

        # 4. Blockers & Project Risk Log
        md_lines.append("## ⚠️ Blockers & Project Risk Matrix")
        if data.risks:
            md_lines.append("| ID | Affected Component | Risk Description | Severity | Raised By | Mitigation Strategy |")
            md_lines.append("|---|---|---|---|---|---|")
            for risk in data.risks:
                s_badge = MarkdownExporter._priority_badge(risk.severity)
                mitigation = risk.mitigation_strategy or "To be finalized by project lead."
                who_said = f"`{risk.who_said}`" if risk.who_said else "Team"
                md_lines.append(f"| **{risk.risk_id}** | `{risk.affected_component}` | {risk.risk_description} | {s_badge} | {who_said} | {mitigation} |")
            md_lines.append("")
        else:
            md_lines.append("*No critical risks or blockers flagged during discussion.*")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("*Generated automatically by Meeting Mind AI Engine.*")

        return "\n".join(md_lines)

    @staticmethod
    def export_file(data: MeetingIntelligenceOutput, filepath: str) -> str:
        """Writes Executive Digest Markdown to file."""
        md_str = MarkdownExporter.export_string(data)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_str)
        return filepath
