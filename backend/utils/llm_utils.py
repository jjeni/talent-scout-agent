import os
import google.generativeai as genai
import asyncio
import logging
import httpx
import json

logger = logging.getLogger(__name__)

# Global lock to prevent concurrent SDK configuration conflicts (for Gemini SDK)
_config_lock = asyncio.Lock()

async def generate_content(
    prompt: str, 
    provider: str = "gemini", 
    model_name: str = "gemini-1.5-flash",
    api_key: str = None,
    system_instruction: str = None,
    response_mime_type: str = "text/plain",
    temperature: float = 0.7
):
    """
    Unified LLM entry point for both native Gemini and OpenRouter.
    """
    if provider == "gemini":
        return await _generate_gemini(prompt, model_name, api_key, system_instruction, response_mime_type, temperature)
    elif provider == "openrouter":
        return await _generate_openrouter(prompt, model_name, api_key, system_instruction, response_mime_type, temperature)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

async def _generate_gemini(prompt, model_name, api_key, system, mime, temp):
    async with _config_lock:
        effective_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not effective_key:
            raise ValueError("No Gemini API Key provided.")
        
        genai.configure(api_key=effective_key)
        
        # Normalize model name: native Gemini SDK usually expects "models/model-id"
        actual_model = model_name
        if "/" not in actual_model and not actual_model.startswith("models/"):
            actual_model = f"models/{actual_model}"

        model = genai.GenerativeModel(
            model_name=actual_model,
            system_instruction=system,
            generation_config={"response_mime_type": mime, "temperature": temp}
        )
        
        # We use a wrapper style to handle errors or specific response structures
        response = await model.generate_content_async(prompt)
        return response.text

async def _generate_openrouter(prompt, model_name, api_key, system, mime, temp):
    effective_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not effective_key:
        logger.error(f"OpenRouter Error: No key found. api_key={api_key}, env_key={os.environ.get('OPENROUTER_API_KEY') is not None}")
        raise ValueError("No OpenRouter API Key provided.")

    # Intelligent Model Mapping for Free Tier
    actual_model = model_name
    if "gemini" in model_name.lower():
        # Use Gemma 3 as fallback since Gemini Lite might have ID issues or limited access
        actual_model = "google/gemma-3-27b-it:free"
    elif "flash" in model_name.lower() or "lite" in model_name.lower():
        actual_model = "google/gemma-3-27b-it:free"
    elif "pro" in model_name.lower() or "oss" in model_name.lower():
        # High capacity free model
        actual_model = "openai/gpt-oss-120b:free"
    
    # If the user passes a full path (e.g. org/model:free), we use it as is
    if "/" in model_name:
        actual_model = model_name

    actual_messages = []
    if system:
        # Consolidate system into user msg for better free model compatibility
        actual_messages.append({"role": "user", "content": f"INSTRUCTIONS:\n{system}\n\nINPUT:\n{prompt}"})
    else:
        actual_messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {effective_key}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "TalentScout AI Agent",
        "Content-Type": "application/json"
    }

    payload = {
        "model": actual_model,
        "messages": actual_messages,
        "temperature": temp,
    }

    # response_format is problematic on many free models, keep it disabled
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]

                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        logger.warning(f"OpenRouter Rate Limit (429). Waiting 5s before retry {attempt+1}...")
                        await asyncio.sleep(5.0)
                        continue
                    raise Exception("OpenRouter Rate Limit: Please wait a minute and try again.")
                
                error_data = response.json()
                msg = error_data.get('error', {}).get('message', 'Unknown error')
                
                if attempt < max_retries - 1 and ("Provider returned error" in msg or "overloaded" in msg.lower()):
                    logger.warning(f"OpenRouter attempt {attempt+1} failed ({msg}). Retrying in 3s...")
                    await asyncio.sleep(3.0)
                    continue
                
                raise Exception(f"OpenRouter Error: {msg}")
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"OpenRouter network/request error: {e}. Retrying...")
                await asyncio.sleep(2.0)
                continue
            raise e
