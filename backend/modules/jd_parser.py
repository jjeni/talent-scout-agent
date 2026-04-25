import asyncio
import json
import logging
import os
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

from models.jd_schema import JDSchema
from utils.llm_utils import generate_content

# EMERGENCY QUOTA ADJUSTMENT: Using Flash Lite
MODEL_NAME = "gemini-2.5-flash-lite"

load_dotenv()
logger = logging.getLogger(__name__)

JD_PARSE_PROMPT = """
You are an expert HR analyst and recruiter. Your task is to carefully parse the provided job description
and extract all key information into a structured JSON object.

Extract the following fields:
- role_title (string): The job title
- seniority (string): One of "Junior", "Mid", "Senior", "Staff", "Lead", "Principal", "Director", or null
- employment_type (string): "Full-time", "Part-time", "Contract", "Freelance", or null
- location (object):
    - type: "Remote", "Hybrid", or "On-site"
    - city: city name or null
    - country: country or null
    - constraint: any timezone or location constraint string, or null
- experience (object):
    - min_years: minimum years required (number or null)
    - preferred_years: preferred years (number or null)
- required_skills (array of objects):
    - skill: skill name (string)
    - importance: 0.0-1.0 float (1.0 = absolutely required, 0.7 = strongly preferred)
- nice_to_have_skills (array of strings): bonus skills mentioned
- education (object):
    - degree_level: "High School", "Associate's", "Bachelor's", "Master's", "PhD", "Any", or null
    - field: field of study or null
    - is_strict: true if education is a hard requirement, false if flexible
- compensation (object):
    - min: minimum salary as number or null
    - max: maximum salary as number or null
    - currency: "USD", "EUR", "GBP", etc.
    - equity: true if equity/stock options mentioned
- urgency: "immediate", "within_month", or "flexible"
- confidence_flags (object): for ambiguous fields, include the field name and your confidence 0-1

Return ONLY valid JSON matching this exact structure. If a field cannot be determined, use null.
Do NOT include any markdown or explanation — only the JSON object.
"""


async def parse_jd(jd_text: str, api_key: str = None, provider: str = "gemini", model: str = None) -> JDSchema:
    """Uses LLM to extract structured fields from JD text."""
    if not jd_text or len(jd_text.strip()) < 20:
        raise ValueError("Job description text is too short or empty.")

    prompt = f"{JD_PARSE_PROMPT}\n\n--- JOB DESCRIPTION ---\n{jd_text}\n--- END JD ---"

    await asyncio.sleep(2.0) # Rate limit check
    try:
        # 5. Call LLM
        raw_json = await generate_content(
            prompt=prompt,
            provider=provider,
            model_name=model or MODEL_NAME,
            api_key=api_key,
            response_mime_type="application/json",
            temperature=0.1
        )

        # Strip markdown code fences if present
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]
            raw_json = raw_json.strip()

        parsed = json.loads(raw_json)
        jd = JDSchema(**parsed)
        jd.raw_text = jd_text
        logger.info(f"JD parsed successfully: role='{jd.role_title}', skills={len(jd.required_skills)}")
        return jd

    except json.JSONDecodeError as e:
        logger.error(f"JD Parser JSON decode error: {e}")
        # Fallback: return minimal schema
        return JDSchema(role_title="Unknown Role", raw_text=jd_text)
    except Exception as e:
        logger.error(f"JD Parser error: {e}")
        raise


def parse_jd_sync(jd_text: str) -> JDSchema:
    """Synchronous wrapper for parse_jd (for non-async contexts)."""
    import asyncio
    return asyncio.run(parse_jd(jd_text))
