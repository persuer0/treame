# Treame

**家务护理具身智能平台 | Embodied AI Platform for Personal Care**

---

## 中文版

### 项目简介

**Treame**（发音同 *Treat Me*）是一个面向家庭日常护理场景的具身智能开发框架。

我们相信，机器人进入家庭的第一步，不是做饭或搬运，而是那些最私人、最细腻的护理动作——刷牙、吹头发、剃胡子。这些动作要求毫米级的位置精度、对人体的实时感知，以及绝对的安全性。Treame 为此而生。

---

### 核心应用场景

```
🦷 刷牙      —— 牙刷轨迹规划 × 力控清洁
💨 吹头发    —— 头部跟随 × 角度自适应
🪒 剃胡子    —— 面部轮廓贴合 × 微米级精度
```

---

### 系统架构

Treame 采用三层解耦架构，从人体感知到物理执行形成完整闭环：

```
感知层  →  控制层  →  执行层
```

**感知层（Vision）**
实时采集人体状态，驱动机械臂动态响应。包含人体骨骼关键点检测、人脸关键点检测、USB 摄像头接入与硬件加速编解码，以及基于 WebSocket 的实时可视化监控。

**控制层（pyAgxArm）**
机械臂 SDK 核心，负责将高层护理动作指令转化为底层运动控制信号。采用工厂模式管理多机型驱动，通过模板方法统一控制接口，支持关节空间、笛卡尔空间、直线、圆弧等多种运动模式。

**执行层（CAN Bus）**
通过 SocketCAN 协议与机械臂本体通信，支持 AGX 系列夹爪与 Revo2 多指手等末端执行器，实现 1 Mbps 高速实时控制。

> 架构图见下方 Manus 生成版本

---

### 支持机型

Treame 支持 AGX 系列五款机械臂，根据护理任务的动作幅度和精度需求灵活选型：

- **Piper** — 标准 6 关节，适合通用护理任务
- **PiperH** — 关节活动范围更大，适合吹发等大幅度动作
- **PiperL** — 中等活动范围，兼顾灵活与稳定
- **PiperX** — 关节对称设计，适合剃须等高精度对称动作
- **Nero** — 7 关节冗余自由度，适合复杂护理场景

末端执行器支持 **AGX 夹爪**（适合夹持牙刷、剃须刀）与 **Revo2 多指手**（适合握持吹风机）。

---

### 设计理念

**安全优先**
护理场景与人体直接接触，Treame 在驱动层内置碰撞保护、关节限位与紧急停止机制，所有运动指令经过输入验证后方可下发。

**感知驱动**
机械臂不做固定轨迹回放，而是实时接收视觉感知层的人体关键点数据，动态调整末端位姿，实现真正意义上的"以人为中心"的护理。

**模块解耦**
感知、控制、执行三层完全解耦，每层可独立替换。视觉模型可升级，机型可切换，通信协议可扩展，不影响其他层。

**多机型统一接口**
五款机械臂共享同一套 API，上层护理应用代码无需感知底层机型差异，降低迁移和扩展成本。

---

### 项目结构

```
treame/
├── action_control/          # 机械臂控制 SDK (pyAgxArm)
│   └── base/pyAgxArm/
│       ├── api/             # 工厂接口与机型配置
│       ├── protocols/       # CAN 协议、消息定义、各机型驱动
│       ├── utiles/          # 坐标变换、数值编解码工具
│       └── demos/           # 各机型示例脚本
└── vision/                  # 视觉感知栈 (ROS2)
    ├── hobot_usb_cam/       # 摄像头驱动
    ├── hobot_codec/         # 硬件编解码
    ├── mono2d_body_detection/     # 人体骨骼检测
    ├── face_landmarks_detection/  # 人脸关键点检测
    ├── hobot_shm/           # 共享内存传输
    └── websocket/           # 实时 Web 可视化
```

---

## English Version

### Overview

**Treame** (*Treat Me*) is an embodied AI framework designed for household personal care robotics.

We believe the first meaningful step for home robots is not cooking or logistics — it is the most intimate, delicate tasks: brushing teeth, drying hair, and shaving. These require millimeter-level precision, real-time human perception, and absolute safety. Treame is built for exactly this.

---

### Target Scenarios

```
🦷 Tooth Brushing  —  trajectory planning × force-controlled cleaning
💨 Hair Drying     —  head tracking × adaptive angle
🪒 Shaving         —  face contour following × micron-level precision
```

---

### System Architecture

Treame adopts a three-layer decoupled architecture forming a closed loop from human perception to physical execution:

```
Perception  →  Control  →  Actuation
```

**Perception Layer (Vision)**
Real-time human state capture to drive dynamic robot response. Includes body skeleton keypoint detection, face landmark detection, USB camera integration with hardware-accelerated codec, and WebSocket-based live visualization.

**Control Layer (pyAgxArm)**
The robotic arm SDK core, translating high-level care action commands into low-level motion control signals. Uses the Factory pattern for multi-model driver management, Template Method for unified control interfaces, and supports joint-space, Cartesian, linear, and arc motion modes.

**Actuation Layer (CAN Bus)**
Communicates with the arm body via SocketCAN protocol at 1 Mbps. Supports AGX Gripper and Revo2 multi-finger hand end effectors.

> See Manus-generated architecture diagram below.

---

### Supported Hardware

Five AGX-series robotic arm models, selected by care task requirements:

- **Piper** — Standard 6-DOF, general-purpose care
- **PiperH** — Wider joint range, suited for hair drying
- **PiperL** — Medium range, balance of agility and stability
- **PiperX** — Symmetric joint design, suited for precision shaving
- **Nero** — 7-DOF redundant, suited for complex care scenarios

End effectors: **AGX Gripper** (toothbrush / razor) · **Revo2 multi-finger hand** (hair dryer)

---

### Design Principles

**Safety First**
Care tasks involve direct contact with the human body. Treame embeds collision protection, joint limit enforcement, and emergency stop at the driver level. All motion commands are validated before execution.

**Perception-Driven Motion**
The arm does not replay fixed trajectories. It continuously receives human keypoint data from the vision layer and dynamically adjusts end-effector pose — true human-centered care.

**Layered Decoupling**
Perception, control, and actuation are fully independent. Vision models, arm models, and communication protocols can each be upgraded without affecting the others.

**Unified Multi-Model Interface**
All five arm models share the same API. Care application code requires no awareness of the underlying hardware, minimizing migration and extension costs.

---

### Repository Structure

```
treame/
├── action_control/          # Robotic arm SDK (pyAgxArm)
│   └── base/pyAgxArm/
│       ├── api/             # Factory interface & model configuration
│       ├── protocols/       # CAN protocol, message types, per-model drivers
│       ├── utiles/          # Coordinate transforms, numeric codec
│       └── demos/           # Per-model example scripts
└── vision/                  # Vision perception stack (ROS2)
    ├── hobot_usb_cam/       # Camera driver
    ├── hobot_codec/         # Hardware codec
    ├── mono2d_body_detection/     # Body skeleton detection
    ├── face_landmarks_detection/  # Face landmark detection
    ├── hobot_shm/           # Shared-memory transport
    └── websocket/           # Real-time web visualization
```

---

### License

See [LICENSE](LICENSE) for details.
