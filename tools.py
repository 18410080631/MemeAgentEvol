# tools.py
import os
import base64
import mimetypes
import fitz  # PyMuPDF
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_API_BASE,MODEL_NAME,TEMPERATURE,RECORD_PATH
import re
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score
class LLMTool:
    """封装LLM调用工具，替代原有的Agent类"""
    
    def __init__(self, model_name: str, temperature: float = 0.0):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        self.model_name = model_name
        self.temperature = temperature
    
    def call_llm(self, system_prompt: str, messages: list, max_tokens: int = 2048, 
                    temperature: float = None, meme_src: str = None,
                    timeout: int = 15, max_retries: int = 3) -> str:
        """调用LLM，支持多模态输入 + 超时重试"""
        import time
        from openai import APITimeoutError, APIConnectionError, RateLimitError

        content = []
        user_text_parts = [m["content"] for m in messages if m["role"] == "user" and isinstance(m["content"], str)]
        if user_text_parts:
            user_text = "\n".join(user_text_parts)
            content.append({"type": "text", "text": user_text})
        if meme_src:
            if meme_src.startswith(("http://", "https://")):
                image_url = meme_src
            else:
                mime_type, _ = mimetypes.guess_type(meme_src)
                mime_type = mime_type or "image/jpeg"
                with open(meme_src, "rb") as f:
                    b64_image = base64.b64encode(f.read()).decode('utf-8')
                image_url = f"data:{mime_type};base64,{b64_image}"
            content.append({"type": "image_url", "image_url": {"url": image_url}})

        full_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            if msg["role"] != "user":
                full_messages.append(msg)
        full_messages.append({"role": "user", "content": content})

        # 重试逻辑
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=full_messages,
                    temperature=temperature if temperature is not None else self.temperature,
                    max_tokens=max_tokens,
                    timeout=timeout, # ← 关键：15秒超时
                    # extra_body={"enable_thinking":False},
                )
                return response.choices[0].message.content.strip()
            except (APITimeoutError, APIConnectionError, RateLimitError) as e:
                if attempt == max_retries - 1:  # 最后一次重试仍失败
                    print(f"LLM call failed after {max_retries}") 
                time.sleep(2 ** attempt)  # 指数退避：2s, 4s, 8s...

def get_description_of_meme(meme_text: str,meme_src:str) -> str:
    """获取对meme的客观描述"""
    system_prompt = """
You are a precision Image-to-Text Transcriber. Your goal is to provide objective, high-density visual data for accessibility indexing. 
You need to Generate a Concise Visual description Follow the format and style below:
Example1:
Visual Audit Summary: /n1. Subjects: One female individual with reddish-brown hair in a ponytail, wearing a dark short-sleeved dress with a black belt and large hoop earrings. She is depicted in a high-step, straddling motion, with her left leg planted on the ground outside the vehicle and her right leg raised and bent at a sharp angle, with the foot resting inside the car on or near the red bucket seat, suggesting an awkward attempt to step into or out of a low-slung car. Her torso is bent forward, looking down toward the raised leg. Due to this high-leg-lift posture and the short length of the dark dress, the skirt is hiked up high along her raised thigh, and her grey or off-white undergarment and the tops of her inner thighs are clearly visible and exposed to the camera between her legs and the dress hem. /n2. Text: 'THERE ARE MULTIPLE REASONS TO LOWER YOUR CAR' in bold white sans-serif uppercase letters at the top; 'THIS IS ONE OF THEM' in bold white sans-serif uppercase letters at the bottom. /n3. Setting: The interior and open door area of a car with red and black leather bucket seats. /n4. Graphic Overlays: Vertical watermarks reading 'VIA 9GAG.COM' on the left edge and 'MemeCenter.com' on the right edge. /n5. Image Medium: Photograph with digital text overlay in meme format.
Example2:
Visual Audit Summary: /n1. Subjects: A person in black clothing performing a jump to brace their limbs against the walls of a hallway, avoiding contact with the floor. The original head is obscured by a cropped image of a woman with glasses and an expressive facial expression (commonly known as the 'Big Red' or 'feminist' meme face). /n2. Text: 'The floor is the fact women are inferior to men' in black sans-serif text at the top; 'Fe🅱️inism' in black sans-serif text at the bottom, featuring a red square 'B' emoji. /n3. Setting: A brightly lit, empty institutional hallway with white walls, a tan floor, and a wooden door. /n4. Graphic Overlays: A cropped square image of a woman's face superimposed over the jumper's head; a red square 'B' emoji replacing the 'm' in 'Feminism'. /n5. Image Medium: Two-panel digital composite meme based on the 'The Floor is Lava' challenge. 
Example3:
Visual Audit Summary: /n1. Subjects: Two male characters from the Marvel Cinematic Universe. Left: Tom Holland as Peter Parker/Spider-Man in the Iron Spider suit. Right: Benedict Cumberbatch as Doctor Stephen Strange in his superhero attire and Cloak of Levitation. /n2. Text: Top-left: 'USA' and 'We have 250,000 cases'; Top-right: 'China' and 'We have 85,000'; Bottom-left: 'Oh, we're using our made up numbers then. So we have like 10 cases.' /n3. Setting: A dark, metallic, or cavernous interior environment, specifically a scene from 'Avengers: Infinity War'. /n4. Graphic Overlays: White text boxes with black sans-serif text placed over the original subtitles area. /n5. Image Medium: Four-panel digital meme using screenshots from a film. 
Example4:
Visual Audit Summary: /n1. Subjects: Two female individuals with light blonde hair. The woman on the left exhibits a contrasting lack of concern for social etiquette; she is hunched forward in a mustard shirt, gripping a large sandwich with both hands and forcing it into her wide-open mouth. In stark contrast, the woman on the right maintains a conventional social poise; she sits upright in a navy blue floral robe, smiling composedly at the camera while neatly holding her phone and sandwich. /n2. Text: 'There are two types of women...' in white sans-serif letters with a thick black outline at the bottom. /n3. Setting: A wooden bench in an outdoor park or wooded area with trees and sunlight in the background. /n4. Graphic Overlays: Impact-style digital text overlay. /n5. Image Medium: Digital photograph with text overlay in a comparative meme format.
"""
    evidence_judge_template = (
"""
Give the discription of the Image I provide to you: 
"""
    )
    llm_tool = LLMTool(model_name=MODEL_NAME, temperature=1.0)
    fact_judge_response = llm_tool.call_llm(
        system_prompt=system_prompt,
        messages=[{"role": "user", "content": evidence_judge_template}],
        meme_src=meme_src,
        temperature=TEMPERATURE,
        max_tokens=4096
    )
    # print(f"✅ 模因描述: {fact_judge_response}")
    return fact_judge_response

def extract_pdf_text(pdf_path: str) -> str:
    """从 PDF 提取全文文本"""
    print("正在提取原文相关部分")
    if not os.path.exists(pdf_path):
        return f"[ERROR: PDF not found at {pdf_path}]"
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    print(len(text))
    llm_tool = LLMTool(model_name=MODEL_NAME,temperature=TEMPERATURE)
    system_prompt = """你是一名标准提取器，请从论文中系统梳理并详细阐述模因（meme）被判定为“有害”（harmful）与“无害”（harmless）的具体判别标准。要求如下：
全面归纳两类判定的核心依据；
每条标准需引用论文原文中的关键表述作为佐证；
-以 JSON 格式返回结果，结构如下：
{
  "有害标准": {
    "标准1": {
      "内容": "...",
      "对应原文": "..."
    },
    "标准2": {
      "内容": "...",
      "对应原文": "..."
    },
    ...
  },
  "无害标准": {
    "标准1": {
      "内容": "...",
      "对应原文": "..."
    },
    "标准2": {
      "内容": "...",
      "对应原文": "..."
    },
    ...
  }
}
-所提取的标准应尽可能完整，内容能多详细多详细，不遗漏论文中任何相关判别依据。
"""
    response = llm_tool.call_llm(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": f"论文原文：{text}"}],
        )
    # print(f"论文标准：\n\n{response}")
    return response

def extract_code_from_markdown(s: str) -> str:
    # 匹配 ```language\n...``` 或 ```\n...```
    match = re.search(r'```(?:\w+)?\s*\n(.*?)\s*```', s, re.DOTALL)
    if match:
        return match.group(1)
    else:
        # 如果没有代码块标记，返回原字符串
        return s.strip()
    
def code_fix(code_str,para,error_info):
    llm_tool = LLMTool(model_name=MODEL_NAME,temperature=TEMPERATURE)
    print("正在对代码修复...")
    system_prompt = f"""你是一名python代码修复员，当前代码使用：
namespace = {{}}
exec(current_code, {{}}, namespace)
classify_func = namespace.get('classify_meme')
label = classify_func(scores)
运行报错：\n\n
{error_info}
当前入参：score:{para}\n\n
请你给出正确代码，代码要求：
函数名为 def classify_meme(scores)；函数实现应自包含，不调用外部方法或变量，即所有逻辑都写在classify_meme中，不要出现其他方法名与调用关系；
输入 scores 为符合原始格式的字典，包含 harmful_scores和 harmless_scores；
函数必须返回字符串 'harmless' 或 'harmful'；
仅使用 Python 标准库，不得引入任何第三方依赖；
仅输出该函数的完整代码，不包含任何注释、解释或其他额外文本。
输出格式：
```python\n
代码
```
    """
    response = llm_tool.call_llm(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": f"源代码：\n\n{code_str}"}],
        )
    code = extract_code_from_markdown(response)
    print(f"修复代码:{code}")
    return code

import re

def extract_dict_from_string(s: str):
    # 匹配以 "harmful_scores" 开头的 JSON 对象（支持多行、嵌套）
    pattern = r'\{\s*"harmful_scores"\s*:\s*\{[^{}]*\}\s*,\s*"harmless_scores"\s*:\s*\{[^{}]*\}\s*,\s*"reasoning"\s*:\s*"[^"]*"\s*\}'
    match = re.search(pattern, s, re.DOTALL)
    if match:
        return match.group()
   # 如果上面没匹配到（比如字段顺序不同），尝试更宽松的模式
    # 匹配包含这三个 key 的最外层 {...}
    loose_pattern = r'\{(?:[^{}]|(?:"(?:[^"\\]|\\.)*"))*\b"harmful_scores"\b(?:[^{}]|(?:"(?:[^"\\]|\\.)*"))*\b"harmless_scores"\b(?:[^{}]|(?:"(?:[^"\\]|\\.)*"))*\b"reasoning"\b(?:[^{}]|(?:"(?:[^"\\]|\\.)*"))*\}'
    # 但 Python re 不支持平衡组，所以改用：找包含这三个 key 的最大可能 {} 块
    # 更实用的做法：找最后一个可能的完整 {} 块（假设模板在末尾）
    start = s.rfind('{')
    if start == -1:
        raise ValueError("No '{' found")
    stack = 0
    for i in range(start, len(s)):
        if s[i] == '{':
            stack += 1
        elif s[i] == '}':
            stack -= 1
            if stack == 0:
                candidate = s[start:i+1]
                # 验证是否包含关键字段
                if '"harmful_scores"' in candidate and '"harmless_scores"' in candidate and '"reasoning"' in candidate:
                    return candidate
    raise ValueError("No valid template block found")


def train_logistic_regression(data, feature_names=None, C=1.0):
    """
    使用逻辑回归训练二分类模型。
    
    参数:
        data: List[List], 每个子列表为 [label, f1, f2, ..., fn]
        feature_names: 可选，特征名称列表（用于输出公式）
        C: 正则化强度（越小正则越强，默认 C=1.0）
    
    返回:
        dict 包含:
            - 'model': 训练好的 LogisticRegression 模型
            - 'scaler': StandardScaler 对象（用于 Python 环境 transform）
            - 'scaler_params': dict, {'mean': [...], 'scale': [...]}（可 JSON 保存）
            - 'weights': 特征权重（已还原到原始尺度）
            - 'intercept': 截距项
            - 'feature_names': 特征名
            - 'performance': {'accuracy': ..., 'f1': ...}
            - 'formula': 可读的线性判别公式字符串
            - 'train_predictions': 训练集预测标签
            - 'train_prediction_proba': 训练集预测概率
    """
    l = set()
    for d in data:
        l.add(d[0])
    if len(l)!=2:
        print(f"警告: 训练数据标签不唯一！标签集合: {l}，无法训练二分类模型。")
        return {
        'model': None,
        'scaler': None,
        'scaler_params': None,  # <-- 关键新增
        'weights': [],
        'intercept': 0.0,
        'feature_names': feature_names,
        'performance': {'accuracy': 1.0, 'f1': 1.0},
        'formula': "No model trained due to inconsistent labels.",
        'train_predictions': [],
        'train_prediction_proba': [],
        "feature_importance":[]
    }

    data = np.array(data)
    y = data[:, 0].astype(int)
    X_raw = data[:, 1:].astype(float)
    n_features = X_raw.shape[1]
    
    if feature_names is None:
        feature_names = [f'F{i}' for i in range(1, n_features + 1)]
    
    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    
    # 训练逻辑回归
    model = LogisticRegression(C=C, solver='liblinear', random_state=42)
    model.fit(X_scaled, y)
    
    # 还原权重到原始尺度
    weights_original = weights_original = [float(w) for w in (model.coef_[0] / scaler.scale_)]
    intercept_original = model.intercept_[0] - np.sum(model.coef_[0] * scaler.mean_ / scaler.scale_)
    
    # 性能评估
    y_pred = model.predict(X_scaled)
    acc = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred, zero_division=0)
    
    # 构建可读公式
    terms = []
    for w, name in zip(weights_original, feature_names):
        if w >= 0:
            terms.append(f"+ {w:.3f} * {name}")
        else:
            terms.append(f"- {abs(w):.3f} * {name}")
    linear_part = " ".join(terms).lstrip("+ ")
    formula = f"Logit = {linear_part} {'+' if intercept_original >= 0 else '-'} {abs(intercept_original):.3f}"
    scaled_weights = [float(w) for w in model.coef_[0]]
    feature_importance = [
        {"feature": name, "abs_weight": abs(w)}
        for name, w in zip(feature_names, scaled_weights)
    ]
    # ✅ 新增：提取 scaler 的可序列化参数
    scaler_params = {
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "n_features": int(n_features)
    }
    
    return {
        'model': model,
        'scaler': scaler,
        'scaler_params': scaler_params,  # <-- 关键新增
        'weights': weights_original,
        'intercept': intercept_original,
        'feature_names': feature_names,
        'performance': {'accuracy': acc, 'f1': f1},
        'formula': formula,
        'train_predictions': y_pred.tolist(),
        'train_prediction_proba': model.predict_proba(X_scaled).tolist(),
        "feature_importance":feature_importance
    }



def safe_append_markdown(filepath, content, max_size_mb=20):
    """
    安全追加：检查文件大小，避免过大
    
    参数:
        filepath: 文件路径
        content: 追加内容
        max_size_mb: 最大文件大小（MB）
    """
    directory = os.path.dirname(filepath)
    
    # 如果目录不存在，创建目录（包括父目录）
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    # 检查文件大小
    if os.path.exists(filepath):
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if size_mb > max_size_mb:
            print(f"警告: 文件超过 {max_size_mb}MB")
            return False
    
    # 追加内容
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write('\n---\n\n')  # 添加分隔线
        f.write(content)
        f.write('\n')
    
    # print(f"✓ 成功追加到 {filepath}")
    return True

import json
import math
from typing import Union, List, Dict
from config import DATASET_NAME
def save_model_minimal(result: Dict, filepath: str = f'{DATASET_NAME}/best_model.json'):
    """
    最小化保存模型（仅保存预测必需参数）
    
    参数:
        result: train_logistic_regression 的返回字典
        filepath: 保存路径
    """
    save_data = {
        'weights': result['weights'],
        'intercept': float(result['intercept']),
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(save_data, f)
    print(f"✓ 模型已保存：{filepath}")

def predict_eval(filepath: str, samples: Union[List, List[List]]) -> Dict:
    """
    加载模型并预测
    
    参数:
        filepath: 模型文件路径
        samples: 样本数据（与训练格式一致）
                 - 单样本：[label, f1, f2, ..., fn]
                 - 多样本：[[label, f1, f2, ...], [label, f1, f2, ...], ...]
                 - label 用于计算准确率/F1，如果为 -1 或 None 表示无标签
    
    返回:
        dict: 包含预测结果、概率、准确率、F1 等
    """
    # 加载模型参数
    with open(filepath, 'r', encoding='utf-8') as f:
        params = json.load(f)
    
    weights = params['weights']
    intercept = params['intercept']
    n_features = len(weights)
    
    # 数据预处理（统一转为列表的列表）
    if not isinstance(samples[0], (list, tuple)):
        samples = [samples]
    
    # 分离标签和特征
    y_true = []
    X = []
    has_label = True
    
    for sample in samples:
        label = sample[0]
        features = sample[1:]
        
        # 检查特征数量
        if len(features) != n_features:
            raise ValueError(f"特征数量不匹配！期望 {n_features}, 得到 {len(features)}")
        
        # 判断是否有有效标签（-1 或 None 表示无标签）
        if label in [-1, None, 'null']:
            has_label = False
            y_true.append(None)
        else:
            y_true.append(int(label))
        
        X.append(features)
    
    # Sigmoid 函数
    def sigmoid(x):
        # 防止溢出
        if x >= 0:
            return 1 / (1 + math.exp(-x))
        else:
            exp_x = math.exp(x)
            return exp_x / (1 + exp_x)
    
    # 预测每个样本
    predictions = []
    probabilities = []
    
    for features in X:
        logit = sum(w * xi for w, xi in zip(weights, features)) + intercept
        prob = sigmoid(logit)
        pred = 1 if prob >= 0.5 else 0
        predictions.append(pred)
        probabilities.append(round(prob, 6))
    
    # 构建基础结果
    result = {
        'count': len(samples),
        'predictions': predictions if len(predictions) > 1 else predictions[0],
        'probabilities': probabilities if len(probabilities) > 1 else probabilities[0]
    }
    
    # 如果有真实标签，计算评估指标
    if has_label and None not in y_true:
        # 准确率
        correct = sum(p == t for p, t in zip(predictions, y_true))
        accuracy = correct / len(y_true)
        
        # 混淆矩阵
        tp = sum(1 for p, t in zip(predictions, y_true) if p == 1 and t == 1)
        fp = sum(1 for p, t in zip(predictions, y_true) if p == 1 and t == 0)
        tn = sum(1 for p, t in zip(predictions, y_true) if p == 0 and t == 0)
        fn = sum(1 for p, t in zip(predictions, y_true) if p == 0 and t == 1)
        
        # 精确率、召回率、F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        result.update({
            'accuracy': round(accuracy, 4),
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4),
            'confusion_matrix': {
                'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn
            },
            'correct_count': correct,
            'total_count': len(y_true)
        })
    else:
        result['has_label'] = False
    
    return result

def caculate_acc(labels, h_n_scores):
    predict = []
    for i in range(len(labels)):
        scores_0 = h_n_scores[i][0]
        scores_1 = h_n_scores[i][1]
        avg_0 = sum(scores_0) / len(scores_0) if scores_0 else 0
        avg_1 = sum(scores_1) / len(scores_1) if scores_1 else 0
        if avg_0 > avg_1:
            predict.append(1)
        else:
            predict.append(0)
    y_true = [1 if label == "harmful" else 0 for label in labels]
    if len(predict) == 0:
        accuracy = 0.0
    else:
        correct_nums = sum(1 for t, p in zip(y_true, predict) if t == p)
        accuracy = correct_nums / len(predict)
    f1 = 0.0
    unique_labels = set(y_true)
    if len(unique_labels) < 2:
        f1 = 0.0
    else:
        f1_scores = []
        for class_val in [0, 1]:
            tp = sum(1 for t, p in zip(y_true, predict) if t == class_val and p == class_val)
            fp = sum(1 for t, p in zip(y_true, predict) if t != class_val and p == class_val)
            fn = sum(1 for t, p in zip(y_true, predict) if t == class_val and p != class_val)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            if precision + recall > 0:
                f1_class = 2 * (precision * recall) / (precision + recall)
            else:
                f1_class = 0
            f1_scores.append(f1_class)
        f1 = sum(f1_scores) / len(f1_scores)
    return {'accuracy': accuracy, 'f1': f1}, predict


import pandas as pd
import numpy as np

def analyze_score_features(labels, h_titles, h_scores, s_titles, s_scores, threshold_low=3, threshold_high=7, top_k=5):
    # 1. 标签预处理
    num_labels = [1 if l == "harmful" or l == 1 else 0 for l in labels]
    
    df_h = pd.DataFrame(h_scores, columns=h_titles)
    df_s = pd.DataFrame(s_scores, columns=s_titles)
    df_h['label'] = num_labels
    df_s['label'] = num_labels

    # 定义内部过滤函数：比例 > 0.4 才保留名称
    def get_frequent_dims(series, threshold=0.4):
        filtered = series[series > threshold]
        if filtered.empty:
            return "没有相关维度"
        # 只返回维度名称（index），如果想看比例可以加上 .to_string()
        return ", ".join(filtered.index.tolist())

    results = {}
    
    # --- 计算各维度的异常比例 ---
    h_pos = df_h[df_h['label'] == 1].drop(columns=['label'])
    s_pos = df_s[df_s['label'] == 1].drop(columns=['label'])
    h_neg = df_h[df_h['label'] == 0].drop(columns=['label'])
    s_neg = df_s[df_s['label'] == 0].drop(columns=['label'])

    # 逻辑核心：计算 mean (比例)
    pos_low_h = (h_pos <= threshold_low).mean()
    pos_high_s = (s_pos >= threshold_high).mean()
    neg_high_h = (h_neg >= threshold_high).mean()
    neg_low_s = (s_neg <= threshold_low).mean()

    # --- 构造 Report ---
    report1 = "### 1. 有害样本 (Label=1) 表现异常建议删除的维度 ###\n"
    report1 += f"【漏报维度】(Harmful打分过低): {get_frequent_dims(pos_low_h)}\n"
    report1 += f"【误导维度】(Harmless打分过高): {get_frequent_dims(pos_high_s)}\n"

    report2 = "### 2. 无害样本 (Label=0) 表现异常建议删除的维度 ###\n"
    report2 += f"【误报维度】(Harmful打分过高): {get_frequent_dims(neg_high_h)}\n"
    report2 += f"【偏差维度】(Harmless打分过低): {get_frequent_dims(neg_low_s)}\n"

    # 3. 全局静态维度 (方差极小)
    all_scores = pd.concat([df_h.drop(columns=['label']), df_s.drop(columns=['label'])], axis=1)
    static_series = all_scores.std().sort_values()
    # 假设标准差小于 0.1 认为是“基本不变”
    static_dims = static_series[static_series < 0.1]
    report = "### 3. 分数基本无变化的无效维度 ###\n"
    report += (", ".join(static_dims.index.tolist()) if not static_dims.empty else "没有相关维度") + "\n"

    return report, report1, report2

import os
import json

class PredictionSaver:
    def __init__(self, dataset_name):
        """
        初始化预测保存器
        :param dataset_name: 数据集名称（也将作为文件夹名）
        """
        self.dataset_name = dataset_name
        self.cache_path = os.path.join(dataset_name, "prediction_cache.json")
        # 确保目录存在
        os.makedirs(self.dataset_name, exist_ok=True)
        # 如果缓存文件不存在，创建初始化的空 JSON 文件
        if not os.path.exists(self.cache_path):
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)
    def _load_data(self):
        """加载 JSON 数据"""
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    def _save_data(self, data):
        """保存 JSON 数据"""
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    def save(self, round_id, meme_id, response):
        """
        保存预测结果
        :param round_id: 轮次 (int 或 str)
        :param meme_id: 图片/数据 ID (int 或 str)
        :param response: 预测结果 (任意可 JSON 序列化对象)
        """
        data = self._load_data()
        # 统一转为字符串，因为 JSON 键只能是字符串
        r_key = str(round_id)
        m_key = str(meme_id)
        if r_key not in data:
            data[r_key] = {}
        data[r_key][m_key] = response
        self._save_data(data)
    def get(self, round_id, meme_id):
        """
        获取预测结果
        :param round_id: 轮次
        :param meme_id: 图片/数据 ID
        :return: 预测结果，如果不存在则返回 None
        """
        data = self._load_data()
        r_key = str(round_id)
        m_key = str(meme_id)
        if r_key in data and m_key in data[r_key]:
            return data[r_key][m_key]
        return None
    def has_cached(self, round_id, meme_id):
        """
        检查是否已缓存
        :return: True/False
        """
        return self.get(round_id, meme_id) is not None
    def get_round_all(self, round_id):
        """
        获取某一轮次的所有预测结果
        :return: 字典或空字典
        """
        data = self._load_data()
        r_key = str(round_id)
        return data.get(r_key, {})

class DescriptionSaver:
    def __init__(self, dataset_name):
        """
        初始化预测保存器
        :param dataset_name: 数据集名称（也将作为文件夹名）
        """
        self.dataset_name = dataset_name
        self.cache_path = os.path.join(dataset_name, "description_cache.json")
        # 确保目录存在
        os.makedirs(self.dataset_name, exist_ok=True)
        # 如果缓存文件不存在，创建初始化的空 JSON 文件
        if not os.path.exists(self.cache_path):
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)
    def _load_data(self):
        """加载 JSON 数据"""
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    def _save_data(self, data):
        """保存 JSON 数据"""
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    def save(self, meme_id, response):
        """
        保存预测结果
        :param round_id: 轮次 (int 或 str)
        :param meme_id: 图片/数据 ID (int 或 str)
        :param response: 预测结果 (任意可 JSON 序列化对象)
        """
        data = self._load_data()
        # 统一转为字符串，因为 JSON 键只能是字符串
        m_key = str(meme_id)
        data[m_key] = response
        self._save_data(data)
    def get(self,meme_id):
        """
        获取预测结果
        :param round_id: 轮次
        :param meme_id: 图片/数据 ID
        :return: 预测结果，如果不存在则返回 None
        """
        data = self._load_data()
        m_key = str(meme_id)
        if m_key in data:
            return data[m_key]
        return None