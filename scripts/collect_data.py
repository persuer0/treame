"""
tri.me — LeRobot 数据采集脚本（含 Rerun 实时可视化）

用法:
    python scripts/collect_data.py \
        --task brushing \
        --episode 0 \
        --output data/lerobot \
        [--rerun]

依赖:
    pip install lerobot rerun-sdk
"""

import argparse
import time
from pathlib import Path

import numpy as np


# ── 可选依赖：Rerun ────────────────────────────────────────────────────────────
def _init_rerun(task: str) -> bool:
    try:
        import rerun as rr
        rr.init(f"tri.me/{task}", spawn=True)
        return True
    except ImportError:
        print("[warn] rerun-sdk not installed, skipping visualization")
        return False


def _log_rerun(frame_idx: int, rgb: np.ndarray, joints: np.ndarray) -> None:
    import rerun as rr
    rr.set_time_sequence("frame", frame_idx)
    rr.log("camera/rgb", rr.Image(rgb))
    rr.log(
        "robot/joints",
        rr.BarChart(joints),
    )


# ── 采集主循环 ─────────────────────────────────────────────────────────────────
def collect_episode(
    task: str,
    episode_idx: int,
    output_dir: Path,
    use_rerun: bool,
    fps: int = 30,
) -> None:
    """采集单条 episode，保存为 LeRobot HDF5 格式。"""
    try:
        from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
    except ImportError as e:
        raise SystemExit(
            "请先安装 lerobot: pip install lerobot"
        ) from e

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    has_rerun = _init_rerun(task) if use_rerun else False

    print(f"[tri.me] 开始采集: task={task}  episode={episode_idx}  fps={fps}")
    print("按 Ctrl+C 结束本条 episode\n")

    frames = []
    frame_idx = 0

    try:
        while True:
            t0 = time.time()

            # ── TODO: 替换为真实传感器读取 ─────────────────────────────────────
            rgb = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)  # 摄像头帧
            joints = np.random.randn(7).astype(np.float32)                  # 7-DOF 关节角
            action = np.random.randn(7).astype(np.float32)                  # 期望动作
            # ───────────────────────────────────────────────────────────────────

            frames.append(
                {
                    "observation.image": rgb,
                    "observation.state": joints,
                    "action": action,
                    "timestamp": frame_idx / fps,
                }
            )

            if has_rerun:
                _log_rerun(frame_idx, rgb, joints)

            frame_idx += 1
            elapsed = time.time() - t0
            time.sleep(max(0.0, 1 / fps - elapsed))

    except KeyboardInterrupt:
        pass

    print(f"\n[tri.me] 采集结束，共 {len(frames)} 帧，正在保存…")
    _save_episode(frames, task, episode_idx, output_dir)
    print(f"[tri.me] 已保存至 {output_dir}/{task}/episode_{episode_idx:04d}.hdf5")


def _save_episode(
    frames: list,
    task: str,
    episode_idx: int,
    output_dir: Path,
) -> None:
    try:
        import h5py
    except ImportError:
        raise SystemExit("请安装 h5py: pip install h5py")

    ep_dir = output_dir / task
    ep_dir.mkdir(parents=True, exist_ok=True)
    ep_path = ep_dir / f"episode_{episode_idx:04d}.hdf5"

    with h5py.File(ep_path, "w") as f:
        for key in frames[0]:
            data = np.stack([fr[key] for fr in frames])
            f.create_dataset(key, data=data, compression="gzip")


# ── CLI ────────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="tri.me LeRobot 数据采集")
    p.add_argument("--task", choices=["brushing", "drying", "shaving"], required=True)
    p.add_argument("--episode", type=int, default=0, help="episode 编号")
    p.add_argument("--output", default="data/lerobot", help="数据保存目录")
    p.add_argument("--fps", type=int, default=30, help="采集频率 (Hz)")
    p.add_argument("--rerun", action="store_true", help="启动 Rerun 实时可视化")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    collect_episode(
        task=args.task,
        episode_idx=args.episode,
        output_dir=Path(args.output),
        use_rerun=args.rerun,
        fps=args.fps,
    )
