from graph import app
from state import MemeSample, AgentState
import json
import os
from config import DATASET_NAME,TASK_FHM_J_H,TASK_HARM_J_H,JUDGE_SCORE,DATASET_NUM,error_focus_threshold
import random
import pandas as pd
seed =  32  #46 95%  54 90%
random.seed(seed)
local_path = 'C:/Users/77366/Desktop/模因检测/few-shot模因检测/基于多智能体对抗辩论的零样本有害模因检测/code/DTD/'
if DATASET_NAME=="FHM":
    data_src = 'data/FHM/data/dev_with_description_copy.jsonl'
    img_src = 'data/FHM/data'
    paper_path = 'data/FHM/paper.pdf'
    initial_prompt = TASK_FHM_J_H
elif DATASET_NAME=="MAMI":
    data_src = 'data/MAMI/data/test_with_description.tsv'
    img_src = 'data/MAMI/data/test_images'
    paper_path = 'data/MAMI/paper.pdf'
elif DATASET_NAME=="HARM":
    data_src = 'data/HARM/test_with_description_copy.jsonl'
    img_src = 'data/HARM/images'
    paper_path = 'data/HARM/paper.pdf'
    initial_prompt = TASK_HARM_J_H
else:
    raise ValueError("Unsupported DATASET_NAME. Choose either 'FHM' or 'MAMI'.")
data_src = local_path + data_src
paper_path = local_path + paper_path
img_src = local_path+ img_src
if DATASET_NAME == 'FHM':
    with open(data_src, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    sampled_lines = random.sample(lines, min(DATASET_NUM, len(lines)))
    dataset = []
    for s in sampled_lines:
        sample = json.loads(s)
        dataset.append({
        'id':sample[id],
        "meme_src": f"{img_src}/{sample['img']}",       # 本地图像路径
        "meme_text": sample['text'],
        "meme_content": sample.get('description', ""),
        "ground_truth": "harmful" if sample['label']==1 else 'harmless',
        "paper_pdf_path": paper_path
        })
if DATASET_NAME=="HARM":
    with open(data_src, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    sampled_lines = random.sample(lines, min(DATASET_NUM, len(lines)))
    dataset = []
    for s in sampled_lines:
        sample = json.loads(s)
        dataset.append({
        'id':sample["id"],
        "meme_src": f"{img_src}/{sample['image']}",       # 本地图像路径
        "meme_text": sample['text'],
        "meme_content": sample.get('description', ""),
        "ground_truth": "harmless" if 'not harmful' in sample['labels'] else 'harmful',
        "paper_pdf_path": paper_path
        })
if DATASET_NAME == 'MAMI':
    data = pd.read_csv(data_src, sep='\t')
    sampled_data = data.sample(n=min(DATASET_NUM, len(data)), random_state=seed) 
    dataset = []  
    for _, row in sampled_data.iterrows():
        dataset.append({
            'id': row['file_name'].split('.')[0],  # 假设 TSV 中有 'id' 列，按实际字段调整
            "meme_src": f"{img_src}/{row['file_name']}",
            "meme_text": row['text'],
            "meme_content": row.get('description', ""),
            "ground_truth": "harmless" if row['label']==0 else 'harmful',
            "paper_pdf_path": paper_path
        })
# 示例数据集（10条）
print('数据加载完成')
initial_state: AgentState = {
    # ====== 基础状态 ======
    "iteration": 0,
    "phase": "global_eval",  # 重要！必须有phase
    # 当前使用的prompt/code
    "current_prompt": initial_prompt,
    "current_code": JUDGE_SCORE,
    # 历史记录
    "prompt_history": [],  # 应该是List[dict]，初始为空
    # 数据集
    "dataset": dataset,
    "paper_text": "",  # 初始化时为空，extract_pdf_agent会填充
    "paper_pdf_path": paper_path,
    # ====== 全局评估相关 ======
    "predictions": {},
    "global_predictions": {},
    "global_errors": [],
    "global_accuracy": 0.0,
    "best_global_accuracy": 0.0,
    "best_global_prompt": "",
    "best_global_code": "",
    "converged": False,
    # ====== 错误聚焦相关 ======
    "fixed_error_dataset": [],
    "error_predictions": {},
    "error_errors": [],
    "error_iteration": 0, 
    "error_accuracy": 0.0,
    "best_error_accuracy": 0.0,
    "best_error_prompt": "",
    "best_error_code": "",
    
    # ====== 误判统计 ======
    "pre1l0": [],
    "pre0l1": [],
}

final_state = app.invoke(initial_state)

os.makedirs(f"output/{DATASET_NAME}", exist_ok=True)
with open(f"output/{DATASET_NAME}/prompt_evolution.json", "w", encoding="utf-8") as f:
    json.dump({
        "total_iterations": final_state["iteration"],
        "converged": final_state["converged"],
        "final_prompt": final_state["best_global_prompt"],
        "prompt_history": final_state["prompt_history"]
    }, f, indent=2, ensure_ascii=False)

print(f"✅ 迭代完成！共 {final_state['iteration']} 轮，收敛: {final_state['converged']}")
print(f"📄 结果已保存至: output/prompt_evolution.json")