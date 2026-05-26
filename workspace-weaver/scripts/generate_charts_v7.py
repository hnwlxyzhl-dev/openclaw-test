#!/usr/bin/env python3
"""V7.1 - 修复贯穿示例数据逻辑：A1 是唯一高温异常"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = '#0B1A2E'
plt.rcParams['axes.facecolor'] = '#0E1F35'
plt.rcParams['text.color'] = 'white'
plt.rcParams['axes.labelcolor'] = '#7A8EA8'
plt.rcParams['xtick.color'] = '#4A5E78'
plt.rcParams['ytick.color'] = '#4A5E78'

OUT = '/home/admin/.openclaw/workspace-weaver/output/charts_v7'
os.makedirs(OUT, exist_ok=True)

BG = '#0B1A2E'; CARD = '#12253F'; GREEN = '#00E676'; CYAN = '#00D4FF'
ORANGE = '#FF6B35'; RED = '#FF4444'; YELLOW = '#FFD700'; WHITE = '#FFFFFF'
LGRAY = '#B0C4DE'; MGRAY = '#7A8EA8'; DGRAY = '#4A5E78'

np.random.seed(42)

# ══ 修正后的贯穿示例数据 ══
# 正常设备：980台，温度 60~75°C，振动 2~5 Hz
normal_temps = np.random.normal(67.5, 4.0, 980).clip(58, 78)
normal_vibs = np.random.normal(3.5, 0.8, 980).clip(1.5, 5.5)

# 异常设备：20台
# 关键：A1 是唯一高温异常（95°C），其他异常都 ≤ 78°C
anomaly_data = [
    (95, 3.2, 'A1 过热'),    # ★ 唯一高温异常！温度远超正常范围
    (48, 13.5, 'A2 松动'),   # 温度偏低 + 振动异常高
    (62, 0.2, 'A3 卡死'),    # 温度正常但振动极低
    # 其他异常：低温或振动异常，温度都在 35~78 之间
    (42, 11.2, ''), (35, 4.0, ''), (52, 14.8, ''),
    (78, 0.3, ''), (40, 7.2, ''), (55, 12.0, ''),
    (38, 9.5, ''), (72, 14.0, ''), (45, 3.5, ''),
    (58, 8.5, ''), (50, 0.5, ''), (68, 12.5, ''),
    (55, 0.8, ''), (42, 9.0, ''), (65, 14.2, ''),
    (70, 0.3, ''), (48, 10.5, ''),
]

anomaly_temps = [d[0] for d in anomaly_data]
anomaly_vibs = [d[1] for d in anomaly_data]

# 验证逻辑：T=85 分割线
right_count = sum(1 for t in anomaly_temps if t >= 85)
left_count = sum(1 for t in anomaly_temps if t < 85)
print(f"验证 T=85 分割：右侧(>=85)={right_count}台异常, 左侧(<85)={left_count}台异常")
assert right_count == 1, f"右侧应该只有A1，实际有{right_count}台！"
print("✅ 逻辑验证通过：T=85 分割后右侧只有 A1(95°C)")

# ══════════════════════════════════════
# Chart 1: 封面散点图
# ══════════════════════════════════════
fig, ax = plt.subplots(1, 1, figsize=(6, 5.5), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor('#0A1525')
ax.scatter(normal_temps, normal_vibs, s=12, c=CYAN, alpha=0.35, edgecolors='none', zorder=2)
ax.scatter(anomaly_temps, anomaly_vibs, s=60, c=ORANGE, alpha=0.9, edgecolors=WHITE, linewidth=0.5, zorder=3)
for temp, vib, name in anomaly_data[:3]:
    if name:
        ax.annotate(name, (temp, vib), textcoords="offset points", xytext=(10, 8),
                    fontsize=9, color=WHITE, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color=ORANGE, lw=0.8))
ax.set_xlabel('温度 (°C)', fontsize=10, labelpad=8)
ax.set_ylabel('振动频率 (Hz)', fontsize=10, labelpad=8)
ax.set_xlim(25, 105); ax.set_ylim(-0.5, 16)
ax.spines['bottom'].set_color('#1A3A5C'); ax.spines['left'].set_color('#1A3A5C')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.grid(True, alpha=0.15, color='#1A3A5C', linestyle='--')
ax.text(0.02, 0.98, f'980 正常设备', transform=ax.transAxes, fontsize=9, color=CYAN, va='top', fontweight='bold')
ax.text(0.02, 0.93, f'20 异常设备', transform=ax.transAxes, fontsize=9, color=ORANGE, va='top', fontweight='bold')
plt.tight_layout(pad=0.5)
fig.savefig(f'{OUT}/cover_scatter.png', dpi=200, bbox_inches='tight', facecolor=BG)
plt.close()
print('✅ cover_scatter.png')

# ══════════════════════════════════════
# Chart 2: 核心思想 — T=85 分割线
# ══════════════════════════════════════
fig, ax = plt.subplots(1, 1, figsize=(5.5, 5), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor('#0A1525')
ax.scatter(normal_temps, normal_vibs, s=10, c=CYAN, alpha=0.3, edgecolors='none', zorder=2)
ax.scatter(anomaly_temps, anomaly_vibs, s=50, c=ORANGE, alpha=0.85, edgecolors=WHITE, linewidth=0.5, zorder=3)

# 分割线 T=85
ax.axvline(x=85, color=GREEN, linewidth=2.5, linestyle='--', alpha=0.9, zorder=4)
ax.axvspan(85, 105, alpha=0.08, color=GREEN, zorder=1)

# 标注 — 现在 T=85 右侧只有 A1！
ax.text(85.5, 15, 'T=85°C', color=GREEN, fontsize=11, fontweight='bold', va='top')
ax.text(62, 8, '左侧：999 台\n(980 正常 + 19 异常)', color=CYAN, fontsize=10, va='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A1525', edgecolor=CYAN, alpha=0.8))
ax.text(90, 8, '右侧\n仅 A1\n1 台', color=ORANGE, fontsize=11, fontweight='bold', va='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#0A1525', edgecolor=ORANGE, alpha=0.8))

for temp, vib, name in anomaly_data[:3]:
    if name:
        ax.annotate(name, (temp, vib), textcoords="offset points", xytext=(10, 8),
                    fontsize=8, color=WHITE, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color=ORANGE, lw=0.8))

ax.set_xlabel('温度 (°C)', fontsize=10, labelpad=8)
ax.set_ylabel('振动频率 (Hz)', fontsize=10, labelpad=8)
ax.set_xlim(25, 105); ax.set_ylim(-0.5, 16)
ax.spines['bottom'].set_color('#1A3A5C'); ax.spines['left'].set_color('#1A3A5C')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.grid(True, alpha=0.12, color='#1A3A5C', linestyle='--')
plt.tight_layout(pad=0.5)
fig.savefig(f'{OUT}/core_idea_scatter.png', dpi=200, bbox_inches='tight', facecolor=BG)
plt.close()
print('✅ core_idea_scatter.png')

# ══════════════════════════════════════
# Chart 3: iTree 树形图 — 修正逻辑
# ══════════════════════════════════════
fig, ax = plt.subplots(1, 1, figsize=(6.5, 4.5), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis('off')

def draw_tree_node(ax, x, y, text, color='#1A3A5C', border=CYAN, text_color=WHITE, fs=9, w=1.6, h=0.45):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle="round,pad=0.05", facecolor=color,
                           edgecolor=border, linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, color=text_color, fontweight='bold')

def draw_tree_edge(ax, x1, y1, x2, y2, color=MGRAY):
    ax.plot([x1, x1], [y1, (y1+y2)/2], color=color, lw=1.2)
    ax.plot([x1, x2], [(y1+y2)/2, (y1+y2)/2], color=color, lw=1.2)
    ax.plot([x2, x2], [(y1+y2)/2, y2], color=color, lw=1.2)

def draw_label(ax, x, y, text, color=GREEN, fs=8):
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, color=color)

# 树结构（基于修正后的数据）：
# Root: 温度 < 85? (256)
#   Right(否): A1(过热) [size=1]  路径=1
#   Left(是): 振动 < 6.5? (255)
#     Right(否): A2(松动) [size~1]  路径=2
#     Left(是): 振动 < 1.5? (~253)
#       Left(是): A3(卡死) [size=1]  路径=3
#       Right(否): ~252 台正常 → ...

L0y = 5.2; root_x = 5.0
L1y = 4.0; L1L = 2.8; L1R = 7.2
L2y = 2.8; L2L = 1.5; L2R = 4.1
L3y = 1.6; L3L = 3.0; L3R = 5.2

# Root
draw_tree_node(ax, root_x, L0y, '温度 < 85?  (256)', border=GREEN, fs=10, w=1.8)
# Root -> L1
draw_tree_edge(ax, root_x, L0y-0.225, L1L, L1y+0.225)
draw_tree_edge(ax, root_x, L0y-0.225, L1R, L1y+0.225)
draw_label(ax, (root_x+L1L)/2, L0y-0.35, 'Yes', GREEN)
draw_label(ax, (root_x+L1R)/2, L0y-0.35, 'No', ORANGE)

# L1R: A1 被孤立！
draw_tree_node(ax, L1R, L1y, 'A1(过热) [size=1]', color='#3A1A0A', border=RED, text_color=RED, fs=10)
ax.text(L1R, L1y-0.45, 'path = 1', ha='center', fontsize=10, color=RED, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#3A1A0A', edgecolor=RED, alpha=0.8))

# L1L: 继续分
draw_tree_node(ax, L1L, L1y, '振动 < 6.5?  (255)', border=CYAN, fs=10)
draw_tree_edge(ax, L1L, L1y-0.225, L2L, L2y+0.225)
draw_tree_edge(ax, L1L, L1y-0.225, L2R, L2y+0.225)
draw_label(ax, (L1L+L2L)/2, L1y-0.35, 'No', ORANGE)
draw_label(ax, (L1L+L2R)/2, L1y-0.35, 'Yes', GREEN)

# L2L: A2 被孤立
draw_tree_node(ax, L2L, L2y, 'A2(松动) [size=1]', color='#3A1A0A', border=ORANGE, text_color=ORANGE, fs=10)
ax.text(L2L, L2y-0.45, 'path = 2', ha='center', fontsize=10, color=ORANGE, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#3A1A0A', edgecolor=ORANGE, alpha=0.8))

# L2R: 继续
draw_tree_node(ax, L2R, L2y, '振动 < 1.5?  (~253)', border=CYAN, fs=10)
draw_tree_edge(ax, L2R, L2y-0.225, L3L, L3y+0.225)
draw_tree_edge(ax, L2R, L2y-0.225, L3R, L3y+0.225)
draw_label(ax, (L2R+L3L)/2, L2y-0.35, 'Yes', GREEN)
draw_label(ax, (L2R+L3R)/2, L2y-0.35, 'No', ORANGE)

# L3L: A3
draw_tree_node(ax, L3L, L3y, 'A3(卡死) [size=1]', color='#3A2A0A', border=YELLOW, text_color=YELLOW, fs=10)
ax.text(L3L, L3y-0.45, 'path = 3', ha='center', fontsize=10, color=YELLOW, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#3A2A0A', edgecolor=YELLOW, alpha=0.8))

# L3R: 正常设备
draw_tree_node(ax, L3R, L3y, '~252 正常  -->  ...', color='#0A2A15', border=GREEN, text_color=MGRAY, fs=10)

# 底部说明
ax.text(5.0, 0.4, 'A1(95) 在根部被孤立(path=1), A2(48,13.5) 振动异常(path=2), A3(62,0.2) 振动极低(path=3)',
        ha='center', fontsize=9, color=MGRAY, style='italic')

plt.tight_layout(pad=0.3)
fig.savefig(f'{OUT}/itree_diagram.png', dpi=200, bbox_inches='tight', facecolor=BG)
plt.close()
print('✅ itree_diagram.png')

# ══════════════════════════════════════
# Chart 4: 异常分数对比
# ══════════════════════════════════════
fig, ax = plt.subplots(1, 1, figsize=(5.5, 3.5), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor('#0E1F35')

# A1 高温(95) -> 最容易孤立 -> path最短 -> 分数最高
# A2 两个维度偏离 -> 也很容易孤立
# A3 只有一个维度偏离 -> 较难孤立
# P 正常 -> 最难孤立
devices = ['A1 过热\n(95, 3.2)', 'A2 松动\n(48, 13.5)', 'A3 卡死\n(62, 0.2)', 'P 正常\n(68, 3.8)']
scores = [0.82, 0.74, 0.58, 0.44]
colors_bar = [RED, ORANGE, YELLOW, CYAN]

bars = ax.barh(devices, scores, color=colors_bar, height=0.6, edgecolor='none', alpha=0.85)
ax.set_xlim(0, 1)
ax.axvline(x=0.5, color=GREEN, linewidth=2, linestyle='--', alpha=0.8)
ax.text(0.5, 3.7, 's = 0.5\n分界线', ha='center', fontsize=9, color=GREEN, fontweight='bold')

for bar, score in zip(bars, scores):
    ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
            f's = {score:.2f}', va='center', fontsize=10, color=WHITE, fontweight='bold')

ax.set_xlabel('异常分数 s(x)', fontsize=10, labelpad=8)
ax.spines['bottom'].set_color('#1A3A5C'); ax.spines['left'].set_color('#1A3A5C')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.tick_params(axis='y', labelsize=9, colors=LGRAY)
ax.tick_params(axis='x', labelsize=9)
plt.tight_layout(pad=0.5)
fig.savefig(f'{OUT}/score_comparison.png', dpi=200, bbox_inches='tight', facecolor=BG)
plt.close()
print('✅ score_comparison.png')

# ══════════════════════════════════════
# Chart 5: 雷达图
# ══════════════════════════════════════
fig, ax = plt.subplots(1, 1, figsize=(4.5, 4.5), dpi=200, subplot_kw=dict(polar=True))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

categories = ['速度', '可扩展性', '高维适应', '无需调参', '无需标签', '并行化']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)] + [0]

iforest = [5, 5, 4, 5, 5, 5, 5]
lof =     [2, 1, 2, 3, 5, 1, 2]
ocsvm =   [1, 1, 4, 2, 4, 1, 1]

ax.plot(angles, iforest, 'o-', linewidth=2, color=GREEN, label='Isolation Forest', markersize=5)
ax.fill(angles, iforest, alpha=0.15, color=GREEN)
ax.plot(angles, lof, 's-', linewidth=1.5, color=ORANGE, label='LOF', markersize=4, alpha=0.7)
ax.fill(angles, lof, alpha=0.05, color=ORANGE)
ax.plot(angles, ocsvm, '^-', linewidth=1.5, color=CYAN, label='One-Class SVM', markersize=4, alpha=0.7)
ax.fill(angles, ocsvm, alpha=0.05, color=CYAN)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=9, color=LGRAY)
ax.set_ylim(0, 5.5)
ax.spines['polar'].set_color('#1A3A5C')
ax.grid(color='#1A3A5C', alpha=0.3)
ax.legend(loc='lower right', bbox_to_anchor=(1.3, -0.05), fontsize=9, framealpha=0.3,
          facecolor=BG, edgecolor='#1A3A5C', labelcolor=LGRAY)
plt.tight_layout(pad=1)
fig.savefig(f'{OUT}/method_radar.png', dpi=200, bbox_inches='tight', facecolor=BG)
plt.close()
print('✅ method_radar.png')

# ══════════════════════════════════════
# Chart 6: 子采样对比
# ══════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(7, 3.5), dpi=200)
fig.patch.set_facecolor(BG)
for idx, (ax, n_s, title) in enumerate(zip(axes, [1000, 256], ['Original: 1000 devices', 'Subsample: 256'])):
    ax.set_facecolor('#0A1525')
    if n_s == 1000:
        ax.scatter(normal_temps, normal_vibs, s=8, c=CYAN, alpha=0.3, edgecolors='none')
        ax.scatter(anomaly_temps, anomaly_vibs, s=40, c=ORANGE, alpha=0.8, edgecolors=WHITE, linewidth=0.5)
    else:
        idx_n = np.random.choice(len(normal_temps), 251, replace=False)
        idx_a = np.random.choice(len(anomaly_temps), min(5, len(anomaly_temps)), replace=False)
        ax.scatter(np.array(normal_temps)[idx_n], np.array(normal_vibs)[idx_n], s=10, c=CYAN, alpha=0.4, edgecolors='none')
        ax.scatter(np.array(anomaly_temps)[idx_a], np.array(anomaly_vibs)[idx_a], s=60, c=ORANGE, alpha=0.9, edgecolors=WHITE, linewidth=0.5)
    ax.set_title(title, fontsize=11, color=WHITE, fontweight='bold', pad=8)
    ax.set_xlim(25, 105); ax.set_ylim(-0.5, 16)
    ax.set_xlabel('Temperature (°C)', fontsize=9, labelpad=5)
    if idx == 0: ax.set_ylabel('Vibration (Hz)', fontsize=9, labelpad=5)
    ax.spines['bottom'].set_color('#1A3A5C'); ax.spines['left'].set_color('#1A3A5C')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.1, color='#1A3A5C', linestyle='--')
plt.tight_layout(pad=1)
fig.savefig(f'{OUT}/subsampling_effect.png', dpi=200, bbox_inches='tight', facecolor=BG)
plt.close()
print('✅ subsampling_effect.png')

# ══════════════════════════════════════
# Chart 7: 路径分布
# ══════════════════════════════════════
fig, ax = plt.subplots(1, 1, figsize=(5.5, 3.5), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor('#0E1F35')
np.random.seed(123)
a1_paths = np.random.exponential(0.8, 1000) + 0.5   # A1: path最短 ~1.3
a2_paths = np.random.exponential(1.5, 1000) + 1.5   # A2: ~3.0
p_paths  = np.random.normal(12.0, 2.5, 1000)        # P: ~12.0
ax.hist(a1_paths, bins=30, alpha=0.6, color=RED, label='A1 overheat (E[h]~1.3)', edgecolor='none')
ax.hist(a2_paths, bins=30, alpha=0.5, color=ORANGE, label='A2 loose (E[h]~3.0)', edgecolor='none')
ax.hist(p_paths, bins=30, alpha=0.4, color=CYAN, label='P normal (E[h]~12.0)', edgecolor='none')
ax.axvline(x=1.3, color=RED, linestyle='--', linewidth=1.5, alpha=0.8)
ax.axvline(x=3.0, color=ORANGE, linestyle='--', linewidth=1.5, alpha=0.8)
ax.axvline(x=12.0, color=CYAN, linestyle='--', linewidth=1.5, alpha=0.8)
ax.set_xlabel('Path length h(x)', fontsize=10, labelpad=8)
ax.set_ylabel('Count', fontsize=10, labelpad=8)
ax.legend(fontsize=9, framealpha=0.3, facecolor=BG, edgecolor='#1A3A5C', labelcolor=LGRAY)
ax.spines['bottom'].set_color('#1A3A5C'); ax.spines['left'].set_color('#1A3A5C')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.grid(True, alpha=0.1, color='#1A3A5C', linestyle='--')
plt.tight_layout(pad=0.5)
fig.savefig(f'{OUT}/path_distribution.png', dpi=200, bbox_inches='tight', facecolor=BG)
plt.close()
print('✅ path_distribution.png')

# ══════════════════════════════════════
# Chart 8: 分数刻度尺
# ══════════════════════════════════════
fig, ax = plt.subplots(1, 1, figsize=(8, 1.8), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG); ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.5, 1.5); ax.axis('off')

from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list('anomaly', [CYAN, '#2A6040', GREEN, '#6A6020', ORANGE, RED])
gradient = np.linspace(0, 1, 256).reshape(1, -1)
ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 0.5], alpha=0.9)

markers = [
    (0.0, '0', LGRAY), (0.5, '0.5\nthreshold', GREEN), (1.0, '1.0', RED),
    (0.44, 'P(0.44)', CYAN), (0.58, 'A3(0.58)', YELLOW),
    (0.74, 'A2(0.74)', ORANGE), (0.82, 'A1(0.82)', RED),
]
for x, label, color in markers:
    y = -0.2 if '(' in label and '0.5' not in label else 0.65
    ax.text(x, y, label, ha='center', va='center',
            fontsize=10 if '(' not in label else 9, color=color, fontweight='bold')
ax.text(0.15, 1.1, '<-- Normal', fontsize=11, color=CYAN, fontweight='bold')
ax.text(0.82, 1.1, 'Anomaly -->', fontsize=11, color=RED, fontweight='bold')
plt.tight_layout(pad=0.2)
fig.savefig(f'{OUT}/score_scale.png', dpi=200, bbox_inches='tight', facecolor=BG)
plt.close()
print('✅ score_scale.png')

print('\nAll charts regenerated with corrected logic!')
