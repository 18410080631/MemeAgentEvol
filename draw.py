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

import matplotlib.pyplot as plt

def draw_individual_evolution():
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

    # --- 学术风格设置 ---
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']
    plt.rcParams['mathtext.fontset'] = 'stix'  # 使数学符号更接近Times风格
    
    # 颜色与样式配置 (保持专业感)
    color_acc = '#1F4E79' # 黑色实线
    color_f1 = '#C00000'  # 深灰色虚线
    color_dim = '#E1E1E1' # 浅灰色柱状图
    
    # 循环生成每一张图
    for name, data in datasets.items():
        # 设置单张图大小，通常4-5英寸宽比较适合Word单栏或半栏嵌入
        fig, ax1 = plt.subplots(figsize=(5, 4))
        
        x = data['rounds']
        
       

        # 1. 绘制性能指标 (左轴)
        # 使用不同标记和线型以增加区分度 (自明性)
        line1, = ax1.plot(x, data['acc'], marker='s', mfc='none', mec=color_acc, 
                         lw=1.2, color=color_acc, label='Accuracy', zorder=3)
        line2, = ax1.plot(x, data['f1'], marker='^', mfc='none', mec=color_f1, 
                         lw=1.2, ls='--', color=color_f1, label='Macro-F1', zorder=3)
        # 2. 绘制维度柱状图 (右轴) - 对应“简写函数图”中的辅助信息
        ax2 = ax1.twinx()
        bars = ax2.bar(x, data['dims'], color=color_dim, alpha=0.7, width=0.5, label='Dimensions', zorder=1)
        ax2.set_ylim(0, 16)
        # 标注格式：物理量(斜体)/单位(正体)
        ax2.set_ylabel(r'$D$/unit', fontsize=10.5) 
        ax2.tick_params(axis='y', labelsize=10.5)
        # 3. 坐标轴及标签设置 (五号字对应10.5pt)
        ax1.set_xlabel('Rounds', fontsize=10.5)
        # 使用LaTeX渲染斜体物理量符号
        ax1.set_ylabel(r'$Value$', fontsize=10.5) 
        ax1.set_ylim(0.5, 1.0)
        ax1.tick_params(axis='both', labelsize=10.5)
        
        # 4. 辅助线
        ax1.grid(True, ls=':', alpha=0.5, zorder=0)

        # 5. 图例 - 放在图内上方，确保自明性
        lines = [line1, line2, bars]
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=9, frameon=True, edgecolor='black', fancybox=False)
        ax1.set_zorder(ax2.get_zorder() + 1) # 让ax1比ax2高一层
        ax1.patch.set_visible(False)
        # 6. 布局调整与保存
        plt.tight_layout()
        filename = f'evolution_{name}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"已保存: {filename}")
        plt.close()

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
import matplotlib.pyplot as plt
import numpy as np
import os
import json

def draw_individual_radar():
    """
    模仿示例图：将图例放入图表内部，使用方正边框和白色背景
    """
    datasets_config = [
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
    # --- 全局学术风格设置 ---
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']
    plt.rcParams['mathtext.fontset'] = 'stix'
    
    color_harmful = '#C00000' 
    color_harmless = '#1F4E79'

    for config in datasets_config:
        dataset_name = config["name"]
        harmful_dims = config["harmful_dims"]
        harmless_dims = config["harmless_dims"]
        
        # 1. 数据加载与处理
        data_src = os.path.join(dataset_name + "_final", "predictions.json")
        if not os.path.exists(data_src):
            continue
            
        with open(data_src, "r", encoding="utf-8") as f:
            predictions = json.load(f)
        
        labels = harmful_dims + harmless_dims
        total_dims = len(labels)
        
        harmful_data = [d for d in predictions if int(d[0]) == 1]
        harmless_data = [d for d in predictions if int(d[0]) == 0]
        
        h_scores = np.mean([d[1:1+total_dims] for d in harmful_data], axis=0)
        n_scores = np.mean([d[1:1+total_dims] for d in harmless_data], axis=0)
        
        angles = np.linspace(0, 2 * np.pi, total_dims, endpoint=False).tolist()
        h_scores_plot = np.concatenate((h_scores, [h_scores[0]]))
        n_scores_plot = np.concatenate((n_scores, [n_scores[0]]))
        angles_plot = angles + [angles[0]]

        # 2. 绘图
        fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True), dpi=300)
        
        # Harmful: 实线 + 方块 (模仿示例图 marker)
        ax.plot(angles_plot, h_scores_plot, color=color_harmful, 
                marker='s', markersize=4, lw=1.2, label='Harmful (Avg.)', zorder=3)
        ax.fill(angles_plot, h_scores_plot, color=color_harmful, alpha=0.1)
        
        # Harmless: 实线 + 菱形 (模仿示例图 marker)
        ax.plot(angles_plot, n_scores_plot, color=color_harmless, 
                marker='d', markersize=5, lw=1.2, label='Harmless (Avg.)', zorder=2)
        ax.fill(angles_plot, n_scores_plot, color=color_harmless, alpha=0.1)
        
        # 3. 极坐标格式化
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles), labels, fontsize=10, fontweight='bold')
        ax.set_ylim(0, 9)
        plt.yticks([3, 6, 9], ["3", "6", "9"], color="grey", size=8)
        ax.grid(True, ls=':', alpha=0.5)

        # 4. 【关键修改】仿照示例图的图例放法
        # loc='center left' 会把图例放在绘图区左侧，framealpha=1 确保背景不透明覆盖网格线
        ax.legend(loc='lower right', 
                          bbox_to_anchor=(1.25, 0.05), 
                          fontsize=9, 
                          frameon=True, 
                          edgecolor='black', 
                          facecolor='white', 
                          framealpha=1, 
                          fancybox=False)

        # 5. 标题与保存
        # ax.set_title(dataset_name, size=14, pad=20, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'radar_inset_{dataset_name}.png', bbox_inches='tight')
        plt.close()

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 1. 整理数据 (根据你提供的数据提取 Top 核心维度进行展示)
# 这里选取一些关键维度作为示例，你可以根据需要扩展全量维度
def draw_dim_importance():
    data = {
        'Dimension': ['H1', 'H2', 'H3', 'H6', 'H7', 'H8', 'N1', 'N2', 'N3'],
        'HARM': [0.475, 0.232, 0.077, 0.598, 0.698, 0.812, 0.289, 0.948, 0.895],
        'FHM': [0.180, 0.498, 0.813, 0.305, 0.381, 0, 0.374, 0.711, 0.059], # 不存在的维度填0
        'MAMI': [0.068, 0.383, 0.827, 0.753, 0.631, 0.111, 0.705, 0.203, 0.320]
    }

    df = pd.DataFrame(data)
    df_melted = df.melt(id_vars='Dimension', var_name='Dataset', value_name='Importance')

    # 2. 绘图配置
    plt.figure(figsize=(14, 7), dpi=300)
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']

    # 使用 Seaborn 风格的分组条形图
    import seaborn as sns
    sns.set_theme(style="whitegrid")
    ax = sns.barplot(x='Dimension', y='Importance', hue='Dataset', data=df_melted, palette=["#EF8383", "#71AEE7", "#AEDB91"])

    # 3. 美化图表
    #plt.title('Comparison of Feature Importance Across Datasets (HARM vs. FHM vs. MAMI)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Evaluation Dimensions', fontsize=12, fontweight='bold')
    plt.ylabel('Absolute Feature Weight (Importance)', fontsize=12, fontweight='bold')
    plt.ylim(0, 1.1)
    plt.legend(title='Dataset', title_fontsize='12', fontsize='11', loc='upper right')

    # 在柱状图上方标注具体数值 (可选)
    for p in ax.patches:
        if p.get_height() > 0:
            ax.annotate(format(p.get_height(), '.2f'), 
                        (p.get_x() + p.get_width() / 2., p.get_height()), 
                        ha = 'center', va = 'center', 
                        xytext = (0, 9), 
                        textcoords = 'offset points',
                        fontsize=8, rotation=45)

    plt.tight_layout()
    plt.savefig('Feature_Importance_Comparison.png')
    # plt.show()
draw_dim_importance()
# --- 配置三个数据集的维度信息 ---
# draw_individual_radar()
# draw_individual_evolution()