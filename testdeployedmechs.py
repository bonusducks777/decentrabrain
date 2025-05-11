import os
from mech_client.interact import interact
from dotenv import load_dotenv

load_dotenv()

def send_mech_request(mech_address: str, tool: str, prompt: str, chain_config: str = "gnosis") -> str:
    """Send a request to a Mech and return the response."""
    try:
        result = interact(
            prompt=prompt,
            tool=tool,
            chain_config=chain_config,
            mech_address=mech_address,
            wallet_address=os.getenv("WALLET_ADDRESS"),
            private_key=os.getenv("PRIVATE_KEY")
        )
        return result[0] if isinstance(result, tuple) else result
    except Exception as e:
        return f"Error: {str(e)}"

def parse_openai_response(response: str) -> list[str]:
    """Parse OpenAI Mech response into a list of commands."""
    return [cmd.strip() for cmd in response.split(",") if cmd.strip()]

def test_system():
    """Test the coordinator-like interaction between OpenAI and robot control Mechs."""
    # Mech configuration (replace with actual addresses)
    openai_mech_address = "0x1234567890abcdef1234567890abcdef12345678"  # Placeholder
    robot_mech_address = "0xabcdef1234567890abcdef1234567890abcdef12"  # Placeholder
    openai_tool = "openai-gpt-4o-2024-08-06"
    robot_tool = "robot-control"

    # Step 1: Send user command to OpenAI Mech
    user_command = "Navigate to the kitchen"
    openai_prompt = f"Generate a sequence of robot commands to {user_command}, avoiding obstacles. Use format: 'move forward 2 seconds, turn left 1.5 seconds'."
    print(f"Sending to OpenAI Mech: {openai_prompt}")
    openai_response = send_mech_request(openai_mech_address, openai_tool, openai_prompt)
    print(f"OpenAI Response: {openai_response}")

    if "Error" in openai_response:
        print("Failed to get OpenAI response")
        return

    # Step 2: Parse commands
    commands = parse_openai_response(openai_response)
    if not commands:
        print("No valid commands received")
        return
    print(f"Parsed Commands: {commands}")

    # Step 3: Send each command to Robot Control Mech
    for command in commands:
        print(f"Sending to Robot Control Mech: {command}")
        robot_response = send_mech_request(robot_mech_address, robot_tool, command)
        print(f"Robot Response: {robot_response}")

        # Step 4: Check for feedback
        if "error" in robot_response.lower() or "obstacle" in robot_response.lower():
            print("Issue detected; requesting new path")
            new_path_prompt = f"Obstacle detected during '{command}' while navigating to the kitchen. Suggest a new sequence of commands."
            new_openai_response = send_mech_request(openai_mech_address, openai_tool, new_path_prompt)
            print(f"New OpenAI Response: {new_openai_response}")
            if "Error" not in new_openai_response:
                new_commands = parse_openai_response(new_openai_response)
                commands.extend(new_commands)
                print(f"New Commands: {new_commands}")

if __name__ == "__main__":
    test_system()