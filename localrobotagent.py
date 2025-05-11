import logging
import os
from typing import List, Optional
from aea.skills.base import SkillContext
from aea.skills.behaviours import TickerBehaviour
from openai_request import run as openai_run
from robot_control_mech import run as robot_run
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LocalCoordinator")

class LocalCoordinatorBehaviour(TickerBehaviour):
    """Local coordinator behaviour to interact with OpenAI and Robot Control Mechs."""

    def __init__(self, **kwargs):
        super().__init__(tick_interval=10.0, **kwargs)  # Check every 10 seconds
        self.openai_tool = "openai-gpt-4o-2024-08-06"
        self.robot_tool = "robot-control"
        self.api_keys = {"openai": os.getenv("OPENAI_API_KEY", "mock-openai-key")}

    def setup(self) -> None:
        """Set up the behaviour."""
        logger.info("LocalCoordinatorBehaviour setup")

    def act(self) -> None:
        """Run the behaviour."""
        user_command = "Navigate to the kitchen"
        logger.info(f"Processing user command: {user_command}")

        # Step 1: Send request to OpenAI Mech to generate robot commands
        openai_prompt = f"Generate a sequence of robot commands to {user_command}, avoiding obstacles. Use format: 'move forward 2 seconds, turn left 1.5 seconds'."
        openai_response = self._send_openai_request(prompt=openai_prompt)

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
            robot_response = self._send_robot_request(prompt=command)
            if robot_response is None:
                logger.error(f"Failed to execute command: {command}")
                continue
            logger.info(f"Robot response: {robot_response}")

            # Step 4: Check for feedback (e.g., obstacles)
            if "error" in robot_response.lower() or "obstacle" in robot_response.lower():
                logger.info("Issue detected; requesting new path")
                new_path_prompt = f"Obstacle detected during '{command}' while navigating to the kitchen. Suggest a new sequence of commands."
                new_openai_response = self._send_openai_request(prompt=new_path_prompt)
                if new_openai_response:
                    new_commands = self._parse_openai_response(new_openai_response)
                    commands.extend(new_commands)  # Add new commands to the queue

    def _send_openai_request(self, prompt: str) -> Optional[str]:
        """Send a request to the OpenAI Mech."""
        try:
            result = openai_run(
                prompt=prompt,
                tool=self.openai_tool,
                api_keys=self.api_keys,
                max_tokens=500,
                temperature=0.7
            )
            response = result[0] if isinstance(result, tuple) else result
            logger.info(f"OpenAI Mech response for prompt '{prompt}': {response}")
            return response
        except Exception as e:
            logger.error(f"Error interacting with OpenAI Mech: {str(e)}")
            return None

    def _send_robot_request(self, prompt: str) -> Optional[str]:
        """Send a request to the Robot Control Mech."""
        try:
            result = robot_run(prompt=prompt, tool=self.robot_tool)
            response = result[0] if isinstance(result, tuple) else result
            logger.info(f"Robot Control Mech response for prompt '{prompt}': {response}")
            return response
        except Exception as e:
            logger.error(f"Error interacting with Robot Control Mech: {str(e)}")
            return None

    def _parse_openai_response(self, response: str) -> List[str]:
        """Parse the OpenAI Mech response into a list of robot commands."""
        try:
            commands = [cmd.strip() for cmd in response.split(",") if cmd.strip()]
            return commands
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {str(e)}")
            return []

    def teardown(self) -> None:
        """Tear down the behaviour."""
        logger.info("LocalCoordinatorBehaviour teardown")

def register_skill(context: SkillContext):
    """Register the coordinator behaviour with the skill."""
    context.behaviours.register(LocalCoordinatorBehaviour(name="local_coordinator_behaviour"))