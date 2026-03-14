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
                    timeout=timeout  # ← 关键：15秒超时
                )
                return response.choices[0].message.content.strip()
            except (APITimeoutError, APIConnectionError, RateLimitError) as e:
                if attempt == max_retries - 1:  # 最后一次重试仍失败
                    print(f"LLM call failed after {max_retries}") 
                time.sleep(2 ** attempt)  # 指数退避：2s, 4s, 8s...

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

def caculate_acc(labels,h_n_scores):
    predict = []
    for i in range(len(labels)):
        if sum(h_n_scores[i][0]) / len(h_n_scores[i][0]) > sum(h_n_scores[i][1]) / len(h_n_scores[i][1]):
            predict.append(1)
        else:
            predict.append(0)
    correct_nums = 0
    for i in range(len(predict)):
        labelsi = 1 if labels[i] == "harmful" else 0
        if labelsi == predict[i]:
            correct_nums+=1
    return  {'accuracy': correct_nums / len(predict), 'f1': 0},predict
            
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

def analyze_misclassified_memes(data_list, labels):
    # 1. 预测逻辑：Avg(Harmful) > Avg(Harmless) -> Predict 1
    predictions = []
    for item in data_list:
        h_scores = list(item['harmful_scores'].values())
        n_scores = list(item['harmless_scores'].values())
        avg_h = sum(h_scores) / len(h_scores) if h_scores else 0
        avg_n = sum(n_scores) / len(n_scores) if n_scores else 0
        predictions.append(1 if avg_h > avg_n else 0)

    # 分类误判样本索引
    # FN: 有害(1)误判为无害(0) | FP: 无害(0)误判为有害(1)
    fn_indices = [i for i, (p, l) in enumerate(zip(predictions, labels)) if p == 0 and l == 1]
    fp_indices = [i for i, (p, l) in enumerate(zip(predictions, labels)) if p == 1 and l == 0]

    def get_stat_str(indices, title, total_count, mode):
        if total_count == 0:
            return f"### {title}\n无相关误判样本。\n"
        
        # 统计容器
        high_counts = {}     # 分数 > 7 的维度 (针对误判方向)
        moderate_counts = {} # 分数 > 5 且 <= 7 的维度
        low_counts = {}      # 分数 < 3 的维度
        
        for idx in indices:
            item = data_list[idx]
            if mode == "FP": # 无害判为有害：找偏高的有害维度和偏低的无害维度
                for dim, score in item['harmful_scores'].items():
                    if score > 7: high_counts[dim] = high_counts.get(dim, 0) + 1
                    elif score > 5: moderate_counts[dim] = moderate_counts.get(dim, 0) + 1
                for dim, score in item['harmless_scores'].items():
                    if score < 2: low_counts[dim] = low_counts.get(dim, 0) + 1
            
            elif mode == "FN": # 有害判为无害：找偏高的无害维度和偏低的有害维度
                for dim, score in item['harmless_scores'].items():
                    if score > 7: high_counts[dim] = high_counts.get(dim, 0) + 1
                    elif score > 5: moderate_counts[dim] = moderate_counts.get(dim, 0) + 1
                for dim, score in item['harmful_scores'].items():
                    if score < 2: low_counts[dim] = low_counts.get(dim, 0) + 1

        # 过滤符合比例条件的维度
        res_high = [dim for dim, count in high_counts.items() if count > total_count / 3]
        res_mod = [dim for dim, count in moderate_counts.items() if count > total_count / 3]
        res_low = [dim for dim, count in low_counts.items() if count > total_count / 2]
        
        target_high_type = "有害维度" if mode == "FP" else "无害维度"
        target_low_type = "无害维度" if mode == "FP" else "有害维度"

        res_str = f"### {title} (样本总数: {total_count})\n"
        res_str += f"- 异常偏高{target_high_type} 建议删除 : {', '.join(res_high) or '无'}\n"
        res_str += f"- 轻微偏高{target_high_type} 建议重写大改: {', '.join(res_mod) or '无'}\n"
        res_str += f"- 显著偏低{target_low_type} 建议删除 (Score<2, 频率>1/2): {', '.join(res_low) or '无'}\n"
        return res_str

    
    # FP: 统计有害分数高、无害分数低的异常
    report1 = get_stat_str(fp_indices, "无害误判为有害 (FP / 误报)", len(fp_indices), "FP")
    # FN: 统计无害分数高、有害分数低的异常
    report2 = get_stat_str(fn_indices, "有害误判为无害 (FN / 漏报)", len(fn_indices), "FN")
    
    return [report1,report2]