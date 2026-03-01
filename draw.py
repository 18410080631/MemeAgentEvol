import matplotlib.pyplot as plt
import os
import numpy as np
import json
import os
def draw_evolution():
    # --- 数据准备 ---
    datasets = {
        'HARM': {
            'rounds': ['R1', 'R2', 'R3', 'R4'],
            'acc': [0.70, 0.775, 0.75, 0.90],
            'f1': [0.57, 0.73, 0.64, 0.87],
            'dims': [6, 10, 13, 13]
        },
        'FHM': {
            'rounds': ['R1', 'R2', 'R3', 'R4', 'R5'],
            'acc': [0.825, 0.825, 0.825, 0.825, 0.85],
            'f1': [0.79, 0.77, 0.77, 0.77, 0.81],
            'dims': [7, 8, 9, 10, 10]
        },
        'MAMI': {
            'rounds': ['R1', 'R2', 'R3', 'R4', 'R5', 'R6'],
            'acc': [0.85, 0.85, 0.85, 0.82, 0.85, 0.90],
            'f1': [0.86, 0.86, 0.86, 0.84, 0.86, 0.91],
            'dims': [6, 8, 9, 10, 11, 12]
        }
    }

    # --- 设置学术风格 ---
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']

    # 调整画布比例：宽度15英寸，高度5英寸。这个比例最适合Word
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    colors = {'acc': '#1F4E79', 'f1': '#C00000', 'dim': '#E1E1E1'}

    for i, (name, data) in enumerate(datasets.items()):
        ax1 = axes[i]
        x = data['rounds']

        # 绘制维度背景（右轴）
        ax2 = ax1.twinx()
        bars = ax2.bar(x, data['dims'], color=colors['dim'], alpha=0.6, width=0.4, label='Dimensions', zorder=1)
        ax2.set_ylim(0, 16)
        ax2.tick_params(axis='y', labelsize=9, labelcolor='#777777')
        if i == 2:
            ax2.set_ylabel('Number of Dimensions', fontsize=10)

        # 绘制性能指标（左轴）
        line1, = ax1.plot(x, data['acc'], marker='s', ms=5, lw=1.5, color=colors['acc'], label='Accuracy', zorder=3)
        line2, = ax1.plot(x, data['f1'], marker='o', ms=5, lw=1.5, ls='--', color=colors['f1'], label='Macro-F1', zorder=3)

        ax1.set_title(name, fontsize=12, fontweight='bold', pad=12)
        ax1.set_xlabel('Rounds', fontsize=10)
        ax1.set_ylim(0.5, 1.0)
        ax1.tick_params(axis='both', labelsize=9)
        if i == 0:
            ax1.set_ylabel('Performance Metrics', fontsize=10)
        ax1.grid(True, ls=':', alpha=0.4, zorder=0)

    # --- 核心改进：解决重叠和间距问题 ---
    # 1. 调整子图间的水平间距 wspace，预留足够空间给y轴标签
    plt.subplots_adjust(wspace=0.35, top=0.85, bottom=0.15, left=0.08, right=0.92)

    # 2. 统一图例
    lines = [line1, line2, bars]
    labels = [l.get_label() for l in lines]
    fig.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, 0.98), 
               ncol=3, frameon=False, fontsize=10)

    # 3. 保存设置：使用 bbox_inches='tight' 自动裁剪空白，但保持内容比例
    plt.savefig('evolution_optimized.png', dpi=300, bbox_inches='tight')
import numpy as np
import matplotlib.pyplot as plt
import json
import os

def plot_triple_radar(datasets_config):
    """
    datasets_config: 列表，每个元素是一个字典，包含：
    {
        "name": "FHM",
        "harmful_dims": ["H1", "H2", "H3"],
        "harmless_dims": ["N1", "N2", "N3", "N4", "N5", "N6", "N7"]
    }
    """
    # 1. 初始化大画布 (1行3列)
    fig = plt.figure(figsize=(20, 7), dpi=300)
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']
    
    for idx, config in enumerate(datasets_config):
        dataset_name = config["name"]
        harmful_dims = config["harmful_dims"]
        harmless_dims = config["harmless_dims"]
        
        # 2. 读取数据 (根据你的目录结构)
        data_src = os.path.join(dataset_name + "_final", "predictions.json")
        if not os.path.exists(data_src):
            print(f"Warning: {data_src} not found, skipping...")
            continue
            
        with open(data_src, "r", encoding="utf-8") as f:
            predictions = json.load(f)
        
        labels = harmful_dims + harmless_dims
        total_dims = len(labels)
        
        # 3. 按类别统计均值
        # 假设 predictions 格式: [label, score1, score2, ..., scoreN, reasoning]
        harmful_data = [d for d in predictions if int(d[0]) == 1]
        harmless_data = [d for d in predictions if int(d[0]) == 0]
        
        h_scores = np.mean([d[1:1+total_dims] for d in harmful_data], axis=0)
        n_scores = np.mean([d[1:1+total_dims] for d in harmless_data], axis=0)
        
        # 4. 雷达图闭合逻辑
        angles = np.linspace(0, 2 * np.pi, total_dims, endpoint=False).tolist()
        h_scores_plot = np.concatenate((h_scores, [h_scores[0]]))
        n_scores_plot = np.concatenate((n_scores, [n_scores[0]]))
        angles_plot = angles + [angles[0]]
        
        # 5. 创建子图 (1, 3, idx+1)
        ax = fig.add_subplot(1, 3, idx+1, polar=True)
        
        # 绘制有害 (红色)
        ax.plot(angles_plot, h_scores_plot, color='#C00000', linewidth=2, label='Harmful (Avg.)')
        ax.fill(angles_plot, h_scores_plot, color='#C00000', alpha=0.2)
        
        # 绘制无害 (蓝色)
        ax.plot(angles_plot, n_scores_plot, color='#1F4E79', linewidth=2, label='Harmless (Avg.)')
        ax.fill(angles_plot, n_scores_plot, color='#1F4E79', alpha=0.2)
        
        # 6. 坐标轴美化
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        # 这里的 labels 要简短，否则会重叠
        ax.set_thetagrids(np.degrees(angles), labels, fontsize=9, fontweight='bold')
        ax.set_ylim(0, 9) # 1-9分制
        ax.set_title(f"({chr(97+idx)}) {dataset_name}", size=16, pad=30, fontweight='bold')

    # 7. 全局图例与保存
    handles, labels_legend = ax.get_legend_handles_labels()
    fig.legend(handles, labels_legend, loc='upper center', bbox_to_anchor=(0.5, 0.05), 
               ncol=2, fontsize=12, frameon=False)
    
    plt.tight_layout()
    plt.savefig('Triple_Radar_Analysis.png', bbox_inches='tight')
    plt.show()

# --- 配置三个数据集的维度信息 ---
config_list = [
    {
        "name": "FHM",
        "harmful_dims": ["H1", "H2", "H3"],
        "harmless_dims": ["N1", "N2", "N3", "N4", "N5", "N6", "N7"]
    },
    {
        "name": "MAMI",
        "harmful_dims": ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"],
        "harmless_dims": ["N1", "N2", "N3", "N4"]
    },
    {
        "name": "HARM",
        "harmful_dims": ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"],
        "harmless_dims": ["N1", "N2", "N3", "N4", "N5"]
    }
]
plot_triple_radar(config_list)