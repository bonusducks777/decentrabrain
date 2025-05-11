import tkinter as tk
from tkinter import Canvas, Frame, Label, Button
import threading
import time
import math
import random
from flask import Flask, request, jsonify
import logging

# Disable Flask's default logging to keep the console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class OptimizedRobotSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Simulator")
        self.root.geometry("800x700")
        
        # Robot properties
        self.robot_x = 250  # Starting X position
        self.robot_y = 250  # Starting Y position
        self.robot_angle = 0  # 0 degrees = facing right/east
        self.robot_size = 20  # Size of the robot
        self.robot_speed = 50  # Pixels per second
        self.robot_turn_speed = 90  # Degrees per second
        
        # Map properties
        self.map_width = 600
        self.map_height = 500
        self.grid_size = 50
        
        # Command queue and timing
        self.command_queue = []
        self.executing_command = False
        self.server_running = False
        self.path_points = []  # Store robot's path
        self.command_start_time = 0  # Track when command started
        self.command_duration = 0  # Current command duration
        
        # Colors
        self.colors = {
            "bg": "#f0f0ff",
            "map_bg": "#e8f4ff",
            "grid": "#d0d0ff",
            "border": "#8080c0",
            "robot": "#5050a0",
            "direction": "#ff5050",
            "path": "#ffc0c0",
            "tree": "#60a060",
            "house": "#a06060",
            "grass": "#c0ffc0",
            "button": "#a0d0ff",
            "title": "#5050a0",
            "text": "#505050"
        }
        
        # Create UI
        self.setup_ui()
        
        # Add decorative elements
        self.add_decorations()
        
        # Start HTTP server in a separate thread
        self.start_server()
        
        # Start command processing
        self.process_commands()
        
        # Create test client
        self.create_test_client()
        
    def setup_ui(self):
        # Main frame
        main_frame = Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title label
        title_label = Label(main_frame, text="🤖 Robot Simulator 🤖", 
                           font=("Arial", 16, "bold"), bg=self.colors["bg"], fg=self.colors["title"])
        title_label.pack(pady=5)
        
        # Status label
        self.status_label = Label(main_frame, text="Starting simulator...", 
                                 bg=self.colors["bg"], fg=self.colors["text"], font=("Arial", 10))
        self.status_label.pack(pady=2)
        
        # Command history label
        self.command_label = Label(main_frame, text="Waiting for commands...", 
                                  bg=self.colors["bg"], fg=self.colors["text"], font=("Arial", 10))
        self.command_label.pack(pady=2)
        
        # Position label
        self.position_label = Label(main_frame, 
                                   text=f"Position: ({self.robot_x}, {self.robot_y}), Angle: {self.robot_angle}°", 
                                   bg=self.colors["bg"], fg=self.colors["text"], font=("Arial", 10))
        self.position_label.pack(pady=2)
        
        # Timer label (to show actual command duration)
        self.timer_label = Label(main_frame, text="Timer: 0.0s", 
                               bg=self.colors["bg"], fg=self.colors["text"], font=("Arial", 10))
        self.timer_label.pack(pady=2)
        
        # Canvas for the map with a cute border
        canvas_frame = Frame(main_frame, bd=5, relief=tk.GROOVE, bg=self.colors["grid"])
        canvas_frame.pack(pady=10)
        
        self.canvas = Canvas(canvas_frame, width=self.map_width, height=self.map_height, 
                            bg=self.colors["map_bg"], bd=0)
        self.canvas.pack()
        
        # Control buttons frame
        control_frame = Frame(main_frame, bg=self.colors["bg"])
        control_frame.pack(pady=10)
        
        # Control buttons with cute styling
        button_style = {"font": ("Arial", 10, "bold"), "width": 10, "height": 2, 
                        "bd": 3, "relief": tk.RAISED}
        
        # Duration selection
        duration_frame = Frame(control_frame, bg=self.colors["bg"])
        duration_frame.grid(row=0, column=0, columnspan=3, pady=5)
        
        Label(duration_frame, text="Duration (seconds):", bg=self.colors["bg"]).pack(side=tk.LEFT, padx=5)
        
        self.duration_var = tk.StringVar(value="1.0")
        duration_options = ["0.5", "1.0", "2.0", "3.0"]
        duration_menu = tk.OptionMenu(duration_frame, self.duration_var, *duration_options)
        duration_menu.pack(side=tk.LEFT, padx=5)
        
        # Movement buttons
        forward_btn = Button(control_frame, text="Forward", bg=self.colors["button"], 
                            command=lambda: self.add_test_command("forward"), **button_style)
        forward_btn.grid(row=1, column=1, padx=5, pady=5)
        
        left_btn = Button(control_frame, text="Left", bg=self.colors["button"], 
                         command=lambda: self.add_test_command("left"), **button_style)
        left_btn.grid(row=2, column=0, padx=5, pady=5)
        
        right_btn = Button(control_frame, text="Right", bg=self.colors["button"], 
                          command=lambda: self.add_test_command("right"), **button_style)
        right_btn.grid(row=2, column=2, padx=5, pady=5)
        
        backward_btn = Button(control_frame, text="Backward", bg=self.colors["button"], 
                             command=lambda: self.add_test_command("backward"), **button_style)
        backward_btn.grid(row=3, column=1, padx=5, pady=5)
        
        # Draw grid
        self.draw_grid()
        
        # Draw robot
        self.draw_robot()
        
    def add_decorations(self):
        # Add trees around the map (simple green circles)
        for _ in range(8):
            x = random.randint(50, self.map_width - 50)
            y = random.randint(50, self.map_height - 50)
            # Make sure trees don't overlap with the robot's starting position
            if abs(x - self.robot_x) > 50 or abs(y - self.robot_y) > 50:
                self.draw_tree(x, y)
        
        # Add houses (simple rectangles)
        for _ in range(3):
            x = random.randint(80, self.map_width - 80)
            y = random.randint(80, self.map_height - 80)
            # Make sure houses don't overlap with the robot's starting position
            if abs(x - self.robot_x) > 80 or abs(y - self.robot_y) > 80:
                self.draw_house(x, y)
        
        # Add some grass patches
        for _ in range(15):
            x = random.randint(20, self.map_width - 20)
            y = random.randint(20, self.map_height - 20)
            size = random.randint(10, 25)
            self.canvas.create_oval(x-size/2, y-size/2, x+size/2, y+size/2, 
                                   fill=self.colors["grass"], outline="", tags="decoration")
    
    def draw_tree(self, x, y):
        # Draw tree trunk
        trunk_width = 8
        trunk_height = 15
        self.canvas.create_rectangle(
            x - trunk_width/2, y, 
            x + trunk_width/2, y + trunk_height, 
            fill="#8B4513", outline="", tags="decoration"
        )
        
        # Draw tree top (3 circles for a cute look)
        radius = 15
        for i in range(3):
            offset_y = -i * radius * 0.8
            self.canvas.create_oval(
                x - radius, y - radius + offset_y,
                x + radius, y + radius + offset_y,
                fill=self.colors["tree"], outline="", tags="decoration"
            )
    
    def draw_house(self, x, y):
        # House dimensions
        width = 40
        height = 30
        
        # Draw house body
        self.canvas.create_rectangle(
            x - width/2, y - height/2,
            x + width/2, y + height/2,
            fill=self.colors["house"], outline="black", tags="decoration"
        )
        
        # Draw roof
        self.canvas.create_polygon(
            x - width/2 - 5, y - height/2,
            x + width/2 + 5, y - height/2,
            x, y - height/2 - 20,
            fill="#8B4513", outline="black", tags="decoration"
        )
        
        # Draw door
        door_width = 10
        door_height = 15
        self.canvas.create_rectangle(
            x - door_width/2, y + height/2 - door_height,
            x + door_width/2, y + height/2,
            fill="#8B7D6B", outline="black", tags="decoration"
        )
        
        # Draw window
        window_size = 8
        self.canvas.create_rectangle(
            x - width/4 - window_size/2, y - height/4 - window_size/2,
            x - width/4 + window_size/2, y - height/4 + window_size/2,
            fill="#ADD8E6", outline="black", tags="decoration"
        )
        self.canvas.create_rectangle(
            x + width/4 - window_size/2, y - height/4 - window_size/2,
            x + width/4 + window_size/2, y - height/4 + window_size/2,
            fill="#ADD8E6", outline="black", tags="decoration"
        )
        
    def draw_grid(self):
        # Draw vertical grid lines
        for x in range(0, self.map_width + 1, self.grid_size):
            self.canvas.create_line(x, 0, x, self.map_height, fill=self.colors["grid"], dash=(4, 4))
            
        # Draw horizontal grid lines
        for y in range(0, self.map_height + 1, self.grid_size):
            self.canvas.create_line(0, y, self.map_width, y, fill=self.colors["grid"], dash=(4, 4))
            
        # Draw border
        self.canvas.create_rectangle(2, 2, self.map_width-2, self.map_height-2, 
                                    outline=self.colors["border"], width=3)
    
    def draw_robot(self):
        # Clear previous robot
        self.canvas.delete("robot")
        
        # Draw robot body (circle)
        self.canvas.create_oval(
            self.robot_x - self.robot_size,
            self.robot_y - self.robot_size,
            self.robot_x + self.robot_size,
            self.robot_y + self.robot_size,
            fill=self.colors["robot"], outline="black", width=2, tags="robot"
        )
        
        # Draw robot face (cute eyes and smile)
        eye_size = self.robot_size / 5
        eye_offset = self.robot_size / 3
        
        # Calculate eye positions based on robot angle
        angle_rad = math.radians(self.robot_angle)
        left_eye_x = self.robot_x + math.cos(angle_rad + math.pi/4) * eye_offset
        left_eye_y = self.robot_y - math.sin(angle_rad + math.pi/4) * eye_offset
        right_eye_x = self.robot_x + math.cos(angle_rad - math.pi/4) * eye_offset
        right_eye_y = self.robot_y - math.sin(angle_rad - math.pi/4) * eye_offset
        
        # Draw eyes
        self.canvas.create_oval(
            left_eye_x - eye_size, left_eye_y - eye_size,
            left_eye_x + eye_size, left_eye_y + eye_size,
            fill="white", outline="black", tags="robot"
        )
        
        self.canvas.create_oval(
            right_eye_x - eye_size, right_eye_y - eye_size,
            right_eye_x + eye_size, right_eye_y + eye_size,
            fill="white", outline="black", tags="robot"
        )
        
        # Draw direction indicator (antenna)
        antenna_length = self.robot_size * 1.2
        end_x = self.robot_x + math.cos(angle_rad) * antenna_length
        end_y = self.robot_y - math.sin(angle_rad) * antenna_length
        
        self.canvas.create_line(
            self.robot_x, self.robot_y, end_x, end_y,
            fill=self.colors["direction"], width=3, tags="robot"
        )
        
        # Draw antenna ball
        self.canvas.create_oval(
            end_x - 4, end_y - 4,
            end_x + 4, end_y + 4,
            fill=self.colors["direction"], outline="black", tags="robot"
        )
        
        # Update position label
        self.position_label.config(text=f"Position: ({int(self.robot_x)}, {int(self.robot_y)}), Angle: {int(self.robot_angle)}°")
    
    def update_path(self):
        # Add current position to path
        self.path_points.append((self.robot_x, self.robot_y))
        
        # Draw path line
        if len(self.path_points) > 1:
            p1 = self.path_points[-2]
            p2 = self.path_points[-1]
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                   fill=self.colors["path"], width=2, tags="path")
    
    def start_server(self):
        # Create Flask app
        app = Flask(__name__)
        
        @app.route('/command', methods=['POST'])
        def receive_command():
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            command = data.get('command', '').lower()
            duration = float(data.get('duration', 1.0))
            
            # Add command to queue
            self.command_queue.append((command, duration))
            
            # Update command label
            self.root.after(0, lambda: self.command_label.config(
                text=f"Received command: {command} for {duration}s"))
            
            return jsonify({"status": "Command received", "command": command, "duration": duration})
        
        @app.route('/status', methods=['GET'])
        def get_status():
            return jsonify({
                "position": {"x": self.robot_x, "y": self.robot_y},
                "angle": self.robot_angle,
                "queue_size": len(self.command_queue),
                "executing": self.executing_command
            })
        
        # Start server in a thread
        def run_server():
            try:
                app.run(host='0.0.0.0', port=5000)
            except Exception as e:
                print(f"Server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait a bit for the server to start
        time.sleep(1)
        self.server_running = True
        self.status_label.config(text="Robot Simulator Ready - Listening on http://localhost:5000")
    
    def process_commands(self):
        if self.command_queue and not self.executing_command:
            self.executing_command = True
            command, duration = self.command_queue.pop(0)
            
            # Execute command
            self.execute_command(command, duration)
        
        # Update timer if a command is executing
        if self.executing_command:
            elapsed = time.time() - self.command_start_time
            if elapsed <= self.command_duration:
                self.timer_label.config(text=f"Timer: {elapsed:.1f}s / {self.command_duration:.1f}s")
            
        # Check again after 50ms (more responsive)
        self.root.after(50, self.process_commands)
    
    def execute_command(self, command, duration):
        # Update status
        self.status_label.config(text=f"Executing: {command} for {duration}s")
        
        # Store command start time and duration
        self.command_start_time = time.time()
        self.command_duration = duration
        
        # Execute the command based on type
        if command == "forward":
            self.execute_movement(duration, 1)
        elif command == "backward":
            self.execute_movement(duration, -1)
        elif command == "left":
            self.execute_turn(duration, 1)
        elif command == "right":
            self.execute_turn(duration, -1)
        else:
            print(f"Unknown command: {command}")
            self.executing_command = False
            self.status_label.config(text="Robot Simulator Ready - Listening on http://localhost:5000")
            self.timer_label.config(text="Timer: 0.0s")
    
    def execute_movement(self, duration, direction):
        """Improved movement execution with precise timing"""
        # Calculate total distance to move
        total_distance = self.robot_speed * duration
        angle_rad = math.radians(self.robot_angle)
        
        # Calculate target position
        target_x = self.robot_x + math.cos(angle_rad) * total_distance * direction
        target_y = self.robot_y - math.sin(angle_rad) * total_distance * direction
        
        # Keep target within bounds
        target_x = max(self.robot_size, min(self.map_width - self.robot_size, target_x))
        target_y = max(self.robot_size, min(self.map_height - self.robot_size, target_y))
        
        # Start the animation
        self.animate_movement(target_x, target_y, duration)
    
    def animate_movement(self, target_x, target_y, duration):
        """Animate movement with precise timing"""
        start_time = time.time()
        start_x = self.robot_x
        start_y = self.robot_y
        
        def update_position():
            # Calculate progress (0.0 to 1.0)
            elapsed = time.time() - start_time
            progress = min(elapsed / duration, 1.0)
            
            # Update position with linear interpolation
            self.robot_x = start_x + (target_x - start_x) * progress
            self.robot_y = start_y + (target_y - start_y) * progress
            
            # Update path and robot
            self.update_path()
            self.draw_robot()
            
            # Continue animation if not complete
            if progress < 1.0:
                self.root.after(16, update_position)  # ~60fps
            else:
                # Ensure final position is exact
                self.robot_x = target_x
                self.robot_y = target_y
                self.draw_robot()
                
                # Command complete
                self.executing_command = False
                self.status_label.config(text="Robot Simulator Ready - Listening on http://localhost:5000")
                self.timer_label.config(text="Timer: 0.0s")
        
        # Start the animation
        update_position()
    
    def execute_turn(self, duration, direction):
        """Improved turning execution with precise timing"""
        # Calculate total angle change
        total_angle_change = self.robot_turn_speed * duration * direction
        target_angle = (self.robot_angle + total_angle_change) % 360
        
        # Start the animation
        self.animate_turn(target_angle, duration)
    
    def animate_turn(self, target_angle, duration):
        """Animate turning with precise timing"""
        start_time = time.time()
        start_angle = self.robot_angle
        angle_diff = (target_angle - start_angle) % 360
        if angle_diff > 180:
            angle_diff -= 360
        
        def update_angle():
            # Calculate progress (0.0 to 1.0)
            elapsed = time.time() - start_time
            progress = min(elapsed / duration, 1.0)
            
            # Update angle with linear interpolation
            self.robot_angle = (start_angle + angle_diff * progress) % 360
            
            # Update robot
            self.draw_robot()
            
            # Continue animation if not complete
            if progress < 1.0:
                self.root.after(16, update_angle)  # ~60fps
            else:
                # Ensure final angle is exact
                self.robot_angle = target_angle
                self.draw_robot()
                
                # Command complete
                self.executing_command = False
                self.status_label.config(text="Robot Simulator Ready - Listening on http://localhost:5000")
                self.timer_label.config(text="Timer: 0.0s")
        
        # Start the animation
        update_angle()
    
    def create_test_client(self):
        # Create a frame for test client
        test_frame = Frame(self.root, bg=self.colors["bg"], bd=3, relief=tk.GROOVE)
        test_frame.pack(pady=10, fill=tk.X, padx=10)
        
        # Test client label
        test_label = Label(test_frame, text="Test HTTP Client", 
                          font=("Arial", 12, "bold"), bg=self.colors["bg"], fg=self.colors["title"])
        test_label.pack(pady=5)
        
        # Add a button to run a test sequence
        test_btn = Button(test_frame, text="Run Test Sequence", bg="#ffd0a0", 
                         font=("Arial", 10, "bold"), command=self.run_test_sequence)
        test_btn.pack(pady=5)
        
        # Add a label to show test results
        self.test_result_label = Label(test_frame, text="", bg=self.colors["bg"], fg=self.colors["text"])
        self.test_result_label.pack(pady=5)
    
    def run_test_sequence(self):
        # Define a sequence of commands
        commands = [
            ("forward", 1.0),
            ("left", 0.5),
            ("forward", 1.0),
            ("right", 0.5),
            ("forward", 1.0),
            ("right", 0.5),
            ("forward", 1.0),
            ("right", 0.5),
            ("forward", 1.0)
        ]
        
        # Add commands to queue with a delay between them
        def add_command(index):
            if index < len(commands):
                command, duration = commands[index]
                self.add_test_command(command, duration)
                self.test_result_label.config(text=f"Sending command {index+1}/{len(commands)}: {command} for {duration}s")
                self.root.after(int((duration + 0.2) * 1000), lambda: add_command(index + 1))
            else:
                self.test_result_label.config(text="Test sequence completed!")
        
        # Start the sequence
        add_command(0)
    
    def add_test_command(self, command, duration=None):
        # Get duration from dropdown if not specified
        if duration is None:
            duration = float(self.duration_var.get())
            
        # Add command directly to queue (simulating HTTP request)
        self.command_queue.append((command, duration))
        self.command_label.config(text=f"Added command: {command} for {duration}s")

# Function to send HTTP commands to the robot
def send_command(command, duration):
    import requests
    url = "http://localhost:5000/command"
    data = {
        "command": command,
        "duration": duration
    }
    try:
        response = requests.post(url, json=data)
        return response.json()
    except requests.exceptions.ConnectionError:
        print("Connection error: Could not connect to the robot simulator.")
        print("Make sure the simulator is running before sending commands.")
        return {"error": "Connection failed"}

# Function to get robot status
def get_status():
    import requests
    url = "http://localhost:5000/status"
    try:
        response = requests.get(url)
        return response.json()
    except requests.exceptions.ConnectionError:
        print("Connection error: Could not connect to the robot simulator.")
        print("Make sure the simulator is running before checking status.")
        return {"error": "Connection failed"}

# Example of how to use the HTTP client from another Python script
def example_control_sequence():
    import time
    
    # Example sequence of commands
    commands = [
        ("forward", 2.0),
        ("left", 1.0),
        ("forward", 1.5),
        ("right", 0.5),
        ("backward", 1.0)
    ]
    
    # Execute commands with a delay between them
    for command, duration in commands:
        print(f"Sending command: {command} for {duration}s")
        result = send_command(command, duration)
        print(f"Response: {result}")
        
        # Wait for the command to complete (duration + a small buffer)
        time.sleep(duration + 0.2)
        
        # Get and print the robot's status
        status = get_status()
        if "error" not in status:
            print(f"Robot status: Position: ({status['position']['x']:.1f}, {status['position']['y']:.1f}), Angle: {status['angle']:.1f}°")
        print("-" * 50)
    
    print("Command sequence completed!")

if __name__ == "__main__":
    root = tk.Tk()
    app = OptimizedRobotSimulator(root)
    root.mainloop()