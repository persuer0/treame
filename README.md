# Treame — 家务护理具身智能平台

> 让机械臂完成日常护理动作：刷牙、吹头发、剃胡子。
> Robotic arms for daily personal care: tooth brushing, hair drying, shaving.

---

## 中文版

### 项目简介

**Treame**（发音同 *Treat Me*）是一个面向**家务护理场景**的具身智能开发框架。

我们的目标是让机械臂真正进入日常生活，承担那些重复性、精细化的个人护理任务——无论是早晨的刷牙、洗澡后的吹发，还是每天的剃须。Treame 提供从底层 CAN 总线控制到上层视觉感知的完整技术栈，为护理类具身机器人的落地提供基础。

### 典型应用场景

| 场景 | 关键动作 | 技术要点 |
|------|----------|----------|
| 🦷 刷牙 | 牙刷轨迹规划、力控清洁 | 笛卡尔直线运动 + 末端力反馈 |
| 💨 吹头发 | 跟随头部运动、角度自适应 | 人体关键点检测 + 实时轨迹调整 |
| 🪒 剃胡子 | 面部轮廓贴合、微米级精度 | 人脸关键点 + TCP 偏置精确控制 |

---

### 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    上层应用 / 护理任务                     │
│          (刷牙轨迹 / 吹发跟随 / 剃须路径规划)               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   视觉感知层 (ROS2)                        │
│   人体骨骼检测  │  人脸关键点  │  USB 摄像头  │ Web 可视化  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   机械臂控制层 (pyAgxArm)                  │
│                                                         │
│  AgxArmFactory  ──▶  ArmDriverAbstract                  │
│  (工厂模式)              (模板方法模式)                     │
│       │                      │                          │
│  驱动注册表               协议解析器 (Parser)               │
│  Piper / PiperH / PiperL / PiperX / Nero               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   通信层 (CanComm)                         │
│         SocketCAN (Linux) │ 跨平台策略模式                  │
└────────────────────────┬────────────────────────────────┘
                         │
                  物理 CAN 总线 (1 Mbps)
                         │
               机械臂本体 + 末端执行器
              (AGX 夹爪 / Revo2 多指手)
```

#### 设计模式说明

| 模式 | 位置 | 作用 |
|------|------|------|
| **工厂模式** | `AgxArmFactory` | 根据配置字典动态创建驱动实例，一行代码切换机型 |
| **模板方法** | `ArmDriverAbstract` | 基类定义控制骨架（连接/使能/运动），子类仅覆盖机型差异 |
| **策略模式** | `CanComm` | 运行时根据操作系统选择 SocketCAN / 虚拟 CAN 实现 |
| **注册表** | `AgxArmFactory._registry` | 三层嵌套字典 `robot → comm → version` 管理全部驱动映射 |

---

### 项目结构

```
treame/
├── action_control/
│   └── base/
│       └── pyAgxArm/
│           ├── api/                   # 工厂 API 与预设常量
│           │   ├── agx_arm_factory.py # AgxArmFactory + create_agx_arm_config
│           │   └── constants.py       # 各机型关节名称、限位预设
│           ├── protocols/
│           │   └── can_protocol/
│           │       ├── comms/         # CAN 总线通信（SocketCAN）
│           │       ├── msgs/          # 发送 / 反馈消息类型定义
│           │       └── drivers/       # 各机型驱动实现
│           │           ├── piper/     # Piper 标准版（2343 行）
│           │           ├── piper_h/   # PiperH — 关节 4 范围 ±135°
│           │           ├── piper_l/   # PiperL — 关节 4 范围 ±127°
│           │           ├── piper_x/   # PiperX — 关节 4/5 范围 ±89°
│           │           ├── nero/      # Nero 7 关节版
│           │           └── effector/  # 末端执行器驱动
│           │               ├── agx_gripper/  # AGX 夹爪
│           │               └── revo2/        # Revo2 多指手
│           ├── utiles/
│           │   ├── numeric_codec.py   # 数值编解码（弧度↔毫度、米↔微米）
│           │   └── tf.py              # 位姿变换矩阵（SE3）
│           ├── configs/               # JSON 配置预设
│           └── demos/                 # 可直接运行的示例脚本
└── vision/
    ├── hobot_usb_cam/                 # USB 摄像头 ROS2 驱动
    ├── hobot_codec/                   # 硬件 H264/H265 编解码
    ├── mono2d_body_detection/         # 2D 人体骨骼关键点检测
    ├── face_landmarks_detection/      # 人脸关键点检测
    ├── hobot_shm/                     # 共享内存高速传输
    └── websocket/                     # Nginx + Three.js 实时可视化
```

---

### 支持机型

| 机型 | 关节数 | 关节 4 范围 | 关节 5 范围 | 适用护理场景 |
|------|--------|------------|------------|-------------|
| Piper | 6 | ±100° | ±70° | 通用 |
| PiperH | 6 | ±135° | ±89.5° | 大幅度动作（吹发） |
| PiperL | 6 | ±127° | ±89.5° | 中幅精细动作 |
| PiperX | 6 | ±89° | ±89° | 精密对称作业（剃须） |
| Nero | 7 | — | — | 高自由度护理 |

---

### 快速开始

#### 1. 安装

```bash
git clone https://github.com/miracle-techlink/treame.git
cd treame/action_control/base
pip install -e .
```

#### 2. 配置 CAN 接口

**实体 CAN（机械臂实机）：**

```bash
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up
```

**虚拟 CAN（仿真测试）：**

```bash
python action_control/base/pyAgxArm/demos/manage_vcan.py create --can_name vcan0
```

#### 3. 连接机械臂

```python
from pyAgxArm import create_agx_arm_config, AgxArmFactory

cfg = create_agx_arm_config(
    robot="piper",       # nero | piper | piper_h | piper_l | piper_x
    comm="can",
    channel="can0",
    interface="socketcan",
)

robot = AgxArmFactory.create_arm(cfg)
robot.connect()
robot.enable()
```

#### 4. 护理动作示例

**刷牙轨迹（直线往复）：**

```python
import time

# 设置牙刷 TCP 偏置（工具末端到法兰的偏移）
robot.set_tcp_offset([0, 0, 0.15, 0, 0, 0])

# 刷牙起始位置
robot.move_p([0.15, 0.0, 0.25, 0.0, 1.5708, 0.0])
time.sleep(0.5)

# 水平往复刷动
for _ in range(10):
    robot.move_l([0.15,  0.03, 0.25, 0.0, 1.5708, 0.0])
    time.sleep(0.3)
    robot.move_l([0.15, -0.03, 0.25, 0.0, 1.5708, 0.0])
    time.sleep(0.3)
```

**吹发跟随（配合视觉关键点）：**

```python
# 人体关键点检测给出头部位置 head_pos = [x, y, z]
# 机械臂实时跟随，保持固定朝向

robot.set_speed_percent(30)   # 护理场景降速，安全优先
target_pose = head_pos + [0.0, 1.5708, 0.0]
robot.move_p(target_pose)
```

**剃须路径（圆弧贴合面部轮廓）：**

```python
# 根据人脸关键点计算面部弧线三点
start = [0.12,  0.04, 0.22, 0.0, 1.5708, 0.0]
via   = [0.12,  0.00, 0.20, 0.0, 1.5708, 0.0]
end   = [0.12, -0.04, 0.22, 0.0, 1.5708, 0.0]

robot.move_c(start, via, end)
```

#### 5. 末端执行器

```python
# AGX 夹爪（适合夹持牙刷、剃须刀）
gripper = robot.init_effector(robot.OPTIONS.EFFECTOR.AGX_GRIPPER)
gripper.move_gripper(0.07)   # 张开 70 mm
gripper.move_gripper(0.0)    # 闭合

# Revo2 多指手（适合拿吹风机）
hand = robot.init_effector(robot.OPTIONS.EFFECTOR.REVO2)
hand.position_time_ctrl(mode='pos', thumb_tip=100)
```

---

### 运动 API

| 方法 | 空间 | 说明 |
|------|------|------|
| `move_j(angles)` | 关节空间 | 点到点，关节插值，适合回零位 |
| `move_p(pose)` | 笛卡尔 | 点到点，路径不保证直线 |
| `move_l(pose)` | 笛卡尔 | 直线运动，适合刷牙/剃须往复 |
| `move_c(s, via, e)` | 笛卡尔 | 圆弧运动，适合面部轮廓贴合 |
| `move_js(angles)` | 关节空间 | 流式控制，适合实时跟随 |
| `move_mit(joint, pos, ...)` | 关节 | MIT 模式，底层力矩/位置混控 |

### 状态查询

```python
robot.get_joint_angles()        # 各关节角度（弧度）
robot.get_flange_pose()         # 末端法兰位姿 [x,y,z,rx,ry,rz]
robot.get_tcp_pose()            # TCP 位姿（含工具偏置）
robot.get_arm_status()          # 使能状态、运动状态、错误码
robot.get_motor_states(joint)   # 电机力矩、温度、电流
robot.is_ok()                   # 通信是否正常
robot.get_fps()                 # 反馈消息频率
```

### 安全控制

```python
robot.set_speed_percent(30)                        # 护理场景建议 ≤50%
robot.set_crash_protection_rating(joint_index=1, rating=1)  # 碰撞保护
robot.set_flange_vel_acc_limits(0.3, 0.1, 0.5, 0.2)       # 限制末端速度/加速度
robot.electronic_emergency_stop()                          # 紧急停止
robot.reset()                                              # 复位
```

---

### 视觉感知栈（ROS2）

面向 D-Robotics X3/X5 开发板，提供完整的实时视觉处理流水线。

```
USB 摄像头 (1080p MJPEG)
    ↓ hobot_usb_cam
硬件编解码 (H264)
    ↓ hobot_codec
人体 / 人脸关键点检测
    ↓ mono2d_body_detection / face_landmarks_detection
共享内存传输 (hobot_shm)
    ↓
WebSocket 推流 → 浏览器 Three.js 3D 骨骼渲染
```

```bash
# 构建视觉模块
colcon build --packages-select \
  hobot_usb_cam hobot_codec mono2d_body_detection \
  face_landmarks_detection websocket

# 启动完整视觉流水线
ros2 launch websocket websocket.launch.py
```

打开 `http://<设备IP>:8080` 即可查看实时骨骼叠加画面。

---

### 示例脚本

| 脚本 | 说明 |
|------|------|
| `demos/piper/test1.py` | Piper 全功能演示 |
| `demos/nero/test1.py` | Nero 7 关节演示 |
| `demos/piper_h/test1.py` | PiperH 演示 |
| `demos/piper_x/test1.py` | PiperX 精密模式演示 |
| `demos/manage_vcan.py` | 虚拟 CAN 接口管理 |
| `demos/detect_piper_series.py` | 自动检测已连接的 Piper 机型 |

---

### 注册自定义驱动

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

---

## English Version

### Overview

**Treame** (*Treat Me*) is an embodied AI framework for **household personal care robotics** — tooth brushing, hair drying, and shaving.

The project provides a full-stack SDK: from low-level CAN bus control of AGX-series robotic arms to a ROS2 vision pipeline for body/face perception, enabling precise, safe, human-centered care motions in daily life.

### Target Scenarios

| Scenario | Key Motion | Technical Highlights |
|----------|-----------|----------------------|
| 🦷 Tooth Brushing | Toothbrush trajectory, force-controlled cleaning | Cartesian linear move + end-effector feedback |
| 💨 Hair Drying | Head tracking, adaptive angle | Body keypoint detection + real-time path adjustment |
| 🪒 Shaving | Face contour following, micron precision | Face landmarks + TCP offset control |

---

### Architecture

```
┌────────────────────────────────────────────────────┐
│              Application / Care Tasks               │
│   (Brush trajectory / Hair follow / Shave path)    │
└─────────────────────┬──────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────┐
│              Vision Layer  (ROS2)                   │
│  Body skeleton │ Face landmarks │ Cam │ Web viz     │
└─────────────────────┬──────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────┐
│           Arm Control Layer  (pyAgxArm)             │
│                                                    │
│  AgxArmFactory ──▶ ArmDriverAbstract               │
│  (Factory)            (Template Method)             │
│       │                    │                        │
│  Driver Registry      Protocol Parser               │
│  Piper / PiperH / PiperL / PiperX / Nero           │
└─────────────────────┬──────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────┐
│              Communication  (CanComm)               │
│       SocketCAN (Linux) │ Strategy pattern          │
└─────────────────────┬──────────────────────────────┘
                      │
               Physical CAN bus (1 Mbps)
                      │
          Robotic arm + End effector
         (AGX Gripper / Revo2 hand)
```

#### Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Factory** | `AgxArmFactory` | Create driver from config dict; switch models in one line |
| **Template Method** | `ArmDriverAbstract` | Shared control skeleton; subclasses override model specifics |
| **Strategy** | `CanComm` | Select SocketCAN / virtual CAN at runtime by OS |
| **Registry** | `AgxArmFactory._registry` | Three-level dict `robot → comm → version` maps all drivers |

---

### Supported Hardware

| Model | DOF | Joint 4 | Joint 5 | Best Use |
|-------|-----|---------|---------|----------|
| Piper | 6 | ±100° | ±70° | General purpose |
| PiperH | 6 | ±135° | ±89.5° | Wide-range (hair drying) |
| PiperL | 6 | ±127° | ±89.5° | Medium-range fine motion |
| PiperX | 6 | ±89° | ±89° | Symmetric precision (shaving) |
| Nero | 7 | — | — | High-DOF care tasks |

**End effectors:** AGX Gripper (toothbrush / razor), Revo2 multi-finger hand (hair dryer)

---

### Quick Start

#### Install

```bash
git clone https://github.com/miracle-techlink/treame.git
cd treame/action_control/base
pip install -e .
```

#### Connect and move

```python
from pyAgxArm import create_agx_arm_config, AgxArmFactory

cfg = create_agx_arm_config(
    robot="piper",          # nero | piper | piper_h | piper_l | piper_x
    comm="can",
    channel="can0",
    interface="socketcan",
)

robot = AgxArmFactory.create_arm(cfg)
robot.connect()
robot.enable()

# Joint-space (radians)
robot.move_j([0.0, 0.4, -0.4, 0.0, -0.4, 0.0])

# Cartesian point-to-point  [x, y, z (m), rx, ry, rz (rad)]
robot.move_p([0.1, 0.0, 0.3, 0.0, 1.5708, 0.0])

# Linear (tooth brushing strokes)
robot.move_l([0.15, 0.03, 0.25, 0.0, 1.5708, 0.0])

# Arc (face contour following)
robot.move_c(start_pose, via_pose, end_pose)
```

#### Safety settings for care scenarios

```python
robot.set_speed_percent(30)           # keep ≤50% near humans
robot.set_crash_protection_rating(joint_index=1, rating=1)
robot.electronic_emergency_stop()     # instant stop
```

---

### Motion API

| Method | Space | Use case |
|--------|-------|----------|
| `move_j(angles)` | Joint | Homing, large repositioning |
| `move_p(pose)` | Cartesian | General point-to-point |
| `move_l(pose)` | Cartesian | Brushing / shaving linear strokes |
| `move_c(s, via, e)` | Cartesian | Face contour arcs |
| `move_js(angles)` | Joint | Streaming / real-time tracking |
| `move_mit(joint, ...)` | Joint | Low-level MIT torque/position |

### State Queries

```python
robot.get_joint_angles()      # list[float] in radians
robot.get_flange_pose()       # [x, y, z, rx, ry, rz]
robot.get_tcp_pose()          # TCP pose with tool offset applied
robot.get_arm_status()        # enable, motion, error flags
robot.get_motor_states(j)     # torque, temperature, current
robot.get_fps()               # feedback message rate
```

---

### Vision Stack (ROS2)

Targeting D-Robotics X3/X5 boards:

```bash
colcon build --packages-select \
  hobot_usb_cam hobot_codec mono2d_body_detection \
  face_landmarks_detection websocket

ros2 launch websocket websocket.launch.py
# Open http://<board-ip>:8080 for live Three.js skeleton overlay
```

---

### Requirements

- Python 3.8+
- `python-can`
- Linux with SocketCAN (real hardware) or any OS with virtual CAN for testing
- ROS2 Humble+ and D-Robotics X3/X5 (vision stack only)

---

### License

See [LICENSE](LICENSE) for details.
