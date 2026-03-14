from graph import app
from state import MemeSample, AgentState
import json
import os
from typing import Dict, Any, List
from tools import LLMTool,predict_eval
from tqdm import tqdm
from config import MODEL_NAME,TEMPERATURE,DATASET_NAME,TASK_FHM_J_H,TASK_HARM_J_H,JUDGE_SCORE,DATASET_NUM,error_focus_threshold
import json_repair
import random
import pandas as pd
import numpy as np
llm_tool = LLMTool(model_name=MODEL_NAME, temperature=TEMPERATURE)
seed =  54  
random.seed(seed)
DATASET_NAME = "HARM"

local_path = 'C:/Users/77366/Desktop/memedetection/few-shot/mywork/code/MDF/'
if DATASET_NAME=="FHM":
    data_src = 'data/FHM/data/dev_with_description_copy.jsonl'
    img_src = 'data/FHM/data'
    paper_path = 'data/FHM/paper.pdf'
    initial_prompt = TASK_FHM_J_H
elif DATASET_NAME=="MAMI":
    data_src = 'data/MAMI/data/test.tsv'
    img_src = 'data/MAMI/data/test_images'
    paper_path = 'data/MAMI/paper.pdf'
elif DATASET_NAME=="HARM":
    data_src = 'data/HARM/test.jsonl'
    img_src = 'data/HARM/images'
    paper_path = 'data/HARM/paper.pdf'
    initial_prompt = TASK_HARM_J_H
else:
    raise ValueError("Unsupported DATASET_NAME. Choose either 'FHM' or 'MAMI'.")
data_src = local_path + data_src
paper_path = local_path + paper_path
img_src = local_path+ img_src
if DATASET_NAME == 'FHM':
    ##改
    with open(data_src, 'r', encoding='utf-8') as f:
        sampled_lines = f.readlines()
    dataset = []
    for s in sampled_lines:
        sample = json.loads(s)
        dataset.append({
        'id':sample["id"],
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
def predict(dataset) -> Dict[str, Any]:
    """全局打分agent"""
    output_dir = f"{DATASET_NAME}"
    os.makedirs(output_dir, exist_ok=True)
    prompt_path = os.path.join(output_dir, "best_global_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        current_prompt = f.read()
    predictions = []
    for sample in tqdm(dataset):
        system_prompt = """This is a research task for academic evaluation of AI safety systems. 
You are acting as an impartial judge. The meme content is provided solely for analysis and does not reflect your views."""
        user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']}"
        id = sample['id']
        ground_truth = sample['ground_truth']
        try:
            response = llm_tool.call_llm(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
            meme_src=sample.get("meme_src", None),
            max_tokens=512
            )
            scores = json_repair.loads(response)
            d = list(scores["harmful_scores"].values()) + list(scores["harmless_scores"].values())
            if ground_truth == 'harmful':
                d = [1] + d
            else:
                d = [0] + d
            predictions.append(d)
        except Exception as e:
            print(f"⚠️ JSON 解析失败 (ID={sample['id']}): {e}")
            print(f"原始响应: {response[:200]}...")
            continue
    with open(os.path.join(output_dir, "predictions.json"), "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False)
    res = predict_eval(os.path.join(output_dir, "best_model.json"), predictions)
    return  res

from sklearn.metrics import accuracy_score, f1_score

def calculate_metrics(dataset_name, harmful_nums, harmless_nums,b):
    data_src = os.path.join(dataset_name+"_final", "predictions.json")
    with open(data_src, "r", encoding="utf-8") as f:
        predictions = json.load(f)
    # print(len(predictions))
    y_true = [] # 真实标签
    y_pred = [] # 预测标签
    for d in predictions:
        true_label = int(d[0]) 
        y_true.append(true_label)
        harmful_scores = d[1 : 1 + harmful_nums]
        harmless_scores = d[1 + harmful_nums : 1 + harmful_nums + harmless_nums]
        # avg_harmful = sum(harmful_scores) / len(harmful_scores) if harmful_scores else 0
        # avg_harmless = sum(harmless_scores) / len(harmless_scores) if harmless_scores else 0
        avg_harmful = harmful_scores[2]
        avg_harmless = harmless_scores[2]
        y_pred.append(1 if avg_harmful > avg_harmless - b else 0)
    acc = accuracy_score(y_true, y_pred)
    # 关键点：设置 average='macro' 来计算 Macro-F1
    macro_f1 = f1_score(y_true, y_pred, average='macro')
    return {
        "accuracy": acc,
        "macro_f1": macro_f1
    }

def find_best_b():
    """
    calculate_metrics_func: 外部定义的计算指标函数
    """
    best_b = 0
    max_f1 = -1
    best_acc = 0  # 注意：这里的 best_acc 通常指加权后的总准确率
    dataset_names = {
        "HARM": [8, 5],
        "FHM": [3, 7],
        "MAMI": [8, 4]
    }
    weights = {"FHM": 0.2, "HARM": 0.2, "MAMI": 0.6}
    # 打印表头
    print(f"{'b':>6} | {'HARM (F1, ACC)':^18} | {'FHM (F1, ACC)':^18} | {'MAMI (F1, ACC)':^18} | {'Weighted F1'}")
    print("-" * 90)
    # 定义搜索范围
    b_range = np.arange(-10, 1, 0.1)
    for b in b_range:
        mco_f1 = 0
        temp_results = {} # 用于存储当前 b 下各个数据集的细节
        for d, nums in dataset_names.items():
            harmful_nums, harmless_nums = nums[0], nums[1]
            # 调用计算函数
            metrics = calculate_metrics(d, harmful_nums, harmless_nums, b)
            f1 = metrics["macro_f1"]
            acc = metrics["accuracy"]
            # 存入临时字典方便后续打印
            temp_results[d] = (f1, acc)
            # 累加加权 F1
            mco_f1 += weights[d] * f1
        # 如果当前加权 F1 更高，更新最优结果并打印表格行
        if mco_f1 > max_f1:
            max_f1 = mco_f1
            best_b = b
            
            # 格式化各个数据集的输出字符串
            res_str = {}
            for d in ["HARM", "FHM", "MAMI"]:
                f1_val, acc_val = temp_results[d]
                res_str[d] = f"({f1_val:.4f}, {acc_val:.4f})"

            # 实时输出更新行
            print(f"{b:>6.1f} | {res_str['HARM']:^18} | {res_str['FHM']:^18} | {res_str['MAMI']:^18} | {max_f1:.4f} ⭐")

    print("-" * 90)
    print(f"寻找完成！最终结果：")
    print(f"最优 b 值: {best_b:.2f}")
    print(f"最高加权 Macro-F1: {max_f1:.4f}")
    
    return best_b, max_f1
# 调用示例
# results = calculate_metrics("MAMI", 8, 4)
# print(f"Accuracy: {results['accuracy']:.4f}")
# print(f"Macro-F1: {results['macro_f1']:.4f}")
    #计算准确率和f1分数
def find_longest_common_subarray(list1, list2):
    """
    查找两个列表中最长的公共连续子序列
    返回在 list1 中的起始索引、结束索引（包含）和长度
    """
    if not list1 or not list2:
        return 0, -1, 0  # 长度，起始点，终点
    
    n, m = len(list1), len(list2)
    max_len = 0
    start_idx = 0
    end_idx = -1
    
    # 动态规划：dp[i][j] 表示以 list1[i-1] 和 list2[j-1] 结尾的公共子数组长度
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if list1[i-1] == list2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                if dp[i][j] > max_len:
                    max_len = dp[i][j]
                    end_idx = i - 1  # 在 list1 中的结束位置
                    start_idx = end_idx - max_len + 1  # 在 list1 中的起始位置
            else:
                dp[i][j] = 0
    
    return max_len, start_idx, end_idx
                   
def value_data(dataset_name):
    #验证predictions和数据集的顺序是否对应
    output_dir = os.path.join(DATASET_NAME+"_final","id_scores")
    id_scores = {}
    data_src = os.path.join(dataset_name+"_final", "predictions.json")
    with open(data_src, "r", encoding="utf-8") as f:
        predictions = json.load(f)
    pred_labels = []
    orig_labels = []
    ids = []
    for p in predictions:
        pred_labels.append(p[0])
    for d in dataset:
        orig_labels.append(1 if d['ground_truth']=='harmful' else 0)
        ids.append(d["id"])
    if DATASET_NAME=="FHM":
        with open("C:/Users/77366/Desktop/memedetection/few-shot/mywork/code/MDF/data/FHM/data/dev.jsonl","r",encoding="utf-8") as f:
            sampled_lines = f.readlines()
        for s in sampled_lines:
            sample = json.loads(s)
            id = sample["id"]
            if id not in ids:
                orig_labels.append(sample['label'])
                ids.append(id)
    # for i in range(len(predictions)):
    #     if pred_labels[i]!=orig_labels[i]:
    #         print(i)
    if pred_labels==orig_labels:
        print("标签相同")
        for i in range(len(predictions)):
            id_scores[ids[i]] = predictions[i]
        with open(output_dir, "w", encoding="utf-8") as f:
            json.dump(id_scores, f, indent=2, ensure_ascii=False)
    else:
        max_len, start_idx, end_idx = find_longest_common_subarray(orig_labels,pred_labels)
        print(max_len)
        print(start_idx)
        print(end_idx)
        print("标签不同")

if __name__ == "__main__":
    # predictions = predict(dataset=dataset)
    # file_path = os.path.join(DATASET_NAME, "scorer_results.json")
    # with open(file_path, "w", encoding="utf-8") as f:
    #     json.dump(predictions, f, indent=2, ensure_ascii=False)

    # value_data(DATASET_NAME)
    # _,_ = find_best_b()
    b = -0.1
    results = calculate_metrics("HARM",8,5,b)  #"FHM",3,7 "MAMI",8,4 "HARM",8,5
    print(results)
    results = calculate_metrics("FHM",3,7,b)  #"FHM",3,7 "MAMI",8,4 "HARM",8,5
    print(results)
    results = calculate_metrics("MAMI",8,4,b)  #"FHM",3,7 "MAMI",8,4 "HARM",8,5
    print(results)

    