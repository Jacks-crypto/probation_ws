# Probation Task: Going Through Gate with Unity Simulation

# Autonomous Navigation System


## Features
- Autonomous GUIDED mode setting
- Controlled downward movement to gate level
- Computer vision gate detection and centering
- Continuous forward movement through gate
- Full ROS2 node coordination

## Requirements
- ROS2 Humble
- MAVROS
- Unity simulation
- Python



### Dependencies
This package requires the following ROS2 packages:
- `vision_msgs`
- `geometry_msgs` 
- `std_msgs`
- `mavros_msgs`

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Jacks-crypto/probation_ws.git
cd probation_ws
```

2. Install ROS2 dependencies:
```bash
sudo apt update
sudo apt install ros-humble-vision-msgs ros-humble-mavros-msgs
```

3. Build the workspace:
```bash
colcon build --packages-select navigation_package
```

4. Source the workspace:
```bash
source install/setup.bash
```

5. Verify installation:
```bash
ros2 pkg list | grep navigation_package
```

### MAVROS Setup
Ensure MAVROS is properly configured for your vehicle/simulation:
```bash
sudo apt install ros-humble-mavros ros-humble-mavros-extras
```

## Usage

1. Open two terminals and source both terminals:
```bash
source install/setup.bash
```

2. Enter this in the first terminal:
```bash
ros2 run ros_tcp_endpoint default_server_endpoint
```

3. Open Unity simulation

4. Enter this in your second terminal:
```bash
ros2 launch navigation_package navigation.launch.py
```

5. Wait for the vehicle to sink finish and press tab once the camera of the vehicle faces the wall.
6. Observe as it detects the gate and move towards it.


### Node Descriptions

#### 1. **guided_node**
- **Purpose**: Initializes the mission by setting the vehicle to GUIDED flight mode
- **Communication**: 
  - **Service Client**: `/mavros/set_mode` (communicates with MAVROS)
  - **Publisher**: `/navigation/guided_ready` (signals completion to downwards_node)


#### 2. **downwards_node** 
- **Purpose**: Controls vertical descent to reach optimal gate detection altitude
- **Communication**:
  - **Subscriber**: `/navigation/guided_ready` (waits for guided_node completion)
  - **Publisher**: `/navigation/movement_complete` (signals completion to rotation_node)
  - **Publisher**: `/mavros/setpoint_velocity/cmd_vel_unstamped` (movement commands)
- **Parameters**: Downward speed , duration 


#### 3. **rotation_node**
- **Purpose**: Searches for and centers the target gate using computer vision
- **Communication**:
  - **Subscriber**: `/navigation/movement_complete` (waits for downwards_node completion)
  - **Subscriber**: `/main_camera/detection/bounding_boxes` (receives camera detections)
  - **Publisher**: `/navigation/detection_complete` (signals completion to forward_node)
  - **Publisher**: `/mavros/setpoint_velocity/cmd_vel_unstamped` (rotation commands)


#### 4. **forward_node**
- **Purpose**: Executes continuous forward movement through the detected gate
- **Communication**:
  - **Subscriber**: `/navigation/detection_complete` (waits for rotation_node completion)
  - **Publisher**: `/mavros/setpoint_velocity/cmd_vel_unstamped` (forward movement commands)



## Additional comments:
- There is a minor bug where the vehicle moves sideways when moving downwards. It is being investigated.
- The detection rate is not 100%.

# Thoughts:
- It is my first ROS2 project with little to no knowledge. I read up the tutorials and learnt a lot about ROS2 from this project. When I was at a loss, I researched to solve certain issues. I believe I will be more confident on working on future projects with my new found knoweledge.