# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2025 Your Name
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
"""Robot control Mech tool for sending HTTP commands to a robot server."""

import re
import requests
from typing import Any, Dict, Optional, Tuple

MechResponse = Tuple[str, Optional[str], Optional[Dict[str, Any]], Any, Any]

# Configuration
PREFIX = "robot-"
ALLOWED_TOOLS = [f"{PREFIX}control"]
ROBOT_SERVER_URL = "http://localhost:5000/command"
VALID_COMMANDS = {"forward", "backward", "left", "right"}

def run(**kwargs) -> Tuple[Optional[str], Optional[Dict[str, Any]], Any, Any]:
    """Run the robot control task by sending an HTTP command to the robot server."""
    prompt = kwargs["prompt"]
    tool = kwargs["tool"]
    counter_callback = kwargs.get("counter_callback", None)

    # Validate tool
    if tool not in ALLOWED_TOOLS:
        return (
            f"Tool {tool} is not in the list of supported tools.",
            None,
            None,
            None,
        )

    # Parse prompt to extract command and duration
    try:
        command, duration = parse_prompt(prompt)
        if command not in VALID_COMMANDS:
            return (
                f"Invalid command '{command}'. Supported commands: {', '.join(VALID_COMMANDS)}.",
                prompt,
                None,
                None,
            )
    except ValueError as e:
        return (
            f"Error parsing prompt: {str(e)}",
            prompt,
            None,
            None,
        )

    # Send HTTP request to robot server
    try:
        response = send_robot_command(command, duration)
        response_message = response.get("message", "No message returned")
        return (
            response_message,
            prompt,
            response,  # Include full JSON response as metadata
            None,
        )
    except requests.RequestException as e:
        return (
            f"Error communicating with robot server: {str(e)}",
            prompt,
            None,
            None,
        )

def parse_prompt(prompt: str) -> Tuple[str, float]:
    """Parse the prompt to extract command and duration."""
    # Expected format: "move forward 2 seconds" or "turn left 1.5"
    pattern = r"^(?:move\s+)?(\w+)\s+(\d*\.?\d*)\s*(?:seconds)?$"
    match = re.match(pattern, prompt.lower().strip())
    if not match:
        raise ValueError("Prompt must be in format '<command> <duration> [seconds]', e.g., 'move forward 2' or 'turn left 1.5'")
    
    command, duration_str = match.groups()
    try:
        duration = float(duration_str)
        if duration <= 0:
            raise ValueError("Duration must be positive")
        return command, duration
    except ValueError as e:
        raise ValueError(f"Invalid duration: {str(e)}")

def send_robot_command(command: str, duration: float) -> Dict[str, Any]:
    """Send an HTTP POST request to the robot server."""
    data = {
        "command": command,
        "duration": duration
    }
    response = requests.post(ROBOT_SERVER_URL, json=data, timeout=5)
    response.raise_for_status()  # Raise exception for 4xx/5xx status codes
    return response.json()