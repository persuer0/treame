#!/usr/bin/env bash
# tri.me — 激活 SocketCAN 接口，连通松灵 Nero 机械臂
# 用法: sudo bash scripts/can_up.sh [接口名 默认can0] [波特率 默认1000000]
# 需要 root 权限

set -euo pipefail

IFACE="${1:-can0}"
BITRATE="${2:-1000000}"

echo "[can_up] 配置 ${IFACE} @ ${BITRATE} bps"

# 加载内核模块
modprobe can
modprobe can_raw
modprobe vcan      # 虚拟 CAN，用于无硬件时测试

# 配置物理 CAN 接口
if ip link show "${IFACE}" &>/dev/null; then
    ip link set "${IFACE}" down 2>/dev/null || true
    ip link set "${IFACE}" type can bitrate "${BITRATE}" restart-ms 100
    ip link set "${IFACE}" up
    echo "[can_up] ${IFACE} 已启动 (bitrate=${BITRATE})"
else
    echo "[warn] 接口 ${IFACE} 不存在，可能未连接 USB-CAN 转换器"
    echo "       如需离线测试，启用虚拟 CAN:"
    echo "         sudo ip link add dev vcan0 type vcan"
    echo "         sudo ip link set up vcan0"
    exit 1
fi

# 打印状态
ip -details link show "${IFACE}"
