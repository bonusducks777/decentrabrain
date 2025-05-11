import json
import logging
import os
from typing import List, Optional, Tuple
from aea.skills.base import SkillContext
from aea.skills.behaviours import TickerBehaviour
from mech_client.interact import interact
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CoordinatorSkill")

class CoordinatorBehaviour(TickerBehaviour):
    """Behaviour for the Olas coordinator agent to interact with OpenAI and robot control Mechs."""

    def __init__(self, **kwargs):
        super().__init__(tick_interval=10.0, **kwargs)  # Check every 10 seconds
        self.chain_config = "gnosis"
        self.rpc_url = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
        self.wallet_address = os.getenv("WALLET_ADDRESS")
        self.private_key = os.getenv("PRIVATE_KEY")
        self.web3 = Web3(Web3.HTTPStatusProvider(self.rpc_url))

        # OpenAI Mech configuration (replace with actual values from Mech Marketplace)
        self.openai_mech_address = "0x1234567890abcdef1234567890abcdef12345678"  # Placeholder
        self.openai_tool = "openai-gpt-4o-2024-08-06"

        # Robot Control Mech configuration (replace with actual values after deployment)
        self.robot_mech_address = "0xabcdef1234567890abcdef1234567890abcdef12"  # Placeholder
        self.robot_tool = "robot-control"

    def setup(self) -> None:
        """Set up the behaviour."""
        logger.info("CoordinatorBehaviour setup")
        if not self.web3.is_connected():
            logger.error("Failed to connect to blockchain")
            return
        logger.info(f"Connected to {self.chain_config} at {self.rpc_url}")

    def act(self) -> None:
        """Run the behaviour."""
        # Example user command (replace with dynamic input, e.g., from a queue or API)
        user_command = "Navigate to the kitchen"
        logger.info(f"Processing user command: {user_command}")

        # Step 1: Send request to OpenAI Mech to generate robot commands
        openai_prompt = f"Generate a sequence of robot commands to {user_command}, avoiding obstacles. Use format: 'move forward 2 seconds, turn left 1.5 seconds'."
        openai_response = self._send_mech_request(
            mech_address=self.openai_mech_address,
            tool=self.openai_tool,
            prompt=openai_prompt
        )

        if openai_response is None:
            logger.error("Failed to get response from OpenAI Mech")
            return

        # Step 2: Parse OpenAI Mech response into individual commands
        commands = self._parse_openai_response(openai_response)
        if not commands:
            logger.error("No valid commands received from OpenAI Mech")
            return

        # Step 3: Send each command to Robot Control Mech
        for command in commands:
            robot_response = self._send_mech_request(
                mech_address=self.robot_mech_address,
                tool=self.robot_tool,
                prompt=command
            )
            if robot_response is None:
                logger.error(f"Failed to execute command: {command}")
                continue
            logger.info(f"Robot response: {robot_response}")

            # Step 4: Check for feedback (e.g., obstacles)
            if "error" in robot_response.lower() or "obstacle" in robot_response.lower():
                logger.info("Issue detected; requesting new path")
                new_path_prompt = f"Obstacle detected during '{command}' while navigating to the kitchen. Suggest a new sequence of commands."
                new_openai_response = self._send_mech_request(
                    mech_address=self.openai_mech_address,
                    tool=self.openai_tool,
                    prompt=new_path_prompt
                )
                if new_openai_response:
                    new_commands = self._parse_openai_response(new_openai_response)
                    commands.extend(new_commands)  # Add new commands to the queue

    def _send_mech_request(self, mech_address: str, tool: str, prompt: str) -> Optional[str]:
        """Send a request to a Mech and return the response."""
        try:
            result = interact(
                prompt=prompt,
                tool=tool,
                chain_config=self.chain_config,
                mech_address=mech_address,
                wallet_address=self.wallet_address,
                private_key=self.private_key
            )
            response = result[0] if isinstance(result, tuple) else result
            logger.info(f"Mech response for prompt '{prompt}': {response}")
            return response
        except Exception as e:
            logger.error(f"Error interacting with Mech {mech_address}: {str(e)}")
            return None

    def _parse_openai_response(self, response: str) -> List[str]:
        """Parse the OpenAI Mech response into a list of robot commands."""
        try:
            # Example response: "move forward 2 seconds, turn left 1.5 seconds, move forward 1 second"
            commands = [cmd.strip() for cmd in response.split(",") if cmd.strip()]
            return commands
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {str(e)}")
            return []

    def teardown(self) -> None:
        """Tear down the behaviour."""
        logger.info("CoordinatorBehaviour teardown")

def register_skill(context: SkillContext):
    """Register the coordinator behaviour with the skill."""
    context.behaviours.register(CoordinatorBehaviour(name="coordinator_behaviour"))