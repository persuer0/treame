"""
DragPassthrough — virtual teleoperator for drag-teach robots.

In drag-teach mode there is no separate leader device. The "teleoperator" is
the human physically moving the compliant arm. DragPassthrough mirrors the
follower robot's current joint positions as the recorded action.

Wiring (handled by scripts/record_songzero.py):
    robot = make_robot_from_config(cfg.robot)          # Songzero7Dof
    teleop = make_teleoperator_from_config(cfg.teleop) # DragPassthrough
    teleop.set_robot(robot)                            # inject robot ref
"""

import logging
from dataclasses import dataclass
from typing import Any

from lerobot.teleoperators.teleoperator import Teleoperator

try:
    from lerobot.configs.teleoperator import TeleoperatorConfig
except ImportError:
    # Older lerobot versions store config differently
    from lerobot.teleoperators.config import TeleoperatorConfig  # type: ignore

logger = logging.getLogger(__name__)


@TeleoperatorConfig.register_subclass("drag_passthrough")
@dataclass
class DragPassthroughConfig(TeleoperatorConfig):
    """No hardware fields needed — state is read from the follower robot."""
    pass


class DragPassthrough(Teleoperator):
    """
    Virtual teleoperator for drag-teach mode.

    get_action() returns the follower robot's current joint positions so that
    lerobot's record loop can save them as the action label without any
    separate leader arm.

    Usage:
        teleop = DragPassthrough(DragPassthroughConfig())
        teleop.set_robot(robot)          # must be called before connect()
        teleop.connect()
        action = teleop.get_action()     # {"joint1": 0.12, ...}
    """

    config_class = DragPassthroughConfig
    name = "drag_passthrough"

    def __init__(self, config: DragPassthroughConfig):
        super().__init__(config)
        self._robot = None
        self._connected = False

    # ------------------------------------------------------------------ #
    #  Robot injection
    # ------------------------------------------------------------------ #

    def set_robot(self, robot) -> None:
        """Inject the follower robot before calling connect().

        Args:
            robot: Any robot that implements get_joint_state() -> dict[str, float].
                   (e.g. Songzero7Dof)
        """
        self._robot = robot
        logger.info(f"DragPassthrough wired to robot: {robot}")

    # ------------------------------------------------------------------ #
    #  Teleoperator interface
    # ------------------------------------------------------------------ #

    @property
    def action_features(self) -> dict:
        if self._robot is not None and hasattr(self._robot, "action_features"):
            return self._robot.action_features
        return {}

    @property
    def observation_features(self) -> dict:
        return {}

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def is_calibrated(self) -> bool:
        return True

    def connect(self, calibrate: bool = False) -> None:
        if self._robot is None:
            raise RuntimeError(
                "DragPassthrough: call set_robot(robot) before connect(). "
                "See scripts/record_songzero.py for wiring."
            )
        self._connected = True
        logger.info("DragPassthrough connected (no hardware).")

    def disconnect(self) -> None:
        self._connected = False
        logger.info("DragPassthrough disconnected.")

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    def get_action(self) -> dict[str, Any]:
        """Return follower robot's current joint positions as action dict.

        Returns:
            dict with bare joint names as keys, e.g.
            {"joint1": 0.12, "joint2": -0.34, "joint3": 0.56,
             "joint4": -0.78, "joint5": 0.90, "joint6": -0.12, "joint7": 0.34}

        Returns empty dict if robot is not set or not connected.
        """
        if self._robot is None or not self._robot.is_connected:
            logger.warning("DragPassthrough.get_action: robot not connected, returning empty action.")
            return {}

        return self._robot.get_joint_state()
