import os
from dotenv import load_dotenv

load_dotenv(override=True)

import httpx
import json
import logging
from typing import Optional, Dict, Any, List
from app.models import ModelType, CompletionCriteria

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_API_URL = os.environ.get("API_URL", "https://api.groq.com/openai/v1/chat/completions")
API_KEY = os.environ.get("API_KEY")

class LLMService:

    def __init__(self):
        self.api_key = os.environ.get("API_KEY")
        if not self.api_key:
            logger.warning("API_KEY not found in environment variables")

    
    async def call_llm(self, model: ModelType, prompt: str, system_prompt: str = "You are a helpful assistant.") -> Dict[str, Any]:
        """
        Calls the LLM API.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if not prompt or not prompt.strip():
            logger.warning("Attempted to call LLM with empty prompt. Using fallback.")
            prompt = "No prompt provided. Please acknowledge."

        payload = {
            "model": model.value,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        logger.info(f"Calling Groq API: Model={model.value}, PromptLength={len(prompt)}")
        logger.debug(f"Payload: {json.dumps(payload)}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(LLM_API_URL, headers=headers, json=payload, timeout=60.0)
                if response.status_code >= 400:
                    logger.error(f"Groq Error Body: {response.text}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"LLM Call failed: {e}")
            raise

    async def validate_output(self, output: str, criteria: CompletionCriteria) -> bool:
        """
        Validates the output based on criteria.
        """
        if criteria.type == "contains":
            if not criteria.value:
                return True
            # Support multiple comma-separated terms — ALL must appear in the output
            terms = [t.strip() for t in criteria.value.split(",") if t.strip()]
            output_lower = output.lower()
            logger.info(f"Validating 'contains': Terms={terms} in Output='{output[:80]}...'?")
            found = all(term.lower() in output_lower for term in terms)
            logger.info(f"Result: {found}")
            return found
            
        elif criteria.type == "json_valid":
            try:
                json.loads(output)
                return True
            except:
                return False
                
        elif criteria.type == "llm_judge":
            # Use a cheaper model (or the same one) to judge
            judge_prompt = f"""
            Task: Evaluate if the following text meets the requirement.
            Requirement: {criteria.instruction}
            
            Text to evaluate:
            {output}
            
            Answer ONLY with 'YES' or 'NO'.
            """
            try:
                # Using Llama 3.1 8B as judge for speed
                response = await self.call_llm(ModelType.LLAMA_3_1_8B, judge_prompt, system_prompt="You are an impartial judge.")
                answer = response['choices'][0]['message']['content'].strip().upper()
                return "YES" in answer
            except Exception as e:
                logger.error(f"Judge failed: {e}")
                return False # Fail safe
                
        return True # Default pass if no criteria
