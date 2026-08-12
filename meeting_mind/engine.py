"""
AI Extraction Engine for Meeting Mind AI.
Supports Claude API (Anthropic), Azure OpenAI (Pydantic Structured Outputs),
and an offline Mock Engine fallback.
"""

import json
import os
import re
from typing import Any, cast, Dict, List, Optional, Tuple
from pydantic import ValidationError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from meeting_mind.models import (
    MeetingIntelligenceOutput,
    ExecutiveSummary,
    ActionItem,
    ArchitectureDecision,
    ProjectRisk,
    PriorityEnum,
    EffortEnum
)

anthropic: Any = None
try:
    import anthropic  # type: ignore
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

AzureOpenAI: Any = None
OpenAI: Any = None
try:
    import openai  # type: ignore
    from openai import AzureOpenAI, OpenAI  # type: ignore
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


SYSTEM_PROMPT = """
You are Meeting Mind AI, an enterprise architecture & sprint planning decision intelligence engine.
Your role is to ingest preprocessed meeting transcripts and extract structured meeting intelligence with 100% precision.

Strict Multi-Dimensional Extraction Pipeline:
Trace the exact intelligence flow:
WHO SAID WHAT (Speaker Attribution) -> WHO OWNS THE TASK (Assignee) -> DEADLINE -> PRIORITY & EFFORT -> DECISIONS -> RISKS

Multi-Dimensional Extraction Directives:
1. Executive Summary:
   - Overview: Clear, professional narrative of the core topics, decisions, and outcomes discussed.
   - Key Takeaways: High-impact bulleted outcome points.
   - Participants: List all identified team members with roles (e.g. "Rahul (Backend Lead)").

2. Action Items (Tasks):
   - Extract direct task assignments for specific individuals.
   - who_said: Full name and role of the speaker who introduced or assigned the task (e.g., 'Priya (Product Manager)').
   - assignee: Full name and role of assigned team member responsible for execution (e.g., 'Rahul (Backend Lead)'). Distinguish between who spoke and who owns the task!
   - priority: Priority (High, Medium, Low) based on urgency cues ("blocker", "must have" -> High).
   - effort: Effort (Simple, Moderate, Complex) based on technical scope.
   - target_timeline: Target Timeline / Deadline (e.g., "End of Sprint 4", "by Wednesday", "Friday").
   - acceptance_criteria: Precise bulleted list of completion conditions based on discussion.
   - context_snippet: Brief transcript quote showing task discussion context.

3. Architecture & Design Decisions:
   - Identify concrete technical choices agreed upon by the team.
   - State topic, decision, rationale, owner, who_said (speaker), and impacted systems.

4. Blockers & Project Risks:
   - Identify technical bottlenecks, third-party dependencies, security risks, or timeline risks.
   - State affected_component, risk_description, severity, who_said (speaker), and mitigation_strategy.
"""

MEETING_INTELLIGENCE_TOOL_SPEC: Any = {
    "name": "submit_meeting_intelligence",
    "description": "Submit structured meeting intelligence data extracted from transcript",
    "input_schema": MeetingIntelligenceOutput.model_json_schema()
}


class MeetingMindEngine:
    def __init__(
        self,
        provider: str = "auto",
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        force_mock: bool = False
    ):
        """
        provider choices: 'auto', 'azure_openai', 'anthropic', 'mock'
        """
        self.force_mock = force_mock
        self.provider = provider.lower()

        # Azure OpenAI credentials
        self.azure_api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/")
        self.azure_deployment = azure_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        self.azure_client: Optional[Any] = None
        self.anthropic_client: Optional[Any] = None

        # Anthropic credentials
        self.anthropic_api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.claude_model = model

        # Determine active provider
        if force_mock or self.provider == "mock":
            self.active_provider = "mock"
        elif (self.provider == "azure_openai" or (self.provider == "auto" and self.azure_api_key)) and HAS_OPENAI and self.azure_api_key:
            self.active_provider = "azure_openai"
            try:
                self.azure_client = AzureOpenAI(
                    azure_endpoint=self.azure_endpoint,
                    api_key=self.azure_api_key,
                    api_version=self.azure_api_version
                )
            except Exception as e:
                print(f"[MeetingMindEngine Warning] Failed to initialize AzureOpenAI client: {e}")
                self.azure_client = None
                self.active_provider = "mock"
        elif (self.provider == "anthropic" or (self.provider == "auto" and self.anthropic_api_key)) and HAS_ANTHROPIC and self.anthropic_api_key:
            self.active_provider = "anthropic"
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        else:
            self.active_provider = "mock"

    def process_transcript(self, cleaned_transcript: str) -> MeetingIntelligenceOutput:
        """Processes transcript using selected provider or mock fallback."""
        if self.active_provider == "azure_openai":
            return self._process_azure_openai(cleaned_transcript)
        elif self.active_provider == "anthropic":
            return self._process_anthropic(cleaned_transcript)
        else:
            return self._mock_extraction(cleaned_transcript)

    def _process_azure_openai(self, transcript: str) -> MeetingIntelligenceOutput:
        """Uses Azure OpenAI Structured Outputs with Pydantic model validation."""
        try:
            azure_client = self.azure_client
            if azure_client is None:
                raise RuntimeError("Azure client is not available")
            response = azure_client.beta.chat.completions.parse(
                model=self.azure_deployment,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Please process the following meeting transcript:\n\n{transcript}"}
                ],
                response_format=MeetingIntelligenceOutput
            )
            parsed_output = response.choices[0].message.parsed
            if parsed_output:
                return parsed_output
            raise ValueError("Azure OpenAI response contained no parsed output.")
        except Exception as e:
            print(f"[MeetingMindEngine Warning] Azure OpenAI extraction failed ({e}). Falling back to mock provider.")
            return self._mock_extraction(transcript)

    def _process_anthropic(self, transcript: str) -> MeetingIntelligenceOutput:
        """Uses Anthropic Claude API tool calling with Pydantic model validation."""
        try:
            anthropic_client = self.anthropic_client
            if anthropic_client is None:
                raise RuntimeError("Anthropic client is not available")
            response = anthropic_client.messages.create(
                model=self.claude_model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=cast(list[Any], [MEETING_INTELLIGENCE_TOOL_SPEC]),
                tool_choice={"type": "tool", "name": "submit_meeting_intelligence"},
                messages=[
                    {"role": "user", "content": f"Please process the following meeting transcript:\n\n{transcript}"}
                ]
            )

            tool_call = None
            for block in response.content:
                if block.type == "tool_use" and block.name == "submit_meeting_intelligence":
                    tool_call = block.input
                    break

            if not tool_call:
                raise ValueError("Claude response did not contain submit_meeting_intelligence tool call.")

            return MeetingIntelligenceOutput.model_validate(tool_call)

        except Exception as e:
            print(f"[MeetingMindEngine Warning] Anthropic API failed ({e}). Falling back to mock provider.")
            return self._mock_extraction(transcript)

    def _mock_extraction(self, transcript: str) -> MeetingIntelligenceOutput:
        """Dynamic transcript parser extracting customized intelligence for any meeting text."""
        import re

        lines = [line.strip() for line in transcript.splitlines() if line.strip()]

        def format_task_title(raw_text: str) -> str:
            text = raw_text.strip()
            if ":" in text:
                text = text.split(":", 1)[1].strip()
            prefixes = [
                r"^(?:good morning|hello|hi|hey|thanks|thank you)[^,.!?]*[,.!?]\s*",
                r"^(?:for action items|action items|as an action item|action item)[^:]*:\s*",
                r"^(?:for the decision on payment vendor|decision on payment vendor|for decision on)[^:]*:\s*",
                r"^(?:right|so|basically|you know|i mean|well|okay|ok)[,\s]+",
                r"^(?:we decided to|decided to|we should|i will|let's|lets|need to|must|please|can you)\s+",
                r"^[A-Za-z0-9\s()._-]+ (?:will|shall|to)\s+",
            ]
            for p in prefixes:
                text = re.sub(p, "", text, flags=re.IGNORECASE).strip()

            first_clause = re.split(r"[.;!\n]", text)[0].strip()
            words = first_clause.split()
            if len(words) > 7:
                title = " ".join(words[:7]).rstrip(",-:")
            else:
                title = first_clause.rstrip(",-:")

            title = title.strip().title()
            if len(title) < 5:
                return "Execute Technical Requirement"
            return title

        def format_takeaway(raw_text: str) -> str:
            text = raw_text.strip()
            if ":" in text:
                text = text.split(":", 1)[1].strip()
            text = re.sub(r"^(?:right|so|basically|you know|i mean|well|okay|ok)[,\s]+", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"^(?:for action items|action items|as an action item)[^:]*:\s*", "", text, flags=re.IGNORECASE).strip()
            if not text:
                return ""
            text = text[0].upper() + text[1:]
            if not text.endswith((".", "!", "?")):
                text += "."
            return text
        
        # 1. Extract Participants dynamically
        participants = []
        for line in lines:
            match = re.match(r"^([A-Za-z0-9\s()._-]+):\s*(.*)", line)
            if match:
                speaker = match.group(1).strip()
                if speaker and speaker not in participants and len(speaker) < 45:
                    participants.append(speaker)

        if not participants:
            participants = ["Team Lead", "Engineering Specialist"]

        # 2. Synthesize Meeting Title & Overview
        meeting_title = "Meeting Sync & Action Items"
        topic_candidates = []
        for line in lines:
            if any(w in line.lower() for w in ["permission", "aws", "infosec", "auth", "sprint", "redis", "database", "ui", "api", "deploy", "release", "fix", "issue", "stripe", "payment", "token"]):
                topic_candidates.append(line)

        if topic_candidates:
            first_candidate = topic_candidates[0]
            meeting_title = format_task_title(first_candidate)
            if len(meeting_title) < 5:
                meeting_title = "Engineering & Operations Sync"

        overview = f"Discussion included {len(participants)} participant(s) ({', '.join(participants[:3])}) covering key tasks and deliverables."
        if lines:
            clean_first = lines[0].split(":", 1)[-1].strip() if ":" in lines[0] else lines[0]
            overview += f" Key focus: '{clean_first[:100]}'."

        def resolve_speaker_and_assignee(speaker_line: str, raw_content: str, known_participants: List[str]) -> Tuple[str, str]:
            who_said = speaker_line
            assignee = speaker_line

            # Normalize speaker_line if known in participants
            for p in known_participants:
                p_name = p.split("(")[0].strip()
                who_name = speaker_line.split("(")[0].strip()
                if p_name.lower() == who_name.lower():
                    who_said = p
                    assignee = p
                    break

            # Look for assigned third-person in content (e.g. "Rahul (Backend Lead) will implement...")
            for p in known_participants:
                p_name = p.split("(")[0].strip()
                if p_name and p_name.lower() in raw_content.lower():
                    pattern = rf"\b{re.escape(p_name)}\b.*?\b(?:will|shall|can|to|assigned|take|implement|update|write|unblock|deploy|handle|build|setup)\b"
                    if re.search(pattern, raw_content, re.IGNORECASE) or f"{p_name} will" in raw_content.lower() or f"{p_name} to" in raw_content.lower():
                        assignee = p
                        break

            return who_said, assignee

        # 3. Extract Action Items dynamically
        action_items = []
        action_keywords = ["unblock", "implement", "deploy", "update", "create", "fix", "verify", "action", "task", "assigned", "will", "need to", "build", "setup", "take the lead", "i'll take", "i'll build", "i will"]
        
        task_idx = 1
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in action_keywords) and not line_lower.rstrip().endswith("?") and not any(dk in line_lower for dk in ["we decided to use", "decided to use redis"]):
                speaker = participants[0]
                content = line
                if ":" in line:
                    parts = line.split(":", 1)
                    speaker = parts[0].strip()
                    content = parts[1].strip()

                who_said, assignee = resolve_speaker_and_assignee(speaker, content, participants)

                # Determine Priority
                if any(p in line_lower for p in ["high", "urgent", "blocker", "today", "immediately", "asap", "12 pm", "security", "permission", "infosec"]):
                    priority = PriorityEnum.HIGH
                elif any(p in line_lower for p in ["low", "nice to have", "sometime"]):
                    priority = PriorityEnum.LOW
                else:
                    priority = PriorityEnum.MEDIUM

                # Determine Effort
                if len(content) > 100 or any(c in line_lower for c in ["cluster", "architecture", "migrate", "infra", "permission", "aws", "sentinel"]):
                    effort = EffortEnum.COMPLEX
                elif len(content) < 40:
                    effort = EffortEnum.SIMPLE
                else:
                    effort = EffortEnum.MODERATE

                # Extract Timeline / Deadline
                timeline = "As discussed"
                time_match = re.search(r"\b(today|tomorrow|by \d+(?::\d+)?\s*(?:AM|PM|am|pm)?|by \w+(?:\s+next\s+week)?|end of sprint \d*|sprint \d*|friday|thursday|wednesday|monday|tuesday)\b", line, re.IGNORECASE)
                if time_match:
                    timeline = time_match.group(0).title()

                clean_item_title = format_task_title(content)

                # Extract acceptance criteria if present in nearby text or line
                ac_list = []
                if "acceptance criteria" in line_lower:
                    ac_text = re.sub(r".*?acceptance criteria:?\s*", "", line, flags=re.IGNORECASE)
                    ac_list = [c.strip() for c in re.split(r"[,;.]\s*(?:second|third|and)?\s*", ac_text) if len(c.strip()) > 5]

                if not ac_list:
                    ac_list = [
                        f"Implement requirement: {content[:80]}",
                        f"Verify resolution and sign off with {assignee}"
                    ]

                action_items.append(ActionItem(
                    task_id=f"ACTION-00{task_idx}",
                    title=clean_item_title,
                    assignee=assignee,
                    who_said=who_said,
                    priority=priority,
                    effort=effort,
                    target_timeline=timeline,
                    acceptance_criteria=ac_list,
                    context_snippet=f"{who_said}: {content[:100]}"
                ))

                task_idx += 1
                if len(action_items) >= 5:
                    break

        if not action_items:
            action_items.append(ActionItem(
                task_id="ACTION-001",
                title="Follow Up On Action Items",
                assignee=participants[0],
                who_said=participants[0],
                priority=PriorityEnum.MEDIUM,
                effort=EffortEnum.MODERATE,
                target_timeline="End of Week",
                acceptance_criteria=["Tasks logged in tracker", "Team aligned"],
                context_snippet="General team action item alignment"
            ))

        # 4. Extract Decisions dynamically
        decisions = []
        decision_keywords = ["decide", "decided", "agreed", "approved", "confirm", "settled", "recommend", "choose"]
        dec_idx = 1
        for line in lines:
            line_lower = line.lower()
            if any(dk in line_lower for dk in decision_keywords):
                content = line
                who_said = participants[0]
                if ":" in line:
                    who_said, content = line.split(":", 1)
                    who_said = who_said.strip()
                    content = content.strip()

                owner = who_said
                for p in participants:
                    p_name = p.split("(")[0].strip()
                    if p_name.lower() in content.lower() or p_name.lower() == who_said.split("(")[0].strip().lower():
                        owner = p
                        break

                topic_title = format_task_title(content)
                systems = []
                for sys_name in ["Auth Microservice", "User Session Store", "API Gateway", "Payment Gateway", "Stripe API", "AWS ElastiCache", "Core Systems"]:
                    if sys_name.lower() in line_lower:
                        systems.append(sys_name)
                if not systems:
                    systems = ["Core Architecture"]

                decisions.append(ArchitectureDecision.model_validate({
                    "decision_id": f"DEC-00{dec_idx}",
                    "topic": topic_title,
                    "decision": content[:120],
                    "rationale": f"Agreed upon in discussion: {content[:100]}",
                    "impacted_systems": systems,
                    "owner": owner,
                    "who_said": who_said
                }))
                dec_idx += 1
                if len(decisions) >= 3:
                    break

        if not decisions:
            decisions.append(ArchitectureDecision.model_validate({
                "decision_id": "DEC-001",
                "topic": "Operational Plan Alignment",
                "decision": "Proceed with agreed action items and review in next sync",
                "rationale": "Ensures execution continuity and milestone delivery",
                "impacted_systems": ["Project Workflow"],
                "owner": participants[0],
                "who_said": participants[0]
            }))

        # 5. Extract Risks & Blockers dynamically
        risks = []
        risk_keywords = ["blocker", "risk", "permission", "issue", "delay", "fail", "limit", "security", "warning", "infosec", "lock time"]
        risk_idx = 1
        for line in lines:
            line_lower = line.lower()
            if any(rk in line_lower for rk in risk_keywords):
                content = line
                who_said = participants[0]
                if ":" in line:
                    who_said, content = line.split(":", 1)
                    who_said = who_said.strip()
                    content = content.strip()

                risk_title = format_task_title(content)
                severity = PriorityEnum.HIGH if any(s in line_lower for s in ["high", "critical", "blocker", "urgent", "permission", "infosec", "lock"]) else PriorityEnum.MEDIUM
                
                mitigation = "Review with lead and escalate if necessary"
                if "mitigation" in line_lower or "strategy" in line_lower:
                    mitigation = content[:120]

                risks.append(ProjectRisk.model_validate({
                    "risk_id": f"RISK-00{risk_idx}",
                    "risk_description": content,
                    "severity": severity,
                    "affected_component": "System Access / Security / Operations",
                    "mitigation_strategy": mitigation,
                    "who_said": who_said
                }))
                risk_idx += 1
                if len(risks) >= 3:
                    break

        if not risks:
            risks.append(ProjectRisk.model_validate({
                "risk_id": "RISK-001",
                "risk_description": "Dependencies & Timeline Tracking - Potential schedule delay",
                "severity": PriorityEnum.LOW,
                "affected_component": "Project Schedule",
                "mitigation_strategy": "Monitor progress in daily standups",
                "who_said": participants[0]
            }))

        # 6. Synthesize Key Takeaways
        key_takeaways = []

        # Point 1: What did we do / primary meeting topic discussed
        if topic_candidates:
            primary_topic = format_takeaway(topic_candidates[0])
            if primary_topic:
                key_takeaways.append(f"Meeting Discussion: Reviewed and aligned on core technical priorities — {primary_topic}")
        elif lines:
            first_clean = format_takeaway(lines[0])
            if first_clean:
                key_takeaways.append(f"Meeting Discussion: Conducted technical alignment on project deliverables — {first_clean}")

        # Point 2: Important decisions agreed upon
        if decisions:
            main_dec = decisions[0]
            key_takeaways.append(f"Key Decision Reached: Agreed to {format_takeaway(main_dec.decision)}")

        # Point 3: Critical action items assigned
        if action_items:
            main_action = action_items[0]
            assignee_str = f" to {main_action.assignee}" if main_action.assignee else ""
            key_takeaways.append(f"Primary Deliverable: Assigned '{main_action.title}'{assignee_str} with timeline '{main_action.target_timeline}'.")

        # Point 4: Major risk / blocker discussed
        if risks:
            main_risk = risks[0]
            sev_str = main_risk.severity.value if hasattr(main_risk.severity, 'value') else str(main_risk.severity)
            key_takeaways.append(f"Major Risk/Blocker: Addressed {format_takeaway(main_risk.risk_description)} (Severity: {sev_str}).")

        if len(key_takeaways) < 2:
            key_takeaways.append(f"Team Alignment: Confirmed execution roadmap across {len(participants)} team members.")

        return MeetingIntelligenceOutput(
            meeting_title=meeting_title,
            date="2026-08-10",
            summary=ExecutiveSummary(
                title=meeting_title,
                overview=overview,
                key_takeaways=key_takeaways,
                participants=participants
            ),
            action_items=action_items,
            decisions=decisions,
            risks=risks
        )
