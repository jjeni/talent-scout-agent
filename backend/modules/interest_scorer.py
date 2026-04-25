import asyncio
import json
import logging
import os

from dotenv import load_dotenv

from models.output_schema import ConversationTranscript, InterestBreakdown
from utils.llm_utils import generate_content

load_dotenv()
logger = logging.getLogger(__name__)

# Use Flash Lite for analysis to save the main Flash quota for the agent
MODEL_NAME = "gemini-2.5-flash-lite"

# Sub-score weights
WEIGHTS = {
    "stated_interest": 0.35,
    "engagement_depth": 0.25,
    "availability": 0.20,
    "sentiment": 0.20,
}

INTEREST_SCORING_PROMPT = """
You are an expert recruiter analyst. Analyze this conversation transcript between a
recruiter agent and a candidate and score the candidate's genuine interest.

Rate each dimension 0-100:

1. stated_interest (0-100):
   - 0-20: Explicitly declined or very negative
   - 21-40: Politely disengaged, looking but not for this
   - 41-60: Neutral / open but not enthusiastic
   - 61-80: Positive and engaged
   - 81-100: Highly enthusiastic, proactively asks about next steps

2. engagement_depth (0-100):
   - How deeply does the candidate engage? Do they ask follow-up questions?
   - Short replies with no questions = low; detailed replies with questions = high

3. availability (0-100):
   - 0-30: Not available (on PIP, long notice, relocation issues)
   - 31-60: Available but constrained (3+ month notice, needs visa)
   - 61-80: Available within 4 weeks
   - 81-100: Immediately available or very short notice

4. sentiment (0-100):
   - Overall emotional tone toward this specific opportunity
   - Excited language, positive framing = high; hesitant, evasive = low

Also provide:
- key_signals: list of 3 important direct quotes or behavioral signals from the candidate
- red_flags: list of any concerning signals (counteroffer risk, not actually looking, wrong fit expectation, etc.)
- summary: one sentence summary of candidate interest level for the recruiter

Return ONLY valid JSON with this exact structure:
{
  "stated_interest": <int 0-100>,
  "engagement_depth": <int 0-100>,
  "availability": <int 0-100>,
  "sentiment": <int 0-100>,
  "key_signals": ["signal1", "signal2", "signal3"],
  "red_flags": ["flag1"],
  "summary": "one sentence"
}
"""


def _format_transcript(transcript: ConversationTranscript) -> str:
    """Format transcript into readable text for the LLM."""
    lines = []
    for turn in transcript.turns:
        if turn.agent:
            lines.append(f"Agent: {turn.agent}")
        if turn.candidate and turn.candidate != "[Conversation closed]":
            lines.append(f"Candidate: {turn.candidate}")
    return "\n".join(lines)


async def score_interest(transcript: ConversationTranscript, api_key: str = None, provider: str = "gemini", model: str = None) -> InterestBreakdown:
    """Analyzes a conversation transcript to produce structured interest scores."""
    if not transcript.turns:
        return _fallback_breakdown("Empty transcript — no conversation data")

    formatted = _format_transcript(transcript)
    prompt = f"{INTEREST_SCORING_PROMPT}\n\n--- CONVERSATION TRANSCRIPT ---\n{formatted}\n--- END ---"

    # Rate limit: ensure we don't spam the 5 RPM limit
    await asyncio.sleep(6.0)

    try:
        raw = await generate_content(
            prompt=prompt,
            provider=provider,
            model_name=model or MODEL_NAME,
            api_key=api_key,
            response_mime_type="application/json",
            temperature=0.1
        )

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        stated = float(data.get("stated_interest", 50))
        engagement = float(data.get("engagement_depth", 50))
        availability = float(data.get("availability", 50))
        sentiment = float(data.get("sentiment", 50))

        total = (
            stated * WEIGHTS["stated_interest"]
            + engagement * WEIGHTS["engagement_depth"]
            + availability * WEIGHTS["availability"]
            + sentiment * WEIGHTS["sentiment"]
        )

        # Add penalty if candidate declined
        if transcript.exit_reason == "declined":
            total = min(total, 25.0)
            stated = min(stated, 20.0)

        return InterestBreakdown(
            stated_interest=round(stated, 1),
            engagement_depth=round(engagement, 1),
            availability=round(availability, 1),
            sentiment=round(sentiment, 1),
            total=round(total, 1),
            key_signals=data.get("key_signals", []),
            red_flags=data.get("red_flags", []),
            summary=data.get("summary", "Interest level could not be determined."),
        )

    except json.JSONDecodeError as e:
        logger.error(f"Interest scorer JSON error: {e}")
        return _fallback_breakdown("JSON parse error in scoring response")
    except Exception as e:
        logger.error(f"Interest scorer error: {e}")
        return _fallback_breakdown(str(e))


def _fallback_breakdown(reason: str) -> InterestBreakdown:
    return InterestBreakdown(
        stated_interest=50.0,
        engagement_depth=50.0,
        availability=50.0,
        sentiment=50.0,
        total=50.0,
        key_signals=[],
        red_flags=[f"Scoring unavailable: {reason}"],
        summary="Interest score could not be computed — manual review recommended.",
    )
