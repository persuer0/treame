# Treame

A modular robotic arm control and visual perception framework built on CAN bus communication.

## Overview

Treame provides a layered SDK for controlling AGX-series robotic arms (Piper, Nero, and variants) over SocketCAN, together with a ROS2-based vision stack for body/face detection and real-time web visualization.

```
treame/
├── action_control/          # Robotic arm control SDK
│   └── base/pyAgxArm/
│       ├── api/             # Factory API & constants
│       ├── protocols/       # CAN protocol layer
│       │   ├── comms/       # CAN bus communication
│       │   ├── msgs/        # Transmit / feedback message types
│       │   └── drivers/     # Per-model drivers (Piper, Nero, …)
│       ├── utiles/          # Numeric codec, coordinate transforms
│       ├── configs/         # JSON config presets
│       └── demos/           # Runnable example scripts
└── vision/                  # ROS2 vision stack
    ├── hobot_usb_cam/       # USB camera driver
    ├── hobot_codec/         # Hardware H264/H265 codec
    ├── mono2d_body_detection/     # 2D body keypoint detection
    ├── face_landmarks_detection/  # Face landmark detection
    ├── hobot_shm/           # Shared-memory transport
    └── websocket/           # Nginx + Three.js live visualization
```

## Supported Hardware

| Model | Joints | Notes |
|-------|--------|-------|
| Piper | 6 | Standard model |
| PiperH | 6 | Joint 4 range ±135° |
| PiperL | 6 | Joint 4 range ±127° |
| PiperX | 6 | Joint 4/5 range ±89° |
| Nero | 7 | — |

**End effectors:** AGX Gripper, Revo2 multi-finger hand

## Architecture

```
User API  (AgxArmFactory / create_agx_arm_config)
    │  Factory pattern — creates driver from config dict
    ▼
Driver    (ArmDriverAbstract subclass per model)
    │  Template method — shared logic, model-specific overrides
    ▼
Parser    (CAN message serialization / deserialization)
    │  Converts SI units → CAN wire units (mdeg, µm, …)
    ▼
CanComm   (SocketCAN — Linux / Darwin / Windows)
    │  Receive thread + callback dispatch
    ▼
Physical CAN bus
```

## Requirements

- Python 3.8+
- [`python-can`](https://python-can.readthedocs.io/)
- Linux with SocketCAN support (for real hardware)
- ROS2 Humble or later (vision stack only)
- D-Robotics X3/X5 board (vision stack only)

## Installation

```bash
git clone https://github.com/miracle-techlink/treame.git
cd treame/action_control/base
pip install -e .
```

## Quick Start

### 1. Set up CAN interface

**Physical CAN (e.g., `can0` at 1 Mbps):**

```bash
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up
```

**Virtual CAN for testing:**

```bash
python action_control/base/pyAgxArm/demos/manage_vcan.py create --can_name vcan0
```

### 2. Connect and move

```python
from pyAgxArm import create_agx_arm_config, AgxArmFactory

# Build config
cfg = create_agx_arm_config(
    robot="piper",          # nero | piper | piper_h | piper_l | piper_x
    comm="can",
    channel="can0",
    interface="socketcan",
)

# Create driver and connect
robot = AgxArmFactory.create_arm(cfg)
robot.connect()
robot.enable()

# Joint-space move (radians)
robot.move_j([0.0, 0.4, -0.4, 0.0, -0.4, 0.0])

# Cartesian move — [x, y, z (m), rx, ry, rz (rad)]
robot.move_p([0.1, 0.0, 0.3, 0.0, 1.5708, 0.0])

# Linear move
robot.move_l([0.2, 0.0, 0.3, 0.0, 1.5708, 0.0])

# Arc move (start → via → end)
robot.move_c(start_pose, mid_pose, end_pose)

# Read state
print(robot.get_joint_angles())
print(robot.get_flange_pose())
print(robot.get_arm_status())

robot.disable()
```

### 3. End effector

```python
# AGX Gripper
gripper = robot.init_effector(robot.OPTIONS.EFFECTOR.AGX_GRIPPER)
gripper.move_gripper(0.07)   # open to 70 mm
gripper.move_gripper(0.0)    # close

# Revo2 multi-finger hand
hand = robot.init_effector(robot.OPTIONS.EFFECTOR.REVO2)
hand.position_time_ctrl(mode='pos', thumb_tip=100)
```

### 4. Leader–follower mode

```python
leader.set_leader_mode()
follower.set_follower_mode()
leader.move_leader_to_home()
```

## Configuration

### Programmatic

```python
cfg = create_agx_arm_config(
    robot="piper",
    channel="can0",
    interface="socketcan",
    # override individual joint limits (radians)
    joint_limits={"joint1": [-1.57, 1.57]},
    log_level="DEBUG",
)
```

### JSON preset

```json
{
    "robot": "piper",
    "comm": {
        "type": "can",
        "can": {
            "channel": "can0",
            "interface": "socketcan",
            "bitrate": 1000000
        }
    },
    "joint_limits": {
        "joint1": [-2.617994, 2.617994],
        "joint2": [0.0,       3.141593],
        "joint3": [-2.967060, 0.0     ],
        "joint4": [-1.745330, 1.745330],
        "joint5": [-1.221730, 1.221730],
        "joint6": [-2.094396, 2.094396]
    }
}
```

## Motion API Reference

| Method | Space | Description |
|--------|-------|-------------|
| `move_j(angles)` | Joint | Point-to-point, joint interpolation |
| `move_p(pose)` | Cartesian | Point-to-point, path not guaranteed |
| `move_l(pose)` | Cartesian | Linear path |
| `move_c(start, via, end)` | Cartesian | Arc path |
| `move_js(angles)` | Joint | Streaming / MIT mode |
| `move_mit(joint, pos, ...)` | Joint | Low-level MIT torque/position |

## State Queries

```python
robot.get_arm_status()          # enable state, motion state, error flags
robot.get_joint_angles()        # list[float] in radians
robot.get_flange_pose()         # [x, y, z, rx, ry, rz]
robot.get_motor_states(joint)   # torque, temperature, current
robot.get_driver_states(joint)  # driver diagnostics
robot.get_firmware()            # firmware version string
robot.get_fps()                 # feedback message rate
```

## Safety & Limits

```python
robot.set_speed_percent(50)                        # global speed scale (%)
robot.set_flange_vel_acc_limits(v, a, wv, wa)      # TCP velocity/accel limits
robot.set_joint_angle_vel_acc_limits_to_default()  # reset to factory defaults
robot.set_crash_protection_rating(joint_index=1, rating=1)
robot.electronic_emergency_stop()
robot.reset()
```

## Registering a Custom Driver

```python
from pyAgxArm import AgxArmFactory
from my_package import MyCustomDriver

AgxArmFactory.register_arm(
    robot="my_robot",
    comm="can",
    firmeware_version="v2",
    driver_cls=MyCustomDriver,
)
```

## Vision Stack

The `vision/` directory is a collection of ROS2 packages targeting D-Robotics X3/X5 boards.

```bash
# Build
colcon build --packages-select hobot_usb_cam hobot_codec mono2d_body_detection websocket

# Launch full pipeline (camera → detection → web visualization)
ros2 launch websocket websocket.launch.py
```

Open `http://<board-ip>:8080` to view the live Three.js skeleton overlay.

## Demo Scripts

| Script | Description |
|--------|-------------|
| `demos/piper/test1.py` | Full Piper feature walkthrough |
| `demos/nero/test1.py` | Nero arm example |
| `demos/piper_h/test1.py` | PiperH example |
| `demos/manage_vcan.py` | Create / delete virtual CAN interfaces |
| `demos/detect_piper_series.py` | Auto-detect connected Piper variant |

## License

See [LICENSE](LICENSE) for details.
