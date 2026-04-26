import asyncio
import logging
import os

from dotenv import load_dotenv

from typing import Optional, Callable
from models.jd_schema import JDSchema
from models.candidate_schema import UnifiedCandidateProfile
from models.output_schema import ConversationTranscript, ConversationTurn
from utils.llm_utils import generate_content

load_dotenv()
logger = logging.getLogger(__name__)

# EMERGENCY QUOTA ADJUSTMENT: 
# Using Gemini 2.5 Flash Lite because standard Flash has hit limit 0.
MODEL_FLASH = "gemini-2.5-flash-lite" 
MODEL_LITE = "gemini-2.5-flash-lite" 

MAX_TURNS = 3 
MIN_TURNS = 2
RPM_LIMIT_DELAY = 12.0 # 60s / 5 RPM = 12s per call to be perfectly safe

# Shared semaphore to ensure only ONE conversation runs at a time globally
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
    reply_lower = candidate_reply.lower()
    decline_signals = ["not interested", "no thanks", "not looking", "happy where i am", "not a good fit"]
    positive_close_signals = ["what are next steps", "sounds perfect", "let's do it"]

    for signal in decline_signals:
        if signal in reply_lower: return True, "declined"
    for signal in positive_close_signals:
        if signal in reply_lower: return True, "positive_close"
    return False, ""

async def run_conversation(
    candidate: UnifiedCandidateProfile, 
    jd: JDSchema, 
    api_key: str = None, 
    provider: str = "gemini", 
    model: str = None,
    turn_callback: Optional[Callable] = None
) -> ConversationTranscript:
    """Simulates a full exchange using a stateless approach for multiple provider support."""
    async with global_convo_semaphore:
        agent_sys = _build_agent_system_prompt(candidate, jd)
        cand_sys = _build_candidate_system_prompt(candidate, jd)

        turns: list[ConversationTurn] = []
        exit_reason = "max_turns"
        
        # 1. Recruiter Opening
        await asyncio.sleep(1.0)
        agent_msg = await generate_content(
            "Start the conversation with a personalized outreach message. Be warm and brief.",
            provider=provider, model_name=model or MODEL_FLASH, api_key=api_key,
            system_instruction=agent_sys, temperature=0.7
        )

        for turn_num in range(MAX_TURNS):
            await asyncio.sleep(RPM_LIMIT_DELAY / 2)
            
            # Candidate Reply
            cand_msg = await generate_content(
                f'The recruiter said: "{agent_msg}". Respond naturally.',
                provider=provider, model_name=model or MODEL_LITE, api_key=api_key,
                system_instruction=cand_sys, temperature=0.8
            )
            
            turn = ConversationTurn(turn=turn_num + 1, agent=agent_msg, candidate=cand_msg)
            turns.append(turn)
            
            if turn_callback:
                try:
                    # If it's a coroutine, await it
                    if asyncio.iscoroutinefunction(turn_callback):
                        await turn_callback(turn)
                    else:
                        turn_callback(turn)
                except Exception as e:
                    logger.warning(f"Turn callback failed: {e}")

            should_exit, reason = _detect_exit(cand_msg)
            if should_exit:
                exit_reason = reason
                break
                
            if turn_num == MAX_TURNS - 1:
                break

            await asyncio.sleep(RPM_LIMIT_DELAY / 2)
            
            # Recruiter Follow-up
            history = "\n".join([f"Agent: {t.agent}\nCandidate: {t.candidate}" for t in turns])
            agent_msg = await generate_content(
                f"Conversation history:\n{history}\n\nSend your next follow-up message.",
                provider=provider, model_name=MODEL_FLASH, api_key=api_key,
                system_instruction=agent_sys, temperature=0.7
            )

        return ConversationTranscript(
            candidate_id=candidate.id,
            turns=turns,
            total_turns=len(turns),
            exit_reason=exit_reason,
        )
