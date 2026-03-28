from graph import app
from state import MemeSample, AgentState
import json
import os
from config import DATASET_NAME,TASK_FHM_J_H,TASK_HARM_J_H,TASK_MAMI_J_H,JUDGE_SCORE,DATASET_NUM,error_focus_threshold
import random
import pandas as pd
from tools import DescriptionSaver,get_description_of_meme
seed =  46  #46 95%  54 90%
local_path = 'C:/Users/77366/Desktop/memedetection/few-shot/mywork/code/MDF/'
if DATASET_NAME=="FHM":
    data_src = 'data/FHM/data/train.jsonl'
    img_src = 'data/FHM/data'
    paper_path = 'data/FHM/paper.pdf'
    initial_prompt = TASK_FHM_J_H
elif DATASET_NAME=="MAMI":
    data_src = 'data/MAMI/data/train.tsv'
    img_src = 'data/MAMI/data/training_images'
    paper_path = 'data/MAMI/paper.pdf'
    initial_prompt = TASK_MAMI_J_H
elif DATASET_NAME=="HARM":
    data_src = 'data/HARM/train.jsonl'
    img_src = 'data/HARM/images'
    paper_path = 'data/HARM/paper.pdf'
    initial_prompt = TASK_HARM_J_H
else:
    raise ValueError("Unsupported DATASET_NAME. Choose either 'FHM' or 'MAMI'.")
data_src = local_path + data_src
paper_path = local_path + paper_path
img_src = local_path+ img_src
descriptionsaver = DescriptionSaver(DATASET_NAME)
if DATASET_NAME == 'FHM':
    random.seed(33)
    with open(data_src, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    sampled_lines = random.sample(lines, min(DATASET_NUM+10, len(lines)))
    dataset = []
    data_num = 0
    for s in sampled_lines:
        sample = json.loads(s)
        des = descriptionsaver.get(sample["id"])
        if des==None:
            des = get_description_of_meme(sample['text'],f"{img_src}/{sample['img']}")
            descriptionsaver.save(sample["id"],des)
        if len(des) > 50:
            data_num+=1
            dataset.append({
            'id':sample["id"],
            "meme_src": f"{img_src}/{sample['img']}",       # 本地图像路径
            "meme_text": sample['text'],
            "meme_content": "The description of the Meme Pictrue:"+des,
            "ground_truth": "harmful" if sample['label']==1 else 'harmless',
            "paper_pdf_path": paper_path
            })
        else:
            print(des)
        if data_num>=DATASET_NUM:
            break
if DATASET_NAME=="HARM":
    random.seed(43)
    with open(data_src, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    sampled_lines = random.sample(lines, min(DATASET_NUM+10, len(lines)))
    dataset = []
    data_num = 0
    for s in sampled_lines:
        sample = json.loads(s)
        des = descriptionsaver.get(sample["id"])
        if des==None:
            des = get_description_of_meme(sample['text'],f"{img_src}/{sample['image']}")
            descriptionsaver.save(sample["id"],des)
        if len(des)>50:
            data_num+=1
            dataset.append({
            'id':sample["id"],
            "meme_src": f"{img_src}/{sample['image']}",       # 本地图像路径
            "meme_text": sample['text'],
            "meme_content": des,
            "ground_truth": "harmless" if 'not harmful' in sample['labels'] else 'harmful',
            "paper_pdf_path": paper_path
            })
        else:
            print(des)
        if data_num>=DATASET_NUM:
            break
if DATASET_NAME == 'MAMI':
    random.seed(33)
    data = pd.read_csv(data_src, sep='\t')
    sampled_data = data.sample(n=min(DATASET_NUM+20, len(data)), random_state=33) 
    dataset = []  
    data_num = 0
    for _, row in sampled_data.iterrows():
        des = descriptionsaver.get(row['file_name'].split('.')[0])
        if des==None:
            des = get_description_of_meme(row['text'],f"{img_src}/{row['file_name']}")
            descriptionsaver.save(row['file_name'].split('.')[0],des)
        if len(des)>50:
            data_num+=1
            dataset.append({
                'id': row['file_name'].split('.')[0],  # 假设 TSV 中有 'id' 列，按实际字段调整
                "meme_src": f"{img_src}/{row['file_name']}",
                "meme_text": row['text'],
                "meme_content": des,
                "ground_truth": "harmless" if row['label']==0 else 'harmful',
                "paper_pdf_path": paper_path
            })
        else:
            print(des)
        if data_num>=DATASET_NUM:
            break
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
    "report":[],
    "res":{"acc":[],"f1":[],"dims":[]}
}

final_state = app.invoke(initial_state)

os.makedirs(f"{DATASET_NAME}", exist_ok=True)
with open(f"{DATASET_NAME}/result.json", "w", encoding="utf-8") as f:
    res = final_state["res"]
    res["rounds"] = []
    for i in range(len(res["acc"])):
        res["rounds"].append(f"R{i+1}")
    json.dump(res, f, indent=2, ensure_ascii=False)
print(f"✅ 迭代完成！共 {final_state['iteration']} 轮，收敛: {final_state['converged']}")
print(f"📄 结果已保存至:{DATASET_NAME}/result.json")