"""
tri.me — Songzero 7DOF 拖动示教采集脚本

在 lerobot-record 基础上自动完成：
  - robot (Songzero7Dof) 与 teleop (DragPassthrough) 的创建与绑定
  - 采集期间 Rerun 实时可视化（可选）
  - 结束后自动上传 HuggingFace Hub（可选）

前置:
    conda activate trime
    bash scripts/install_lerobot_ext.sh   # 首次运行前执行一次
    sudo bash scripts/can_up.sh           # 如果走 CAN 控制（WiFi 模式不需要）

用法:
    python scripts/record_songzero.py \\
        --task brushing \\
        --repo-id <hf_username>/trime-brushing \\
        --episodes 50 \\
        --host 192.168.31.1 \\
        [--rerun] \\
        [--no-push]

数据保存至: data/lerobot/<repo-id>/
"""

import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="tri.me Songzero 拖动示教采集")
    p.add_argument("--task", choices=["brushing", "drying", "shaving"], required=True,
                   help="采集任务类型")
    p.add_argument("--repo-id", required=True,
                   help="HuggingFace dataset repo，格式 <user>/<name>")
    p.add_argument("--episodes", type=int, default=50,
                   help="采集 episode 数量")
    p.add_argument("--episode-time", type=int, default=60,
                   help="每条 episode 采集时长 (秒)")
    p.add_argument("--reset-time", type=int, default=30,
                   help="每条 episode 后环境复位等待时长 (秒)")
    p.add_argument("--fps", type=int, default=30,
                   help="采集频率 (Hz)")
    p.add_argument("--host", default="192.168.31.1",
                   help="Songzero 控制器 IP")
    p.add_argument("--root", default="data/lerobot",
                   help="数据集本地保存根目录")
    p.add_argument("--rerun", action="store_true",
                   help="启动 Rerun 实时可视化")
    p.add_argument("--no-push", action="store_true",
                   help="不上传 HuggingFace Hub")
    p.add_argument("--resume", action="store_true",
                   help="断点续采（在已有 dataset 上继续）")
    return p.parse_args()


def build_task_description(task: str) -> str:
    return {
        "brushing": "Robot brushes human teeth along upper and lower arcs.",
        "drying":   "Robot dries human hair with a handheld dryer, following head motion.",
        "shaving":  "Robot shaves human face along cheek and jaw contours.",
    }[task]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args()

    # ── 导入 lerobot（扩展必须已安装）────────────────────────────────────────
    try:
        from lerobot.robots.songzero7dof import Songzero7Dof, Songzero7DofConfig
        from lerobot.teleoperators.drag_passthrough import DragPassthrough, DragPassthroughConfig
    except ImportError as e:
        raise SystemExit(
            f"导入失败: {e}\n"
            "请先运行: bash scripts/install_lerobot_ext.sh"
        ) from e

    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from lerobot.datasets.pipeline_features import (
        aggregate_pipeline_dataset_features,
        create_initial_features,
    )
    from lerobot.datasets.utils import combine_feature_dicts
    from lerobot.datasets.video_utils import VideoEncodingManager
    from lerobot.processor import make_default_processors
    from lerobot.utils.control_utils import (
        init_keyboard_listener,
        is_headless,
        sanity_check_dataset_name,
        sanity_check_dataset_robot_compatibility,
    )
    from lerobot.utils.utils import init_logging, log_say
    from lerobot.utils.visualization_utils import init_rerun, log_rerun_data

    init_logging()

    # ── 构建 robot & teleop ───────────────────────────────────────────────────
    robot_cfg = Songzero7DofConfig(host=args.host)
    robot = Songzero7Dof(robot_cfg)

    teleop_cfg = DragPassthroughConfig()
    teleop = DragPassthrough(teleop_cfg)
    teleop.set_robot(robot)          # 绑定：teleop 从 robot 读关节角作为 action

    # ── 处理器（默认 Identity）────────────────────────────────────────────────
    teleop_action_processor, robot_action_processor, robot_observation_processor = (
        make_default_processors()
    )

    # ── 特征描述 ──────────────────────────────────────────────────────────────
    dataset_features = combine_feature_dicts(
        aggregate_pipeline_dataset_features(
            pipeline=teleop_action_processor,
            initial_features=create_initial_features(action=robot.action_features),
            use_videos=True,
        ),
        aggregate_pipeline_dataset_features(
            pipeline=robot_observation_processor,
            initial_features=create_initial_features(observation=robot.observation_features),
            use_videos=True,
        ),
    )

    # ── 创建或恢复 dataset ────────────────────────────────────────────────────
    root = Path(args.root)
    num_cameras = len(robot_cfg.cameras)

    if args.resume:
        dataset = LeRobotDataset(args.repo_id, root=root)
        sanity_check_dataset_robot_compatibility(dataset, robot, args.fps, dataset_features)
    else:
        sanity_check_dataset_name(args.repo_id, policy=None)
        dataset = LeRobotDataset.create(
            args.repo_id,
            args.fps,
            root=root,
            robot_type=robot.name,
            features=dataset_features,
            use_videos=True,
            image_writer_processes=0,
            image_writer_threads=4 * num_cameras,
        )

    # ── Rerun 可视化 ──────────────────────────────────────────────────────────
    if args.rerun:
        init_rerun(session_name=f"trime/{args.task}")

    # ── 连接 ──────────────────────────────────────────────────────────────────
    robot.connect()
    teleop.connect()

    listener, events = init_keyboard_listener()

    # ── 采集主循环 ────────────────────────────────────────────────────────────
    # 延迟导入避免循环依赖
    from lerobot.scripts.record import record_loop  # lerobot >= 0.3

    task_desc = build_task_description(args.task)
    logger.info(f"任务: {task_desc}")
    logger.info("键盘控制: [Space] 提前结束当前 episode  [q] 停止采集  [r] 重录当前 episode")

    with VideoEncodingManager(dataset):
        recorded = 0
        while recorded < args.episodes and not events["stop_recording"]:
            log_say(f"Recording episode {dataset.num_episodes}", play_sounds=True)
            record_loop(
                robot=robot,
                events=events,
                fps=args.fps,
                teleop_action_processor=teleop_action_processor,
                robot_action_processor=robot_action_processor,
                robot_observation_processor=robot_observation_processor,
                dataset=dataset,
                teleop=teleop,
                control_time_s=args.episode_time,
                single_task=task_desc,
                display_data=args.rerun,
            )

            if not events["stop_recording"] and (
                recorded < args.episodes - 1 or events["rerecord_episode"]
            ):
                log_say("Reset the environment", play_sounds=True)
                record_loop(
                    robot=robot,
                    events=events,
                    fps=args.fps,
                    teleop_action_processor=teleop_action_processor,
                    robot_action_processor=robot_action_processor,
                    robot_observation_processor=robot_observation_processor,
                    teleop=teleop,
                    control_time_s=args.reset_time,
                    single_task=task_desc,
                    display_data=args.rerun,
                )

            if events["rerecord_episode"]:
                events["rerecord_episode"] = False
                events["exit_early"] = False
                dataset.clear_episode_buffer()
                continue

            dataset.save_episode()
            recorded += 1
            logger.info(f"已采集 {recorded}/{args.episodes} episodes")

    # ── 断开 & 上传 ───────────────────────────────────────────────────────────
    robot.disconnect()
    teleop.disconnect()

    if not is_headless() and listener is not None:
        listener.stop()

    if not args.no_push:
        logger.info("上传至 HuggingFace Hub...")
        dataset.push_to_hub(tags=["tri.me", args.task, "drag-teach"], private=False)
        logger.info(f"上传完成: https://huggingface.co/datasets/{args.repo_id}")
    else:
        logger.info(f"数据集已保存至本地: {root / args.repo_id}")


if __name__ == "__main__":
    main()
