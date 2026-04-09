"""
tri.me — π0.5 推理脚本

从 HuggingFace 加载 physical-intelligence/pi0.5 基座权重，
对当前摄像头帧 + 关节状态运行一步推理，输出 7-DOF 动作。

用法:
    python scripts/infer_pi05.py \
        --task brushing \
        [--checkpoint physical-intelligence/pi0.5] \
        [--device cuda]

依赖:
    pip install lerobot torch torchvision

基座权重:
    https://huggingface.co/physical-intelligence/pi0.5
"""

import argparse
import time
from pathlib import Path

import numpy as np
import torch


# ── 模型加载 ───────────────────────────────────────────────────────────────────
def load_policy(checkpoint: str, device: str):
    """
    从 HuggingFace Hub 或本地路径加载 pi0.5 策略。

    checkpoint 示例:
        "physical-intelligence/pi0.5"          # HuggingFace Hub
        "/path/to/local/pi05_checkpoint"       # 本地目录
    """
    try:
        from lerobot.common.policies.pi0 import PI0Policy
    except ImportError as e:
        raise SystemExit(
            "请先安装 lerobot (含 pi0 支持): pip install lerobot"
        ) from e

    print(f"[tri.me] 加载模型: {checkpoint}")
    policy = PI0Policy.from_pretrained(checkpoint)
    policy = policy.to(device)
    policy.eval()
    print(f"[tri.me] 模型已加载至 {device}\n")
    return policy


# ── 推理循环 ───────────────────────────────────────────────────────────────────
def infer_loop(
    policy,
    task: str,
    device: str,
    fps: int = 30,
    steps: int = 200,
) -> None:
    """
    实时推理循环：读取传感器 → 运行 π0.5 → 发送动作。

    steps=-1 表示无限循环直到 Ctrl+C。
    """
    print(f"[tri.me] 开始推理: task={task}  fps={fps}  steps={steps}")
    print("按 Ctrl+C 停止\n")

    step = 0
    try:
        while steps < 0 or step < steps:
            t0 = time.time()

            # ── TODO: 替换为真实传感器读取 ─────────────────────────────────────
            rgb = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            joints = np.random.randn(7).astype(np.float32)
            # ───────────────────────────────────────────────────────────────────

            obs = _build_obs(rgb, joints, task, device)

            with torch.no_grad():
                action = policy.select_action(obs)  # shape: (7,)

            action_np = action.cpu().numpy()

            # ── TODO: 替换为真实机械臂控制 ─────────────────────────────────────
            _send_action(action_np)
            # ───────────────────────────────────────────────────────────────────

            elapsed = time.time() - t0
            if step % fps == 0:
                print(
                    f"step {step:4d} | action mean={action_np.mean():.4f} "
                    f"| latency={elapsed*1000:.1f}ms"
                )

            time.sleep(max(0.0, 1 / fps - elapsed))
            step += 1

    except KeyboardInterrupt:
        print(f"\n[tri.me] 推理停止，共运行 {step} 步")


def _build_obs(
    rgb: np.ndarray,
    joints: np.ndarray,
    task: str,
    device: str,
) -> dict:
    """将原始传感器数据转为 LeRobot 策略所需的 obs dict。"""
    import torchvision.transforms.functional as TF

    image = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0  # (3,H,W)
    image = TF.resize(image, [224, 224])
    image = image.unsqueeze(0).to(device)  # (1,3,H,W)

    state = torch.from_numpy(joints).unsqueeze(0).to(device)  # (1,7)

    return {
        "observation.image": image,
        "observation.state": state,
        "task": [task],
    }


def _send_action(action: np.ndarray) -> None:
    """占位：将动作发送至机械臂。替换为 pyAgxArm 调用。"""
    _ = action  # noqa: F841


# ── CLI ────────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="tri.me π0.5 推理")
    p.add_argument("--task", choices=["brushing", "drying", "shaving"], required=True)
    p.add_argument(
        "--checkpoint",
        default="physical-intelligence/pi0.5",
        help="HuggingFace 模型 ID 或本地路径",
    )
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--fps", type=int, default=30, help="推理频率 (Hz)")
    p.add_argument("--steps", type=int, default=-1, help="推理步数 (-1=无限)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    policy = load_policy(args.checkpoint, args.device)
    infer_loop(
        policy=policy,
        task=args.task,
        device=args.device,
        fps=args.fps,
        steps=args.steps,
    )
