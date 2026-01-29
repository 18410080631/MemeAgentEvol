# tools.py
import os
import base64
import mimetypes
import fitz  # PyMuPDF
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_API_BASE,MODEL_NAME,TEMPERATURE
import re
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score
class LLMTool:
    """封装LLM调用工具，替代原有的Agent类"""
    
    def __init__(self, model_name: str, temperature: float = 0.3):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        self.model_name = model_name
        self.temperature = temperature
    
    def call_llm(self, system_prompt: str, messages: list, max_tokens: int = 4096, 
                temperature: float = None, meme_src: str = None) -> str:
        """调用LLM，支持多模态输入"""
        content = []
        # 合并所有 user 消息的文本内容
        user_text_parts = [m["content"] for m in messages if m["role"] == "user" and isinstance(m["content"], str)]
        if user_text_parts:
            user_text = "\n".join(user_text_parts)
            content.append({"type": "text", "text": user_text})
        # 添加图像（如果提供）
        if meme_src:
            if meme_src.startswith(("http://", "https://")):
                image_url = meme_src
            else:
                mime_type, _ = mimetypes.guess_type(meme_src)
                if mime_type is None:
                    mime_type = "image/jpeg"
                with open(meme_src, "rb") as f:
                    b64_image = base64.b64encode(f.read()).decode('utf-8')
                image_url = f"data:{mime_type};base64,{b64_image}"
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        
        # 构建完整消息（system + 历史 + 新 user 内容）
        full_messages = [
            {"role": "system", "content": system_prompt}
        ]
        # 保留非 user 的历史消息（如 assistant 回复，虽然当前未用）
        for msg in messages:
            if msg["role"] != "user":
                full_messages.append(msg)
        # 最后添加新的多模态 user 消息
        full_messages.append({"role": "user", "content": content})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=full_messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()

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

import ast
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