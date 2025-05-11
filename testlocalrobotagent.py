import logging
from localrobotagent import LocalCoordinatorBehaviour

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestLocalCoordinator")

# Mock SkillContext for standalone testing
class MockSkillContext:
    def __init__(self):
        self.behaviours = MockBehaviours()

class MockBehaviours:
    def register(self, behaviour):
        logger.info(f"Registered behaviour: {behaviour.name}")

class TestLocalCoordinator:
    def __init__(self, user_command: str):
        self.behaviour = LocalCoordinatorBehaviour()
        self.behaviour.context = MockSkillContext()
        self.user_command = user_command

    def run_test(self):
        logger.info("Starting local coordinator test")
        self.behaviour.setup()
        
        # Override act to use the provided user command
        original_act = self.behaviour.act
        def patched_act():
            logger.info(f"Processing user command: {self.user_command}")
            openai_prompt = f"Generate a sequence of robot commands to {self.user_command}, avoiding obstacles. Use format: 'move forward 2 seconds, turn left 1.5 seconds'."
            openai_response = self.behaviour._send_openai_request(prompt=openai_prompt)
            if openai_response:
                commands = self.behaviour._parse_openai_response(openai_response)
                for command in commands:
                    robot_response = self.behaviour._send_robot_request(prompt=command)
                    logger.info(f"Robot response: {robot_response}")
                    # Simulate obstacle for testing
                    if "forward" in command:
                        logger.info("Simulating obstacle detection")
                        new_path_prompt = f"Obstacle detected during '{command}' while navigating to {self.user_command}. Suggest a new sequence of commands."
                        new_openai_response = self.behaviour._send_openai_request(prompt=new_path_prompt)
                        if new_openai_response:
                            new_commands = self.behaviour._parse_openai_response(new_openai_response)
                            for new_command in new_commands:
                                robot_response = self.behaviour._send_robot_request(prompt=new_command)
                                logger.info(f"Robot response for new command: {robot_response}")
        
        self.behaviour.act = patched_act
        self.behaviour.act()
        self.behaviour.teardown()

if __name__ == "__main__":
    test_command = "Navigate to the kitchen"
    coordinator_test = TestLocalCoordinator(user_command=test_command)
    coordinator_test.run_test()