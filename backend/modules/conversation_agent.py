import asyncio
import logging
import os

import google.generativeai as genai
from dotenv import load_dotenv

from models.jd_schema import JDSchema
from models.candidate_schema import UnifiedCandidateProfile
from models.output_schema import ConversationTranscript, ConversationTurn

load_dotenv()
logger = logging.getLogger(__name__)

from utils.gemini_utils import get_model

# EMERGENCY QUOTA ADJUSTMENT: 
# Using Gemini 2.5 Flash Lite because standard Flash has hit limit 0.
MODEL_FLASH = "gemini-2.5-flash-lite" 
MODEL_LITE = "gemini-2.5-flash-lite" 

MAX_TURNS = 3 
MIN_TURNS = 2
RPM_LIMIT_DELAY = 12.0 # 60s / 5 RPM = 12s per call to be perfectly safe, or 3-4s with some overlap
# We'll use 6s to allow small bursts while staying close to the average limit.

# Shared semaphore to ensure only ONE conversation runs at a time globally
# to prevent 429 errors from parallel candidate processing.
global_convo_semaphore = asyncio.Semaphore(1)


def _build_agent_system_prompt(candidate: UnifiedCandidateProfile, jd: JDSchema) -> str:
    skills_str = ", ".join(candidate.skills[:8]) if candidate.skills else "various skills"
    comp_str = ""
    if jd.compensation:
        if jd.compensation.min and jd.compensation.max:
            comp_str = f"${jd.compensation.min:,.0f}–${jd.compensation.max:,.0f} {jd.compensation.currency}"
            if jd.compensation.equity:
                comp_str += " + equity"

    location_str = ""
    if jd.location:
        location_str = jd.location.type
        if jd.location.constraint:
            location_str += f" ({jd.location.constraint})"

    required_skills_str = ", ".join(s.skill for s in jd.required_skills[:5])

    return f"""You are a warm, professional talent acquisition specialist at an AI recruitment platform.
You are reaching out to {candidate.name} about a {jd.role_title} opportunity.

CANDIDATE BACKGROUND:
- Current title: {candidate.current_title or 'Not specified'}
- Skills: {skills_str}
- Experience: {candidate.experience_years} years
- Location: {candidate.location or 'Unknown'}

JOB DETAILS:
- Role: {jd.role_title}
- Seniority: {jd.seniority or 'Not specified'}
- Employment: {jd.employment_type or 'Full-time'}
- Location: {location_str or 'Not specified'}
- Compensation: {comp_str or 'Competitive'}
- Core stack: {required_skills_str}

YOUR CONVERSATION GOALS (cover in natural order across turns):
1. Gauge initial interest in the opportunity
2. Understand their current job satisfaction / openness to move
3. MANDATORY: Confirm availability / standard notice period (e.g. 2 weeks, 1 month)
4. MANDATORY: Ask what they look for in their next career move (Career Growth)
5. Confirm location/remote flexibility
6. Capture enthusiasm level for this specific role

STRICT RULES:
- Be concise — max 3 sentences per turn
- Be personalized — reference their background specifically
- Never repeat a question already answered by the candidate
- If candidate declines or shows strong disinterest, gracefully close the conversation
- If candidate expresses strong interest and all key signals are captured, you may close early
- Do NOT mention you are an AI agent
- Maintain a warm, conversational tone — not robotic or scripted
"""


def _build_candidate_system_prompt(candidate: UnifiedCandidateProfile, jd: JDSchema) -> str:
    """Prompt to simulate a realistic candidate response persona."""
    # Randomise interest level based on profile-JD fit signals
    interest_level = "moderately interested"
    if candidate.experience_years >= (jd.experience.min_years or 0) * 0.9 if jd.experience else True:
        interest_level = "genuinely interested but thoughtful"

    return f"""You are roleplaying as {candidate.name}, a {candidate.current_title or 'software professional'} 
with {candidate.experience_years} years of experience.

Your skills include: {', '.join(candidate.skills[:6])}.
You are located in: {candidate.location or 'unknown location'}.
You are {interest_level} in new opportunities.

PERSONA RULES:
- Respond naturally as a real candidate would — brief, realistic, and conversational
- Show realistic signals: ask clarifying questions, mention your current situation
- Vary your engagement — don't be uniformly enthusiastic or disinterested
- Mention your notice period (1-4 weeks) if asked
- Express genuine reactions to the role details
- Keep responses to 2-3 sentences
- Do NOT break character
"""


def _detect_exit(candidate_reply: str) -> tuple[bool, str]:
    """Detect if conversation should end based on candidate reply."""
    reply_lower = candidate_reply.lower()

    decline_signals = [
        "not interested", "no thanks", "not looking", "happy where i am",
        "not a good fit", "pass on this", "decline", "not for me",
        "not right now", "wrong timing"
    ]
    positive_close_signals = [
        "what are next steps", "next steps", "sounds perfect", "i'm in",
        "sign me up", "let's do it", "when can we", "schedule"
    ]

    for signal in decline_signals:
        if signal in reply_lower:
            return True, "declined"
    for signal in positive_close_signals:
        if signal in reply_lower:
            return True, "positive_close"

    return False, ""


async def run_conversation(candidate: UnifiedCandidateProfile, jd: JDSchema, api_key: str = None) -> ConversationTranscript:
    """Simulates a full exchange. Both personas use models from get_model."""
    async with global_convo_semaphore:
        agent_model = await get_model(MODEL_FLASH, api_key)
        candidate_model = await get_model(MODEL_LITE, api_key)

        agent_chat = agent_model.start_chat(history=[])
        candidate_chat = candidate_model.start_chat(history=[])

        turns: list[ConversationTurn] = []
        exit_reason = "max_turns"

        logger.info(f"Agent-Candidate interaction starting for {candidate.name} (respecting RPM)...")
        await asyncio.sleep(2.0) 
        
        agent_opening_resp = await agent_chat.send_message_async(
            "Start the conversation with a personalized outreach message. Be warm and brief."
        )
        agent_opening = agent_opening_resp.text.strip()

        for turn_num in range(MAX_TURNS):
            await asyncio.sleep(RPM_LIMIT_DELAY / 2) 

            cand_context = agent_opening if turn_num == 0 else turns[-1].agent
            candidate_reply_resp = await candidate_chat.send_message_async(
                f'The recruiter said: "{cand_context}"\nRespond naturally as the candidate.'
            )
            candidate_reply = candidate_reply_resp.text.strip()

            turns.append(ConversationTurn(
                turn=turn_num + 1,
                agent=cand_context,
                candidate=candidate_reply,
            ))

            should_exit, reason = _detect_exit(candidate_reply)
            if should_exit and turn_num >= MIN_TURNS - 1:
                exit_reason = reason
                break

            await asyncio.sleep(RPM_LIMIT_DELAY / 2)

            history_summary = "\n".join(
                f"Agent: {t.agent}\nCandidate: {t.candidate}" for t in turns
            )
            agent_reply_resp = await agent_chat.send_message_async(
                f"Conversation so far:\n{history_summary}\n\n"
                f"Send your next message to {candidate.name}. "
                f"Move naturally toward understanding their interest and availability."
            )
            agent_reply = agent_reply_resp.text.strip()

            # Store agent reply for next iteration
            turns[-1] = ConversationTurn(
                turn=turn_num + 1,
                agent=cand_context,
                candidate=candidate_reply,
            )

            # Peek — if this is the last allowed turn, close gracefully
            if turn_num == MAX_TURNS - 1:
                await asyncio.sleep(3.0)
                closing_resp = await agent_chat.send_message_async(
                    "The conversation has covered the key points. Send a brief, warm closing message."
                )
                closing = closing_resp.text.strip()
                turns.append(ConversationTurn(
                    turn=turn_num + 2,
                    agent=agent_reply,
                    candidate="[Conversation closed]",
                ))
                break
            else:
                turns.append(ConversationTurn(
                    turn=turn_num + 2,
                    agent=agent_reply,
                    candidate="",  # Will be filled next iteration
                ))
                agent_opening = agent_reply  # carry forward for next candidate turn

    # Clean up empty last turn if present
    turns = [t for t in turns if t.agent and t.candidate]

    logger.info(
        f"Conversation for {candidate.name} complete: {len(turns)} turns, exit={exit_reason}"
    )

    return ConversationTranscript(
        candidate_id=candidate.id,
        turns=turns,
        total_turns=len(turns),
        exit_reason=exit_reason,
    )
