# backend/app/agents/ai_clients.py
import json
from openai import OpenAI
import anthropic
from app.core.config import settings

# 1. Define the standard interface for all clients
class LLMClient:
    def execute(self, system_prompt: str, user_prompt_json: dict) -> str:
        """The standard method every client must implement."""
        raise NotImplementedError

# 2. Create the OpenAI-specific client
class OpenAIClient(LLMClient):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in the environment.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def execute(self, system_prompt: str, user_prompt_json: dict) -> str:
        response = self.client.chat.completions.create(
            model=settings.AI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt_json, indent=2)}
            ],
            max_tokens=settings.AI_MAX_TOKENS, # Use the dynamic setting
            temperature=settings.AI_TEMPERATURE
        )
        return response.choices[0].message.content

# 3. Create the Anthropic-specific client
class AnthropicClient(LLMClient):
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set in the environment.")
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def execute(self, system_prompt: str, user_prompt_json: dict) -> str:
        response = self.client.messages.create(
            model=settings.AI_MODEL,
            system=system_prompt,
            messages=[
                {"role": "user", "content": json.dumps(user_prompt_json, indent=2)}
            ],
            max_tokens=settings.AI_MAX_TOKENS, # Use the dynamic setting
            temperature=settings.AI_TEMPERATURE
        )
        # Note: Anthropic doesn't have a guaranteed JSON mode yet, so we still parse
        return response.content[0].text

# 4. Create the factory function that chooses the right client
def get_client() -> LLMClient:
    """Reads the AI_PROVIDER from settings and returns the correct client instance."""
    provider = settings.AI_PROVIDER.lower()
    if provider == "openai":
        print("🤖 Using OpenAI Client")
        return OpenAIClient()
    elif provider == "anthropic":
        print("🤖 Using Anthropic (Claude) Client")
        return AnthropicClient()
    else:
        raise ValueError(f"Unsupported AI_PROVIDER: {provider}. Choose 'openai' or 'anthropic'.")