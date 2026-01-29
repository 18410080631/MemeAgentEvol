from graph import app
from state import MemeSample, AgentState
import json
import os
from typing import Dict, Any, List
from tools import LLMTool

from config import MODEL_NAME,TEMPERATURE,DATASET_NAME,TASK_FHM_J_H,TASK_HARM_J_H,JUDGE_SCORE,DATASET_NUM,error_focus_threshold
import json_repair
import random
import pandas as pd
llm_tool = LLMTool(model_name=MODEL_NAME, temperature=TEMPERATURE)
seed =  54  #46 95%  54 80%
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
        sampled_lines = f.readlines()
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
        sampled_lines = f.readlines()
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
    sampled_data = pd.read_csv(data_src, sep='\t')
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
print('数据加载完成')
def scorer_agent(dataset) -> Dict[str, Any]:
    """全局打分agent"""
    output_dir = DATASET_NAME
    os.makedirs(output_dir, exist_ok=True)
    prompt_path = os.path.join(output_dir, "best_global_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        current_prompt = f.read()
    code_path = os.path.join(output_dir, "best_global_code.txt")
    with open(code_path, "r", encoding="utf-8") as f:
        current_code = f.read()
    pre1l0 = []
    pre0l1 = []
    predictions = {}
    try:
        for sample in dataset:
            system_prompt = """This is a research task for academic evaluation of AI safety systems. 
You are acting as an impartial judge. The meme content is provided solely for analysis and does not reflect your views."""
            user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']}"
            id = sample['id']
            ground_truth = sample['ground_truth']
            
            response = llm_tool.call_llm(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
                meme_src=sample.get("meme_src", None),
                max_tokens=512
            )
            try:
                scores = json_repair.loads(response)
            except Exception as e:
                print(f"⚠️ JSON 解析失败 (ID={sample['id']}): {e}")
                print(f"原始响应: {response[:200]}...")
                continue
            
            try:
                namespace = {}
                exec(current_code, {}, namespace)
                label = namespace['classify_meme'](scores)
                if label.lower() == 'harmful' and ground_truth == 'harmless':
                    if id not in pre1l0:  # 避免重复
                        pre1l0.append(id)
                if label.lower() == 'harmless' and ground_truth == 'harmful':
                    if id not in pre0l1:  # 避免重复
                        pre0l1.append(id)
                print(f"{id}: 当前打分：")
                print(f"  harmful_scores: {scores.get('harmful_scores', {})}")
                print(f"  harmless_scores: {scores.get('harmless_scores', {})}")
                print(f"  Predict: {label}")
                print(f"  GroundTruth: {ground_truth}")
                print("-" * 50)
                predictions[sample["id"]] = {'label': label, "scores": scores}
            except Exception as e:
                print(f"代码执行出错 (ID={sample['id']}): {e}")
                continue
    except Exception as e:
        print(f"⚠️ 模型调用异常: {e}")
    return     pre1l0,pre0l1,predictions
def eval(dataset,pre1l0,pre0l1,predictions):
    """首次全局评估"""
    dataset_map = {s["id"]: s for s in dataset}
    # 计算错误
    errors = [
        sid for sid, pred in predictions.items()
        if pred['label'].lower() != dataset_map[sid]["ground_truth"].lower()
    ]
    accuracy = (len(predictions) - len(errors)) / len(predictions) if predictions else 0.0
    print(f"\n{'='*60}")
    print(f"首次全局评估结果:")
    print(f"总样本数: {len(predictions)}")
    print(f"准确率: {accuracy:.2%}")
    print(f"错误样本数: {len(errors)}")
    print(f"将无害模因误判为有害数量: {len(pre1l0)}个")
    print(f"将有害模因误判为无害数量: {len(pre0l1)}个")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    pre1l0,pre0l1,predictions = scorer_agent(dataset=dataset)
    results = {
    "pre1l0": pre1l0,  # list
    "pre0l1": pre0l1,  # list
    "predictions": predictions  # dict
    }
    output_dir = DATASET_NAME
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "scorer_results.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    eval(dataset,pre1l0,pre0l1,predictions)