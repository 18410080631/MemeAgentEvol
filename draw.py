import matplotlib.pyplot as plt
import os
import numpy as np
import json
import os
from config import DATASET_NAME
import matplotlib.pyplot as plt

import json
import matplotlib.pyplot as plt
import os

import json
import matplotlib.pyplot as plt
import os

def draw_individual_evolution():
    # --- 1. 数据配置 ---
    # 定义实验变体标签及其对应的文件夹后缀
    variants = {
        'Full Model': 'full',
        'w/o MEE': 'wo_MEE',
        'w/o RRM': 'wo_RRM'
    }
    dataset_names = ['HARM', 'FHM', 'MAMI']
    
    # 学术配色方案（高对比度）
    styles = {
        'Full Model': {'color': '#1F4E79', 'marker': 'o', 'ls': '-'},   # 深蓝 实线
        'w/o MEE':    {'color': '#C00000', 'marker': 's', 'ls': '--'},  # 深红 虚线
        'w/o RRM':    {'color': '#008000', 'marker': '^', 'ls': '-.'}  # 绿色 点划线
    }

    # --- 2. 字体与学术风格设置 ---
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']
    plt.rcParams['mathtext.fontset'] = 'stix'
    
    # --- 3. 循环为每个数据集绘图 ---
    for ds_name in dataset_names:
        # 设置适合论文发表的尺寸
        fig, ax = plt.subplots(figsize=(5.5, 4.2))
        
        # 遍历读取并绘制每个变体的 Accuracy
        for label, suffix in variants.items():
            # 路径拼接，例如: HARM_full/result.json
            file_path = f"{ds_name}_{suffix}/result.json"
            
            if not os.path.exists(file_path):
                print(f"跳过: 未找到路径 {file_path}")
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取数据
            x = data['rounds']
            y = data['acc']
            
            # 绘制 Accuracy 演化曲线
            ax.plot(x, y, 
                    label=label,
                    color=styles[label]['color'],
                    marker=styles[label]['marker'],
                    ls=styles[label]['ls'],
                    lw=1.6, 
                    mfc='white', # 标志内部填充白色，提升学术质感
                    ms=6,
                    zorder=3)

        # --- 4. 坐标轴及细节微调 ---
        ax.set_xlabel('Evolutionary Rounds', fontsize=11)
        ax.set_ylabel('Accuracy', fontsize=11)
        
        # 开启网格，使用极淡的虚线
        ax.grid(True, ls=':', alpha=0.5, zorder=0)
        
        # 根据实际数据微调 y 轴范围，例如 0.6 到 0.9
        # ax.set_ylim(0.6, 0.9) 
        
        ax.tick_params(axis='both', labelsize=10)
        
        # 图例设置：无阴影、黑边、右下角
        ax.legend(loc='lower right', fontsize=10, frameon=True, 
                  edgecolor='black', fancybox=False)

        # --- 5. 布局优化与保存 ---
        plt.tight_layout()
        save_dir = "evolution_pics"
        os.makedirs(save_dir, exist_ok=True)
        
        # 文件名示例: accuracy_evolution_HARM.png
        save_path = os.path.join(save_dir, f'accuracy_evolution_{ds_name}.png')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"已成功保存对比图: {save_path}")
        plt.close()

# 执行调用

# 执行
# draw_individual_evolution()

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
import os

import matplotlib.pyplot as plt
import os
import numpy as np

def draw_insight_size_impact():
    # --- 1. 数据配置 ---
    # 包含了 0 (Baseline) 以及 10, 20, 40, 60
    x_sizes = [0, 10, 20, 40, 60]
    
    # 你的真实/模拟数据
    data = {
        'FHM':  [0.648, 0.664, 0.660, 0.696, 0.682],
        'HARM': [0.692, 0.711, 0.720, 0.741, 0.750], 
        'MAMI': [0.724, 0.728, 0.755, 0.795, 0.797]
    }

    # 学术配色与线型
    styles = {
        'FHM':  {'color': '#1F4E79', 'marker': 'o', 'ls': '-'},   
        'HARM': {'color': '#C00000', 'marker': 's', 'ls': '--'},  
        'MAMI': {'color': '#008000', 'marker': '^', 'ls': '-.'}   
    }

    # --- 2. 字体与风格设置 ---
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman']
    plt.rcParams['mathtext.fontset'] = 'stix'
    
    fig, ax = plt.subplots(figsize=(6, 4.5))
    
    # --- 3. 绘图 ---
    for ds_name, y_values in data.items():
        ax.plot(x_sizes, y_values, 
                label=ds_name,
                color=styles[ds_name]['color'],
                marker=styles[ds_name]['marker'],
                ls=styles[ds_name]['ls'],
                lw=1.8, 
                mfc='white', 
                ms=7,
                zorder=3)

    # --- 4. 坐标轴及范围微调 ---
    ax.set_xlabel('Size of Insight Set', fontsize=12)
    ax.set_ylabel('Accuracy', fontsize=12)
    
    ax.set_xticks(x_sizes)
    
    # --- 关键调整区 ---
    # 根据你的数据：最小值 0.648, 最大值 0.795
    # 设置 y 轴从 0.62 开始到 0.82 结束，给顶部留出一点图例空间
    ax.set_ylim(0.62, 0.82) 
    
    # 设置更精细的刻度，每 0.02 一个刻度
    ax.set_yticks(np.arange(0.62, 0.83, 0.02))
    # ------------------

    ax.grid(True, ls=':', alpha=0.5, zorder=0)
    ax.tick_params(axis='both', labelsize=11)
    
    ax.legend(loc='lower right', fontsize=11, frameon=True, 
              edgecolor='black', fancybox=False)

    # --- 5. 布局优化与保存 ---
    plt.tight_layout()
    save_dir = "evolution_pics"
    os.makedirs(save_dir, exist_ok=True)
    
    save_path = os.path.join(save_dir, 'insight_size_impact_comparison.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    print(f"图像已保存至: {save_path}")
    plt.show()

    # plt.show()

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
# draw_dim_importance()
# --- 配置三个数据集的维度信息 ---
# draw_individual_radar()
# draw_individual_evolution()
draw_insight_size_impact()