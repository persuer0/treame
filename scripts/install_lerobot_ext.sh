#!/usr/bin/env bash
# tri.me — 将 lerobot_ext/ 中的扩展安装进 lerobot 源码
#
# 做三件事:
#   1. 找到当前 conda 环境中 lerobot 的安装路径
#   2. 将 songzero7dof / drag_passthrough 目录 symlink 进去
#   3. 在 lerobot 的 __init__.py 中追加 import，使注册表生效
#
# 用法:
#   conda activate trime
#   bash scripts/install_lerobot_ext.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXT_DIR="${REPO_ROOT}/lerobot_ext"

# ── 1. 找 lerobot 安装路径 ────────────────────────────────────────────────────
LEROBOT_DIR=$(python3 -c "import lerobot; import os; print(os.path.dirname(lerobot.__file__))" 2>/dev/null || true)
if [[ -z "${LEROBOT_DIR}" ]]; then
    echo "[error] 未找到 lerobot，请先激活环境并运行 setup_env.sh"
    exit 1
fi
echo "[install_ext] lerobot 路径: ${LEROBOT_DIR}"

# ── 2. Symlink robot 驱动 ──────────────────────────────────────────────────────
ROBOT_SRC="${EXT_DIR}/robots/songzero7dof"
ROBOT_DST="${LEROBOT_DIR}/robots/songzero7dof"

if [[ -L "${ROBOT_DST}" ]]; then
    echo "[skip] ${ROBOT_DST} 已存在（symlink），跳过"
elif [[ -d "${ROBOT_DST}" ]]; then
    echo "[warn] ${ROBOT_DST} 已作为普通目录存在，跳过"
else
    ln -s "${ROBOT_SRC}" "${ROBOT_DST}"
    echo "[ok] robot symlink: ${ROBOT_DST} -> ${ROBOT_SRC}"
fi

# ── 3. Symlink teleop 驱动 ────────────────────────────────────────────────────
TELEOP_SRC="${EXT_DIR}/teleoperators/drag_passthrough"
TELEOP_DST="${LEROBOT_DIR}/teleoperators/drag_passthrough"

if [[ -L "${TELEOP_DST}" ]]; then
    echo "[skip] ${TELEOP_DST} 已存在（symlink），跳过"
elif [[ -d "${TELEOP_DST}" ]]; then
    echo "[warn] ${TELEOP_DST} 已作为普通目录存在，跳过"
else
    ln -s "${TELEOP_SRC}" "${TELEOP_DST}"
    echo "[ok] teleop symlink: ${TELEOP_DST} -> ${TELEOP_SRC}"
fi

# ── 4. Patch lerobot/robots/__init__.py ───────────────────────────────────────
ROBOTS_INIT="${LEROBOT_DIR}/robots/__init__.py"
ROBOT_IMPORT="from lerobot.robots import songzero7dof  # tri.me ext"

if grep -qF "songzero7dof" "${ROBOTS_INIT}" 2>/dev/null; then
    echo "[skip] robots/__init__.py 已含 songzero7dof"
else
    echo "" >> "${ROBOTS_INIT}"
    echo "${ROBOT_IMPORT}" >> "${ROBOTS_INIT}"
    echo "[ok] patched: ${ROBOTS_INIT}"
fi

# ── 5. Patch lerobot/teleoperators/__init__.py ────────────────────────────────
TELEOPS_INIT="${LEROBOT_DIR}/teleoperators/__init__.py"
TELEOP_IMPORT="from lerobot.teleoperators import drag_passthrough  # tri.me ext"

if grep -qF "drag_passthrough" "${TELEOPS_INIT}" 2>/dev/null; then
    echo "[skip] teleoperators/__init__.py 已含 drag_passthrough"
else
    echo "" >> "${TELEOPS_INIT}"
    echo "${TELEOP_IMPORT}" >> "${TELEOPS_INIT}"
    echo "[ok] patched: ${TELEOPS_INIT}"
fi

# ── 6. 验证 ───────────────────────────────────────────────────────────────────
echo ""
echo "[verify] 导入测试..."
python3 -c "
from lerobot.robots.songzero7dof import Songzero7Dof, Songzero7DofConfig
from lerobot.teleoperators.drag_passthrough import DragPassthrough, DragPassthroughConfig
print('[verify] OK — songzero7dof 和 drag_passthrough 均可导入')
"

echo ""
echo "======================================================"
echo "  lerobot 扩展安装完成！"
echo ""
echo "  采集命令示例:"
echo "    python scripts/record_songzero.py \\"
echo "        --task brushing \\"
echo "        --repo-id <hf_user>/trime-brushing \\"
echo "        --episodes 50"
echo "======================================================"
