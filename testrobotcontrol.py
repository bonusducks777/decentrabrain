from robot_control_mech import run

kwargs = {
    "prompt": "move forward 2 seconds",
    "tool": "robot-control",
    "counter_callback": None
}
result = run(**kwargs)
print(result[0])  # Prints the response