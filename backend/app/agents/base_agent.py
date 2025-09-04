# backend/app/agents/base_agent.py
from app.agents.ai_clients import LLMClient
import traceback

class AIAgent:
    """A generic AI agent that is given a client and a role."""

    def __init__(self, system_prompt: str, client: LLMClient):
        """Initializes the agent with a system prompt and a pre-configured client."""
        self.system_prompt = system_prompt
        self.client = client

    def execute_task(self, user_prompt_json: dict) -> str:
        """Executes a task by delegating to the provided client."""
        print(f"--- Delegating task to AIAgent using {self.client.__class__.__name__} ---")
        
        try:
            # CORRECTED: The call to self.client.execute now only passes the prompts.
            # The client adapter itself is responsible for getting the model and temperature
            # from the settings file when it makes the actual API call.
            response_text = self.client.execute(
                system_prompt=self.system_prompt,
                user_prompt_json=user_prompt_json
            )
            print("--- Agent responded ---")
            return response_text
        except Exception as e:
            print(f"❌ AI Client Error: {e}")
            traceback.print_exc()
            return "{}" # Return empty JSON on error