#!/usr/bin/env bash
# tri.me 环境一键初始化脚本
# 用法: bash scripts/setup_env.sh
# 测试环境: Ubuntu 22.04, CUDA 12.1, Python 3.10

set -euo pipefail

CONDA_ENV="trime"
PYTHON_VERSION="3.10"
LEROBOT_REPO="https://github.com/huggingface/lerobot.git"

echo "======================================================"
echo "  tri.me 环境初始化"
echo "======================================================"

# ── 0. 检查 conda ──────────────────────────────────────────────────────────────
if ! command -v conda &>/dev/null; then
    echo "[error] 未找到 conda，请先安装 Miniconda:"
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# ── 1. 创建 conda 环境 ─────────────────────────────────────────────────────────
if conda env list | grep -q "^${CONDA_ENV} "; then
    echo "[skip] conda 环境 '${CONDA_ENV}' 已存在，跳过创建"
else
    echo "[1/5] 创建 conda 环境: ${CONDA_ENV} (Python ${PYTHON_VERSION})"
    conda create -y -n "${CONDA_ENV}" python="${PYTHON_VERSION}"
fi

# 在目标环境中执行后续步骤
CONDA_BASE=$(conda info --base)
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV}"

# ── 2. 安装 PyTorch (CUDA 12.1) ───────────────────────────────────────────────
echo "[2/5] 安装 PyTorch 2.3 + CUDA 12.1"
pip install torch==2.3.1 torchvision==0.18.1 \
    --index-url https://download.pytorch.org/whl/cu121

# ── 3. 安装 lerobot (含 pi0 extra) ────────────────────────────────────────────
echo "[3/5] 安装 lerobot (from source, pi0 extra)"
TMP_DIR=$(mktemp -d)
git clone --depth 1 "${LEROBOT_REPO}" "${TMP_DIR}/lerobot"
pip install -e "${TMP_DIR}/lerobot[pi0]"

# ── 4. 安装其余 Python 依赖 ────────────────────────────────────────────────────
echo "[4/5] 安装 Rerun、h5py 等依赖"
pip install \
    rerun-sdk>=0.16 \
    h5py>=3.11 \
    numpy>=1.26 \
    opencv-python>=4.9 \
    huggingface_hub>=0.23

# ── 5. CAN 总线工具 (系统级) ───────────────────────────────────────────────────
echo "[5/5] 安装 CAN 总线工具"
if command -v apt-get &>/dev/null; then
    sudo apt-get install -y can-utils
else
    echo "[warn] 非 Debian 系统，请手动安装 can-utils"
fi

echo ""
echo "======================================================"
echo "  环境初始化完成！"
echo ""
echo "  激活环境:"
echo "    conda activate ${CONDA_ENV}"
echo ""
echo "  下一步 — 激活 CAN 接口 (需要 root):"
echo "    sudo bash scripts/can_up.sh"
echo ""
echo "  下一步 — 下载基座权重:"
echo "    huggingface-cli download physical-intelligence/pi0.5 \\"
echo "        --local-dir checkpoints/pi0.5"
echo "======================================================"
