"""
Generate three ICRA-style architecture diagrams for Treame README.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties
import numpy as np

_CJK = FontProperties(
    fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
_CJK_B = FontProperties(
    fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')

plt.rcParams.update({'axes.linewidth': 0, 'figure.facecolor': 'white'})

C_BLUE   = '#D6E4F0'
C_GRAY   = '#ECECEC'
C_GREEN  = '#DDE5D0'
C_WHITE  = '#FFFFFF'
C_DARK   = '#1A1A2E'
C_ACCENT = '#2C5F8A'
C_ARROW  = '#444455'


def txt(ax, x, y, s, size=9.5, bold=False, color=C_DARK, ha='center', va='center', **kw):
    fp = _CJK_B if bold else _CJK
    ax.text(x, y, s, ha=ha, va=va, fontsize=size, color=color,
            fontproperties=fp, **kw)


def rbox(ax, x, y, w, h, fc, label, sub=None, lsize=9.5, bold=False,
         ec='#7799AA', lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.015",
                                facecolor=fc, edgecolor=ec,
                                linewidth=lw, zorder=3))
    cy = y + h / 2 + (0.013 if sub else 0)
    txt(ax, x + w/2, cy, label, size=lsize, bold=bold, zorder=4)
    if sub:
        txt(ax, x + w/2, y + h/2 - 0.024, sub,
            size=7.5, color='#555566', zorder=4)


def arr_down(ax, x, y_top, length=0.058):
    ax.annotate('', xy=(x, y_top - length), xytext=(x, y_top),
                arrowprops=dict(arrowstyle='->', color=C_ARROW,
                                lw=1.6, mutation_scale=14), zorder=5)


# ══════════════════════════════════════════════════════════════════════════════
# Fig 1 — Three-layer architecture
# ══════════════════════════════════════════════════════════════════════════════
def fig1():
    fig, ax = plt.subplots(figsize=(8.8, 5.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    layers = [
        (0.04, 0.67, 0.92, 0.28, C_BLUE,  '感知层  Perception'),
        (0.04, 0.37, 0.92, 0.25, C_GRAY,  '控制层  Control'),
        (0.04, 0.07, 0.92, 0.25, C_GREEN, '执行层  Actuation'),
    ]
    for x, y, w, h, c, lbl in layers:
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                   boxstyle="round,pad=0.02",
                                   facecolor=c, edgecolor='#99AABB',
                                   linewidth=1.2, zorder=1))
        txt(ax, x + 0.013, y + h - 0.036, lbl,
            size=9, bold=True, color=C_ACCENT, ha='left', va='top', zorder=2)

    # perception
    pmods = [('USB 摄像头','Camera'),('人体骨骼检测','Body Skeleton'),
             ('人脸关键点','Face Landmarks'),('实时可视化','Web Viz')]
    pw, gap, x0 = 0.196, 0.017, 0.056
    for i,(zh,en) in enumerate(pmods):
        rbox(ax, x0+i*(pw+gap), 0.735, pw, 0.14, C_WHITE, zh, en, lsize=9)

    # control
    cmods = [('pyAgxArm SDK',None),
             ('运动规划','关节 / 直线 / 圆弧'),
             ('坐标变换 SE3','TCP Offset')]
    cw = 0.273
    for i,(zh,en) in enumerate(cmods):
        rbox(ax, x0+i*(cw+gap), 0.425, cw, 0.125, C_WHITE, zh, en, lsize=9)

    # actuation
    amods = [('SocketCAN  1 Mbps','CAN Bus'),
             ('松灵 Nero  7-DOF','AGX Gripper · Revo2 Hand')]
    aw = 0.418
    for i,(zh,en) in enumerate(amods):
        rbox(ax, x0+i*(aw+gap), 0.12, aw, 0.125, C_WHITE, zh, en, lsize=9)

    arr_down(ax, 0.50, 0.67)
    arr_down(ax, 0.50, 0.37)

    txt(ax, 0.50, 0.022,
        'Fig. 1  Treame 三层解耦系统架构  /  Three-Layer Decoupled Architecture',
        size=8.2, color='#333344',
        fontstyle='italic')

    fig.savefig('docs/images/fig1_architecture.png', dpi=180,
                bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('fig1 done')


# ══════════════════════════════════════════════════════════════════════════════
# Fig 2 — Closed-loop control
# ══════════════════════════════════════════════════════════════════════════════
def fig2():
    fig, ax = plt.subplots(figsize=(6.2, 5.8))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    nodes = {'human':(0.50,0.83),'vision':(0.83,0.50),
             'ctrl':(0.50,0.17),'robot':(0.17,0.50)}
    nlabels = {'human':('人体 / 面部','Human / Face'),
               'vision':('视觉感知层','Vision Layer'),
               'ctrl':('机械臂控制层','Control Layer'),
               'robot':('松灵 Nero','7-DOF Arm')}
    ncolors = {'human':C_BLUE,'vision':C_GRAY,'ctrl':C_GRAY,'robot':C_GREEN}
    nw, nh = 0.22, 0.11

    for k,(cx,cy) in nodes.items():
        zh,en = nlabels[k]
        rbox(ax, cx-nw/2, cy-nh/2, nw, nh, ncolors[k], zh, en,
             lsize=9.5, bold=True, ec=C_ACCENT, lw=1.4)

    # clockwise arrows
    arrow_defs = [
        ('human','vision', '关键点数据流', 0.285, 0.765),
        ('vision','ctrl',  '位姿估计',     0.795, 0.285),
        ('ctrl',  'robot', 'CAN 控制指令', 0.21,  0.235),
        ('robot', 'human', '接触 / 反馈',  0.175, 0.755),
    ]
    for src, dst, lbl, tx, ty in arrow_defs:
        sx, sy = nodes[src]; dx, dy = nodes[dst]
        ox = nw/2 * np.sign(dx-sx) if abs(dx-sx)>abs(dy-sy) else 0
        oy = nh/2 * np.sign(dy-sy) if abs(dy-sy)>=abs(dx-sx) else 0
        ax.annotate('', xy=(dx-ox, dy-oy), xytext=(sx+ox, sy+oy),
                    arrowprops=dict(arrowstyle='->', color=C_ARROW,
                                   lw=1.5, mutation_scale=13,
                                   connectionstyle='arc3,rad=0.15'),
                    zorder=5)
        txt(ax, tx, ty, lbl, size=8,
            bbox=dict(boxstyle='round,pad=0.08', fc='white', ec='none', alpha=0.9),
            zorder=6)

    # center box
    ax.add_patch(FancyBboxPatch((0.355,0.445), 0.29, 0.11,
                                boxstyle="round,pad=0.015",
                                facecolor='#EAF2FB', edgecolor=C_ACCENT,
                                linewidth=1.3, zorder=3))
    txt(ax, 0.50, 0.50, '感知驱动实时护理', size=9, bold=True,
        color=C_ACCENT, zorder=4)

    txt(ax, 0.50, 0.022,
        'Fig. 2  感知驱动控制闭环  /  Perception-Driven Closed-Loop Control',
        size=8.2, color='#333344', fontstyle='italic')

    fig.savefig('docs/images/fig2_loop.png', dpi=180,
                bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('fig2 done')


# ══════════════════════════════════════════════════════════════════════════════
# Fig 3 — Modular driver architecture
# ══════════════════════════════════════════════════════════════════════════════
def fig3():
    fig, ax = plt.subplots(figsize=(7.8, 5.8))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    # application
    rbox(ax, 0.18, 0.82, 0.64, 0.11, C_BLUE,
         '护理应用层', '刷牙 · 吹发 · 剃须',
         lsize=10, bold=True, ec=C_ACCENT, lw=1.4)
    arr_down(ax, 0.50, 0.82)
    txt(ax, 0.535, 0.798, '统一 API', size=7.8, color='#555')

    # factory
    rbox(ax, 0.10, 0.645, 0.80, 0.115, '#D0E8F8',
         'AgxArmFactory  +  ArmDriverAbstract',
         'Factory Pattern · Template Method',
         lsize=10, bold=True, ec=C_ACCENT, lw=1.8)

    # three modules
    mxs = [0.07, 0.385, 0.695]; mw = 0.25; gap = 0.02
    mods = [('运动规划模块','Motion Planner'),
            ('协议解析模块','CAN Parser'),
            ('末端执行器模块','End-Effector Driver')]
    for i,(zh,en) in enumerate(mods):
        tx = mxs[i]+mw/2
        ax.annotate('', xy=(tx, 0.575), xytext=(0.50, 0.645),
                    arrowprops=dict(arrowstyle='->', color=C_ARROW,
                                   lw=1.3, mutation_scale=12), zorder=5)
        rbox(ax, mxs[i], 0.44, mw, 0.13, C_GRAY, zh, en, lsize=8.8, ec='#99AABB')

    for i in range(3):
        tx = mxs[i]+mw/2
        ax.annotate('', xy=(0.50, 0.36), xytext=(tx, 0.44),
                    arrowprops=dict(arrowstyle='->', color=C_ARROW,
                                   lw=1.3, mutation_scale=12), zorder=5)

    # CAN + hardware
    rbox(ax, 0.18, 0.24, 0.64, 0.115, C_GREEN,
         'SocketCAN  →  松灵 Nero  7-DOF',
         'AGX Gripper  ·  Revo2 Multi-finger Hand',
         lsize=10, bold=True, ec='#779966', lw=1.4)

    # bracket
    ax.annotate('', xy=(0.945, 0.44), xytext=(0.945, 0.76),
                arrowprops=dict(arrowstyle=']-[', color=C_ACCENT,
                                lw=1.4, mutation_scale=8))
    txt(ax, 0.965, 0.60, '工厂模式\n+\n模板方法',
        size=8, color=C_ACCENT, bold=True, ha='left')

    txt(ax, 0.50, 0.022,
        'Fig. 3  模块化驱动架构与统一接口设计  /  Modular Driver Architecture',
        size=8.2, color='#333344', fontstyle='italic')

    fig.savefig('docs/images/fig3_modules.png', dpi=180,
                bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('fig3 done')


if __name__ == '__main__':
    fig1(); fig2(); fig3()
    print('All figures saved to docs/images/')
