import os
from mech_client.interact import interact
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def call_openai_mech(prompt: str, tool: str) -> str:
    """Send a prompt to the OpenAI Mech and return the response."""
    try:
        # Mech configuration (replace with actual values from Mech Marketplace)
        mech_address = "0x1234567890abcdef1234567890abcdef12345678"  # Placeholder
        chain_config = "gnosis"
        wallet_address = os.getenv("WALLET_ADDRESS")
        private_key = os.getenv("PRIVATE_KEY")

        # Send request to the Mech
        result = interact(
            prompt=prompt,
            tool=tool,
            chain_config=chain_config,
            mech_address=mech_address,
            wallet_address=wallet_address,
            private_key=private_key
        )

        # Extract response (interact returns a tuple: response, prompt, metadata, callback, keys)
        response = result[0] if isinstance(result, tuple) else result
        return response
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Example prompt and tool
    demo_prompt = "Generate a greeting message for a new user."
    demo_tool = "openai-gpt-4o-2024-08-06"  # Must match ALLOWED_TOOLS in Mech script

    # Call the Mech
    response = call_openai_mech(demo_prompt, demo_tool)
    print(f"Prompt: {demo_prompt}")
    print(f"Response: {response}")