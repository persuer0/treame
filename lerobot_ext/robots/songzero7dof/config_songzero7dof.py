from dataclasses import dataclass, field
from lerobot.cameras import CameraConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from ..config import RobotConfig


def songzero_cameras_config() -> dict[str, CameraConfig]:
    return {
        "cam_high": OpenCVCameraConfig(
            index_or_path="/dev/video4", fps=30, width=640, height=480
        ),
        "cam_low": OpenCVCameraConfig(
            index_or_path="/dev/video2", fps=30, width=640, height=480
        ),
    }


@RobotConfig.register_subclass("songzero7dof")
@dataclass
class Songzero7DofConfig(RobotConfig):
    # Robot controller address
    host: str = "192.168.31.1"
    ws_port: int = 9090
    rest_port: int = 8080
    username: str = "admin"
    password: str = "123456"

    # Number of joints
    num_joints: int = 7

    # cameras
    cameras: dict[str, CameraConfig] = field(default_factory=songzero_cameras_config)
