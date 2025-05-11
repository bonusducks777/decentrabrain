import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load the Mech script (assume it's saved as mech.py in the same directory)
from openai_request import run, OpenAIClientManager, DEFAULT_OPENAI_SETTINGS

# Load environment variables
load_dotenv()

def call_mech_locally(prompt: str, tool: str) -> str:
    """Call the Mech's run function locally."""
    try:
        # Mock KeyChain object (simplified for local testing)
        class MockKeyChain:
            def __init__(self):
                self.keys = {
                    "openai": os.getenv("OPENAI_API_KEY"),
                    "anthropic": None,
                    "google_api_key": None,
                    "openrouter": None
                }
                self.retries = {"openai": 3, "anthropic": 3, "google_api_key": 3, "openrouter": 3}

            def __getitem__(self, key: str) -> str:
                return self.keys[key]

            def max_retries(self) -> Dict[str, int]:
                return self.retries

            def rotate(self, service: str) -> None:
                pass  # No rotation for local testing

        # Prepare arguments for the run function
        api_keys = MockKeyChain()
        kwargs = {
            "prompt": prompt,
            "tool": tool,
            "api_keys": api_keys,
            "max_tokens": DEFAULT_OPENAI_SETTINGS["max_tokens"],
            "temperature": DEFAULT_OPENAI_SETTINGS["temperature"],
            "counter_callback": None
        }

        # Call the run function
        result = run(**kwargs)
        response = result[0]  # Extract the response from the tuple
        return response
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Example prompt and tool
    demo_prompt = "Generate a greeting message for a new user."
    demo_tool = "openai-gpt-4o-2024-08-06"

    # Call the Mech locally
    response = call_mech_locally(demo_prompt, demo_tool)
    print(f"Prompt: {demo_prompt}")
    print(f"Response: {response}")