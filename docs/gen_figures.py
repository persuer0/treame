"""
ICRA-style architecture diagrams for tri.me — redesigned with Okabe-Ito palette,
8pt spacing grid, no text overlap, clean hierarchy.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties
import numpy as np

# ── fonts ─────────────────────────────────────────────────────────────────────
_R = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
_B = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

def T(ax, x, y, s, size=10, bold=False, color='#1a1a1a',
      ha='center', va='center', zorder=6, **kw):
    ax.text(x, y, s, ha=ha, va=va, fontsize=size, color=color,
            fontproperties=(_B if bold else _R), zorder=zorder, **kw)

# ── Okabe-Ito palette ─────────────────────────────────────────────────────────
SKY   = '#56B4E9'   # sky blue   — perception
ORANG = '#E69F00'   # orange     — control
GREEN = '#009E73'   # green      — actuation / hardware
LGRAY = '#F4F4F4'   # light gray — module boxes
DGRAY = '#333333'   # dark       — text
MID   = '#EEEEEE'   # mid gray   — sub-boxes
WHITE = '#FFFFFF'
ARROW = '#555555'

def box(ax, x, y, w, h, fc=WHITE, ec='#888', lw=1.2, radius=0.012, zorder=3):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={radius}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zorder
    ))

def arrow(ax, x0, y0, x1, y1, rad=0.0, lw=1.8, color=ARROW):
    ax.annotate('',
        xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle='->', color=color, lw=lw,
            mutation_scale=16,
            connectionstyle=f'arc3,rad={rad}'
        ), zorder=7)

def label_arrow(ax, x, y, text, size=8.5):
    T(ax, x, y, text, size=size, color='#444444',
      bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.92))


# ══════════════════════════════════════════════════════════════════════════════
# FIG 1 — Three-layer decoupled architecture
# ══════════════════════════════════════════════════════════════════════════════
def fig1():
    W, H = 11, 6
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    fig.patch.set_facecolor(WHITE)

    # ── layer bands ──
    bands = [
        (0.3, 4.15, 10.4, 1.55, SKY+'33',   SKY,   '感知层', 'Perception'),
        (0.3, 2.35, 10.4, 1.55, ORANG+'22', ORANG, '控制层', 'Control'),
        (0.3, 0.45, 10.4, 1.65, GREEN+'22', GREEN, '执行层', 'Actuation'),
    ]
    for x, y, w, h, fc, ec, zh, en in bands:
        box(ax, x, y, w, h, fc=fc, ec=ec, lw=1.6, radius=0.025, zorder=1)
        # layer label — left side
        T(ax, x+0.22, y+h-0.28, zh, size=11, bold=True, color=ec, ha='left', va='top')
        T(ax, x+0.22, y+h-0.54, en, size=8.5, color=ec+'BB', ha='left', va='top')

    # ── perception modules (4 boxes) ──
    pmods = [
        ('USB 摄像头',    'Camera'),
        ('人体骨骼检测', 'Body Skeleton'),
        ('人脸关键点',   'Face Landmarks'),
        ('实时可视化',   'Web Viz'),
    ]
    pw, ph, gap = 2.2, 1.0, 0.22
    px0 = 0.3 + (10.4 - 4*pw - 3*gap) / 2
    for i, (zh, en) in enumerate(pmods):
        bx = px0 + i*(pw+gap)
        by = 4.4
        box(ax, bx, by, pw, ph, fc=WHITE, ec=SKY, lw=1.2, radius=0.015, zorder=4)
        T(ax, bx+pw/2, by+ph*0.62, zh, size=10.5, bold=True, color=DGRAY)
        T(ax, bx+pw/2, by+ph*0.28, en, size=8.5, color='#666666')

    # ── control modules (3 boxes) ──
    cmods = [
        ('pyAgxArm SDK',  'Core SDK'),
        ('运动规划',      '关节 / 直线 / 圆弧'),
        ('坐标变换 SE3',  'TCP Offset'),
    ]
    cw, ch = 3.0, 1.0; cgap = 0.25
    cx0 = 0.3 + (10.4 - 3*cw - 2*cgap) / 2
    for i, (zh, en) in enumerate(cmods):
        bx = cx0 + i*(cw+cgap)
        by = 2.6
        box(ax, bx, by, cw, ch, fc=WHITE, ec=ORANG, lw=1.2, radius=0.015, zorder=4)
        T(ax, bx+cw/2, by+ch*0.64, zh, size=10.5, bold=True, color=DGRAY)
        T(ax, bx+cw/2, by+ch*0.28, en, size=8.5, color='#666666')

    # ── actuation modules (2 boxes) ──
    amods = [
        ('SocketCAN  1 Mbps', 'CAN Bus Protocol'),
        ('松灵 Nero  7-DOF',  'AGX Gripper · Revo2 Hand'),
    ]
    aw, ah = 4.6, 1.1; agap = 0.4
    ax0 = 0.3 + (10.4 - 2*aw - agap) / 2
    for i, (zh, en) in enumerate(amods):
        bx = ax0 + i*(aw+agap)
        by = 0.7
        box(ax, bx, by, aw, ah, fc=WHITE, ec=GREEN, lw=1.2, radius=0.015, zorder=4)
        T(ax, bx+aw/2, by+ah*0.64, zh, size=10.5, bold=True, color=DGRAY)
        T(ax, bx+aw/2, by+ah*0.26, en, size=8.5, color='#666666')

    # ── arrows between layers ──
    arrow(ax, W/2, 4.15, W/2, 3.9)
    arrow(ax, W/2, 2.35, W/2, 2.1)

    # ── caption ──
    T(ax, W/2, 0.16,
      'Fig. 1   tri.me 三层解耦系统架构  /  Three-Layer Decoupled Architecture',
      size=9, color='#555555', bold=False,
      fontstyle='italic')

    fig.savefig('docs/images/fig1_architecture.png', dpi=200,
                bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print('fig1 done ✓')


# ══════════════════════════════════════════════════════════════════════════════
# FIG 2 — Perception-driven closed-loop control
# ══════════════════════════════════════════════════════════════════════════════
def fig2():
    W, H = 8, 7.5
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    fig.patch.set_facecolor(WHITE)

    nw, nh = 2.6, 1.1
    # node centers
    nodes = {
        'human': (W/2,       6.3),
        'vision':(W-1.6,     H/2),
        'ctrl':  (W/2,       1.2),
        'robot': (1.6,       H/2),
    }
    ninfo = {
        'human': ('人体 / 面部', 'Human / Face', SKY,   SKY+'55'),
        'vision':('视觉感知层',  'Vision Layer',  ORANG, ORANG+'33'),
        'ctrl':  ('机械臂控制层','Control Layer', ORANG, ORANG+'33'),
        'robot': ('松灵 Nero',  '7-DOF Arm',     GREEN, GREEN+'33'),
    }
    for k, (cx, cy) in nodes.items():
        zh, en, ec, fc = ninfo[k]
        box(ax, cx-nw/2, cy-nh/2, nw, nh, fc=fc, ec=ec, lw=1.8, radius=0.02, zorder=4)
        T(ax, cx, cy+0.18, zh, size=11.5, bold=True, color=DGRAY)
        T(ax, cx, cy-0.22, en, size=9,    color='#555555')

    # ── arrows (clockwise, offset so they don't pierce box centers) ──
    def edge(src, dst, lbl, lx, ly, rad=0.25):
        sx, sy = nodes[src]; dx, dy = nodes[dst]
        # start/end at box edge approximations
        arrow(ax, sx, sy, dx, dy, rad=rad, lw=1.6, color=ARROW)
        label_arrow(ax, lx, ly, lbl, size=9)

    edge('human', 'vision', '关键点数据流\nKeypoint Stream', 6.55, 6.05, rad=-0.2)
    edge('vision','ctrl',   '位姿估计\nPose Estimation',   6.55, 1.95, rad=-0.2)
    edge('ctrl',  'robot',  'CAN 控制指令\nCAN Command',   1.45, 1.95, rad=-0.2)
    edge('robot', 'human',  '接触 / 反馈\nFeedback',       1.45, 6.05, rad=-0.2)

    # ── center highlight box ──
    cw2, ch2 = 2.8, 1.0
    box(ax, W/2-cw2/2, H/2-ch2/2, cw2, ch2,
        fc='#EAF5FF', ec=SKY, lw=1.5, radius=0.02, zorder=4)
    T(ax, W/2, H/2+0.15, '感知驱动实时护理', size=11, bold=True, color=SKY)
    T(ax, W/2, H/2-0.22, 'Perception-Driven Care', size=8.5, color='#555')

    T(ax, W/2, 0.22,
      'Fig. 2   感知驱动控制闭环  /  Perception-Driven Closed-Loop Control',
      size=9, color='#555555', fontstyle='italic')

    fig.savefig('docs/images/fig2_loop.png', dpi=200,
                bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print('fig2 done ✓')


# ══════════════════════════════════════════════════════════════════════════════
# FIG 3 — Modular driver architecture
# ══════════════════════════════════════════════════════════════════════════════
def fig3():
    W, H = 10, 7
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    fig.patch.set_facecolor(WHITE)

    # ── top: application ──
    aw, ah = 7.0, 1.1
    ax0 = (W - aw) / 2
    box(ax, ax0, 5.7, aw, ah, fc=SKY+'44', ec=SKY, lw=1.8, radius=0.02, zorder=4)
    T(ax, W/2, 5.7+ah*0.65, '护理应用层', size=12, bold=True, color=DGRAY)
    T(ax, W/2, 5.7+ah*0.25, '刷牙 · 吹发 · 剃须  /  Care Application', size=9, color='#555')

    arrow(ax, W/2, 5.7, W/2, 5.35, lw=1.8)
    T(ax, W/2+0.5, 5.52, '统一 API', size=8.5, color='#666')

    # ── middle: factory ──
    fw, fh = 8.2, 1.15
    fx0 = (W - fw) / 2
    box(ax, fx0, 4.05, fw, fh, fc=ORANG+'33', ec=ORANG, lw=1.8, radius=0.02, zorder=4)
    T(ax, W/2, 4.05+fh*0.67, 'AgxArmFactory  +  ArmDriverAbstract',
      size=11.5, bold=True, color=DGRAY)
    T(ax, W/2, 4.05+fh*0.25, 'Factory Pattern  ·  Template Method',
      size=9, color='#666')

    # ── fan-out to three modules ──
    mw, mh = 2.5, 1.1
    mgap = 0.25
    mx0 = (W - 3*mw - 2*mgap) / 2
    mods = [
        ('运动规划模块',   'Motion Planner'),
        ('协议解析模块',   'CAN Parser'),
        ('末端执行器模块', 'End-Effector'),
    ]
    mcenters = []
    for i, (zh, en) in enumerate(mods):
        bx = mx0 + i*(mw+mgap)
        by = 2.7
        mcenters.append(bx + mw/2)
        # fan arrow
        arrow(ax, W/2, 4.05, bx+mw/2, by+mh, rad=0.0 if i==1 else (0.2 if i==2 else -0.2),
              lw=1.4)
        box(ax, bx, by, mw, mh, fc=LGRAY, ec='#AAAAAA', lw=1.1, radius=0.015, zorder=4)
        T(ax, bx+mw/2, by+mh*0.65, zh, size=10, bold=True, color=DGRAY)
        T(ax, bx+mw/2, by+mh*0.26, en, size=8.5, color='#666')

    # ── converge to CAN + hardware ──
    hw, hh = 7.0, 1.15
    hx0 = (W - hw) / 2
    hy = 1.2
    for mcx in mcenters:
        arrow(ax, mcx, 2.7, W/2, hy+hh, rad=0.0, lw=1.4)
    box(ax, hx0, hy, hw, hh, fc=GREEN+'44', ec=GREEN, lw=1.8, radius=0.02, zorder=4)
    T(ax, W/2, hy+hh*0.67, 'SocketCAN  →  松灵 Nero  7-DOF',
      size=11.5, bold=True, color=DGRAY)
    T(ax, W/2, hy+hh*0.26, 'AGX Gripper  ·  Revo2 Multi-finger Hand',
      size=9, color='#555')

    # ── right bracket annotation ──
    bx_r = W - 0.55
    ax.annotate('', xy=(bx_r, 2.65), xytext=(bx_r, 5.2),
                arrowprops=dict(arrowstyle=']-[', color=ORANG, lw=1.6, mutation_scale=10))
    T(ax, bx_r+0.38, 3.92, '工厂模式\n+\n模板方法', size=8.5,
      bold=True, color=ORANG, ha='left')

    T(ax, W/2, 0.28,
      'Fig. 3   模块化驱动架构与统一接口设计  /  Modular Driver Architecture',
      size=9, color='#555555', fontstyle='italic')

    fig.savefig('docs/images/fig3_modules.png', dpi=200,
                bbox_inches='tight', facecolor=WHITE)
    plt.close(fig)
    print('fig3 done ✓')


if __name__ == '__main__':
    fig1(); fig2(); fig3()
    print('\nAll figures saved → docs/images/')
