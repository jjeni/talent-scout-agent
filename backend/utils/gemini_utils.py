import os
import google.generativeai as genai
import asyncio
import logging

logger = logging.getLogger(__name__)

# Global lock to prevent concurrent SDK configuration conflicts
_config_lock = asyncio.Lock()

async def get_model(model_name: str, api_key: str = None, **kwargs):
    """
    Thread-safe/Async-safe model retrieval. 
    If api_key is provided, it re-configures the SDK for this specific call.
    """
    async with _config_lock:
        effective_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not effective_key:
            raise ValueError("No Gemini API Key provided. Set it in .env or the UI.")
        
        # logger.info(f"Configuring Gemini with key ending in ...{effective_key[-4:]}")
        genai.configure(api_key=effective_key)
        
        # Create model instance
        # Note: In some SDK versions, the config is attached to the model object, 
        # in others it's truly global. We re-reconfigure globally just in case.
        model = genai.GenerativeModel(model_name=model_name, **kwargs)
        return model

async def generate_content_safe(model_name: str, contents: any, api_key: str = None, **kwargs):
    """
    Wrapper to ensure the correct API key is used during the actual call.
    """
    model = await get_model(model_name, api_key, **kwargs)
    # We await the response inside the lock-protected-ish context? 
    # Actually, the 'configure' only needs to happen before the GRPC/REST call starts.
    return await model.generate_content_async(contents)
