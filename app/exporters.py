"""
Exporters module for Meeting Mind AI.
Provides JSONExporter for raw structured output and MarkdownExporter for formatted reports.
"""

import json
from pathlib import Path
from typing import Union
from app.schemas import MeetingResult


class JSONExporter:
    """Exports MeetingResult models to schema-valid JSON files."""

    @staticmethod
    def export(result: MeetingResult, output_path: Union[str, Path]) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        json_str = result.model_dump_json(indent=2)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json_str)

        return json_str


class MarkdownExporter:
    """Exports MeetingResult models to human-readable Markdown reports with tables."""

    @staticmethod
    def export(result: MeetingResult, output_path: Union[str, Path]) -> str:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        md = []
        md.append("# Meeting Digest\n")

        # Executive Summary section
        md.append("## Executive Summary\n")
        md.append(f"**Title**: {result.summary.title}\n")
        md.append(f"{result.summary.overview}\n")

        if result.summary.key_takeaways:
            md.append("### Key Takeaways")
            for takeaway in result.summary.key_takeaways:
                md.append(f"- {takeaway}")
            md.append("")

        if result.summary.participants:
            md.append("### Participants")
            for participant in result.summary.participants:
                md.append(f"- {participant}")
            md.append("")

        # Decisions section
        md.append("## Decisions\n")
        if result.decisions:
            md.append("| Decision | Reason | Owner | Who Said |")
            md.append("|---|---|---|---|")
            for d in result.decisions:
                decision_clean = d.decision.replace("|", "\\|")
                reason_clean = d.reason.replace("|", "\\|")
                owner_clean = (d.owner or "Team").replace("|", "\\|")
                who_said_clean = (d.who_said or "Team").replace("|", "\\|")
                md.append(f"| {decision_clean} | {reason_clean} | {owner_clean} | {who_said_clean} |")
            md.append("")
        else:
            md.append("*No specific architectural decisions recorded.*\n")

        # Risks & Blockers section
        md.append("## Risks & Blockers\n")
        if result.risks:
            md.append("| Risk | Impact | Severity | Who Said |")
            md.append("|---|---|---|---|")
            for r in result.risks:
                risk_clean = r.risk.replace("|", "\\|")
                impact_clean = r.impact.replace("|", "\\|")
                severity_val = r.severity.value if hasattr(r.severity, 'value') else str(r.severity)
                who_said_clean = (r.who_said or "Team").replace("|", "\\|")
                md.append(f"| {risk_clean} | {impact_clean} | {severity_val} | {who_said_clean} |")
            md.append("")
        else:
            md.append("*No project risks or blockers identified.*\n")

        # Action Items section
        md.append("## Action Items\n")
        if result.action_items:
            md.append("| Task | Task Owner (Assignee) | Who Said | Priority | Complexity | Timeline |")
            md.append("|---|---|---|---|---|---|")
            for item in result.action_items:
                task_clean = item.title.replace("|", "\\|")
                assignee_info = item.assignee
                if item.role:
                    assignee_info += f" ({item.role})"
                assignee_clean = assignee_info.replace("|", "\\|")
                who_said_clean = (item.who_said or "Discussion").replace("|", "\\|")
                prio_val = item.priority.value if hasattr(item.priority, 'value') else str(item.priority)
                comp_val = item.complexity.value if hasattr(item.complexity, 'value') else str(item.complexity)
                timeline_clean = item.timeline.replace("|", "\\|")
                md.append(f"| {task_clean} | {assignee_clean} | {who_said_clean} | {prio_val} | {comp_val} | {timeline_clean} |")
            md.append("")
        else:
            md.append("*No action items recorded.*\n")

        content = "\n".join(md)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return content
