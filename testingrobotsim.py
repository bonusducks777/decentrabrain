# Example client code
import requests

def send_robot_command(command, duration):
    url = "http://localhost:5000/command"
    data = {
        "command": command,
        "duration": duration
    }
    response = requests.post(url, json=data)
    return response.json()

# Move forward for 2 seconds
result = send_robot_command("forward", 2.0)
print(result)