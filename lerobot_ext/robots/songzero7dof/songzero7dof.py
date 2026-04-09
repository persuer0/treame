"""
Songzero 7DOF robot driver for LeRobot.

Connection: WiFi WebSocket (port 9090) for state reading,
            REST API (port 80) for authentication and control.

Enable + drag-teach sequence (fully automatic):
  1. POST /api/login  → JWT token
  2. GET  /api/estop?action=2  → resume e-stop
  3. GET  /api/cleanError?action=1  → clear errors
  4. GET  /api/setting/setCtrlMode?ctrlMode=3  → teach controller mode
  5. GET  /api/set/enable?jointNum=8&action=1  → enable all 7 joints
  6. GET  /api/teach?action=1&name=lerobot_session  → start drag mode

  To stop:
  7. GET  /api/teach?action=2  → stop drag / go back to position mode
  8. GET  /api/set/enable?jointNum=8&action=2  → disable joints
"""

import logging
import threading
import time
from typing import Any

import requests

from lerobot.cameras.opencv import OpenCVCamera
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from ..robot import Robot
from .config_songzero7dof import Songzero7DofConfig

logger = logging.getLogger(__name__)

JOINT_NAMES = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7"]

# Teach session name used internally (no data is saved by the robot; we record externally)
_TEACH_SESSION = "lerobot_drag_session"


class Songzero7Dof(Robot):
    config_class = Songzero7DofConfig
    name = "songzero7dof"

    def __init__(self, config: Songzero7DofConfig):
        super().__init__(config)
        self.config = config
        self._connected = False
        self._ws = None
        self._ws_thread = None
        self._lock = threading.Lock()
        self._latest_positions = [0.0] * config.num_joints
        self._token = None
        self._session = requests.Session()
        self.cameras: dict[str, OpenCVCamera] = {}

    # ------------------------------------------------------------------ #
    #  Properties required by base class
    # ------------------------------------------------------------------ #

    @property
    def observation_features(self) -> dict:
        feats = {}
        for name in JOINT_NAMES:
            feats[f"observation.state.{name}"] = float
        for cam_name, cam_cfg in self.config.cameras.items():
            feats[f"observation.images.{cam_name}"] = (cam_cfg.height, cam_cfg.width, 3)
        return feats

    @property
    def action_features(self) -> dict:
        return {f"action.{name}": float for name in JOINT_NAMES}

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def is_calibrated(self) -> bool:
        return True

    # ------------------------------------------------------------------ #
    #  Connection / disconnection
    # ------------------------------------------------------------------ #

    def connect(self, calibrate: bool = True) -> None:
        if self._connected:
            raise DeviceAlreadyConnectedError(f"{self} is already connected.")

        logger.info(f"Connecting to Songzero7Dof at {self.config.host}...")

        # 1. REST auth (port 80 — nginx proxies /api/* to backend)
        self._token = self._login()
        self._session.headers.update({"Authorization": f"Bearer {self._token}"})
        logger.info("REST API authenticated.")

        # 2. Enable arm + start drag mode
        self._enable_arm()

        # 3. Start WebSocket reader
        self._start_ws_reader()

        # 4. Connect cameras
        for cam_name, cam_cfg in self.config.cameras.items():
            cam = OpenCVCamera(cam_cfg)
            cam.connect()
            self.cameras[cam_name] = cam
            logger.info(f"Camera '{cam_name}' connected.")

        self._connected = True
        logger.info("Songzero7Dof connected and in drag mode. Physically move the arm to record.")

    def disconnect(self) -> None:
        if not self._connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        self._connected = False

        # Stop drag mode and disable joints
        try:
            self._api_get(f"/api/teach?action=2")
            logger.info("Drag teach mode stopped.")
        except Exception as e:
            logger.warning(f"Could not stop teach mode: {e}")

        try:
            self._api_get("/api/set/enable?jointNum=8&action=2")
            logger.info("Joints disabled.")
        except Exception as e:
            logger.warning(f"Could not disable joints: {e}")

        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass

        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=3)

        for cam in self.cameras.values():
            cam.disconnect()
        self.cameras.clear()

        logger.info("Songzero7Dof disconnected.")

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    # ------------------------------------------------------------------ #
    #  Observation / action
    # ------------------------------------------------------------------ #

    def get_observation(self) -> dict[str, Any]:
        if not self._connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        obs = {}

        with self._lock:
            positions = list(self._latest_positions)
        for name, pos in zip(JOINT_NAMES, positions):
            obs[f"observation.state.{name}"] = pos

        for cam_name, cam in self.cameras.items():
            frame = cam.async_read()
            obs[f"observation.images.{cam_name}"] = frame

        return obs

    def get_joint_state(self) -> dict[str, float]:
        """Return current joint positions keyed by bare joint name (no prefix).

        Used by DragPassthrough teleoperator to mirror robot state as action.
        Example return: {"joint1": 0.12, "joint2": -0.34, ...}
        """
        with self._lock:
            positions = list(self._latest_positions)
        return {name: pos for name, pos in zip(JOINT_NAMES, positions)}

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Drag-teach mode: no-op (arm is moved manually)."""
        if not self._connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        return action

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _api_base(self) -> str:
        return f"http://{self.config.host}"

    def _api_get(self, path: str) -> dict:
        url = self._api_base() + path
        resp = self._session.get(url, timeout=5)
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"API call failed {path}: {data.get('desc', data)}")
        return data

    def _login(self) -> str:
        url = f"http://{self.config.host}/api/login"
        resp = requests.post(
            url,
            json={"username": self.config.username, "password": self.config.password},
            timeout=5,
        )
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Robot login failed: {data}")
        return data["data"]["accessToken"]

    def _enable_arm(self) -> None:
        """Full enable sequence: estop-resume → clear errors → ctrl mode → enable joints → drag mode."""
        logger.info("Enabling arm and starting drag mode...")

        # Resume e-stop (safe to call even if not in e-stop)
        try:
            self._api_get("/api/estop?action=2")
        except Exception:
            pass  # might return error if not in e-stop state

        time.sleep(0.3)

        # Clear errors
        try:
            self._api_get("/api/cleanError?action=1")
        except Exception:
            pass

        time.sleep(0.3)

        # Set teach controller mode (ctrlMode=3)
        self._api_get("/api/setting/setCtrlMode?ctrlMode=3")
        time.sleep(0.5)

        # Enable all 7 joints (jointNum=8 = ALL, action=1 = ENABLE)
        self._api_get("/api/set/enable?jointNum=8&action=1")
        logger.info("All joints enabled.")
        time.sleep(0.5)

        # Start drag teach session (makes the arm compliant / physically moveable)
        # Try each delete action (7 or 8) to remove any previous session, then create new
        for del_action in [7, 8, 4]:
            try:
                self._session.get(
                    self._api_base() + f"/api/teach?action={del_action}&name={_TEACH_SESSION}",
                    timeout=2,
                )
            except Exception:
                pass

        try:
            self._api_get(f"/api/teach?action=1&name={_TEACH_SESSION}")
            logger.info("Drag teach mode active — arm is now compliant.")
        except RuntimeError as e:
            logger.warning(f"Could not start teach session ({e}). Arm may still be moveable in ctrlMode=3.")


    def _start_ws_reader(self) -> None:
        import websocket
        import json

        ws_url = f"ws://{self.config.host}:{self.config.ws_port}"

        def on_message(ws, message):
            try:
                msg = json.loads(message)
                if msg.get("uri") == "/highSpeedStates":
                    positions = msg["data"].get("positions", [])
                    if len(positions) == self.config.num_joints:
                        with self._lock:
                            self._latest_positions = positions
            except Exception:
                pass

        def on_error(ws, error):
            logger.warning(f"WebSocket error: {error}")

        def on_close(ws, *args):
            logger.info("WebSocket closed.")

        def on_open(ws):
            logger.info("WebSocket connected to robot.")

        self._ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )
        self._ws_thread = threading.Thread(
            target=self._ws.run_forever, daemon=True, name="songzero_ws"
        )
        self._ws_thread.start()

        # Wait up to 5s for first position data
        t0 = time.time()
        while time.time() - t0 < 5:
            with self._lock:
                if any(p != 0.0 for p in self._latest_positions):
                    break
            time.sleep(0.05)
        else:
            logger.warning("Timed out waiting for WS data — check robot WiFi connection.")
