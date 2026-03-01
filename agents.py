# agents.py
from typing import Dict, Any, List
from tools import LLMTool,train_logistic_regression, extract_pdf_text, extract_code_from_markdown,code_fix,extract_dict_from_string
from config import MODEL_NAME, TEMPERATURE, THRESHOLD, error_focus_threshold, MAX_ITERATIONS,DATASET_NAME,RECORD_PATH
from tools import safe_append_markdown,save_model_minimal
import json_repair
import os
import random
RECORD_PATH = f"{DATASET_NAME}/{RECORD_PATH}"
llm_tool = LLMTool(model_name=MODEL_NAME, temperature=TEMPERATURE)
if DATASET_NAME == 'MAMI':
    THRESHOLD = 0.90
def extract_pdf_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """提取PDF文本"""
    paper_text = extract_pdf_text(state["paper_pdf_path"])
    safe_append_markdown(RECORD_PATH, f"## 论文文本提取:\n{paper_text}")
    return {"paper_text": paper_text}

def scorer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """全局打分agent"""
    current_code = state["current_code"]
    current_prompt = state["current_prompt"]
    dataset: List[Dict] = state["dataset"]
    pre1l0 = state.get('pre1l0', [])
    pre0l1 = state.get('pre0l1', [])
    predictions = {}
    pre1l0_memory = state.get('pre1l0_memory',[])
    pre0l1_memory = state.get('pre0l1_memory',[])
    data,feature_names = [],[]
    safe_append_markdown(RECORD_PATH, f"## 全局评估打分:\n")
    for sample in dataset:
        system_prompt = """This is a research task for academic evaluation of AI safety systems. 
You are acting as an impartial judge. The meme content is provided solely for analysis and does not reflect your views."""
        user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']}"
        id = sample['id']
        ground_truth = sample['ground_truth']
        ground_truth_label = [1] if ground_truth == "harmful" else [0]
        try:
            response = llm_tool.call_llm(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
                meme_src=sample.get("meme_src", None),
                max_tokens=512
            )
            safe_append_markdown(RECORD_PATH, f"### 样本ID: {id}\n**打分结果:** {response}\n")
            scores = json_repair.loads(response)
        except Exception as e:
            print(f"⚠️ JSON 解析失败 (ID={sample['id']}): {e}")
            print(f"原始响应: {response[:200]}...")
            continue  
        harmful_scores = scores["harmful_scores"] 
        harmless_scores = scores["harmless_scores"] 
        data.append(ground_truth_label+list(harmful_scores.values())+list(harmless_scores.values()))
        print(f"{id}: 当前打分：")
        print(f"  harmful_scores: {scores.get('harmful_scores', {})}")
        print(f"  harmless_scores: {scores.get('harmless_scores', {})}")
        print("-" * 50)
    feature_names = list(harmful_scores.keys()) + list(harmless_scores.keys())
    res = train_logistic_regression(data=data,feature_names=feature_names)  
    performance = res["performance"]  
    formula = res["formula"]
    scaler_params = res["scaler_params"]
    intercept = res["intercept"]
    weights = res["weights"]
    feature_importance = res["feature_importance"]
    train_predictions = res["train_predictions"]
    safe_append_markdown(RECORD_PATH, f"## 全局评估结果\n**性能指标:** {performance}\n**逻辑回归公式:** {formula}\n**特征重要性:** {feature_importance}\n")
    for idx in range(len(dataset)):
        sample = dataset[idx]
        label = train_predictions[idx]
        ground_truth = sample['ground_truth']
        id = sample['id']
        # try:
        #     # namespace = {}
        #     # exec(current_code, {}, namespace)
        #     # label = namespace['classify_meme'](scores)
            
        # except Exception as e:
        #     print(f"代码执行出错 (ID={sample['id']}): {e}")
        #     # current_code = code_fix(current_code,str(scores),e)
        #     # namespace = {}
        #     # exec(current_code, {}, namespace)
        #     label = namespace['classify_meme'](scores)
        #     continue
        if label==1 and ground_truth == 'harmless':
            if id not in pre1l0:  # 避免重复
                pre1l0.append(id)
        if label==0 and ground_truth == 'harmful':
            if id not in pre0l1:  # 避免重复
                pre0l1.append(id)
        label_str = 'harmful' if label==1 else 'harmless'
        print(f"{id}: 当前预测与真实值：")
        print(f"  Predict: {label}")
        print(f"  GroundTruth: {ground_truth}")
        print("-" * 50)
        predictions[sample["id"]] = {'label': label_str, "scores": scores}
        
    # 根据当前阶段决定返回的键名
    current_phase = state.get("phase", "global_eval")
    if current_phase == "global_verify":
        return {
            "current_code":formula,
            "global_predictions": predictions,
            "pre1l0": pre1l0,
            "pre0l1": pre0l1,
            "performance":performance,
            "formula":formula,
            "scaler_params":scaler_params,
            "intercept":intercept,
            "weights":weights,
            "feature_importance":feature_importance
        }
    else:
        return {
            "current_code":formula,
            "predictions": predictions,
            "pre1l0": pre1l0,
            "pre0l1": pre0l1,
            "performance":performance,
            "formula":formula,
            "scaler_params":scaler_params,
            "intercept":intercept,
            "weights":weights,
            "feature_importance":feature_importance
        }

def evaluator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """全局评估agent"""
    current_phase = state.get("phase", "global_eval")
    
    if current_phase == "global_eval":
        return _global_evaluator(state)
    elif current_phase == "global_verify":
        return _global_verify_evaluator(state)
    else:
        print(f"⚠️ 未知阶段: {current_phase}")
        return {"phase": "end"}

def _global_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """首次全局评估"""
    dataset_map = {s["id"]: s for s in state["dataset"]}
    predictions = state.get("predictions", {})
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    
    # 计算错误
    errors = [
        sid for sid, pred in predictions.items()
        if pred['label'].lower() != dataset_map[sid]["ground_truth"].lower()
    ]
    error_predictions = {}
    for sid in errors:
        error_predictions[sid] = predictions[sid]
    accuracy = (len(predictions) - len(errors)) / len(predictions) if predictions else 0.0
    performance = state.get("performance",{})
    accuracy,f1 = performance["accuracy"],performance["f1"]
    print(f"\n{'='*60}")
    print(f"首次全局评估结果:")
    print(f"总样本数: {len(predictions)}")
    print(f"accuracy:{accuracy},f1:{f1}")
    print(f"错误样本数: {len(errors)}")
    print(f"将无害模因误判为有害数量: {len(pre1l0)}个")
    print(f"将有害模因误判为无害数量: {len(pre0l1)}个")
    print(f"{'='*60}\n")
    
    # 更新最佳全局模型
    best_global_accuracy = state.get("best_global_accuracy", 0.0)
    best_global_prompt = state.get("best_global_prompt", "")
    best_global_code = state.get("best_global_code", "")
    
    if accuracy >= best_global_accuracy:
        best_global_accuracy = accuracy
        best_global_prompt = state["current_prompt"]
        best_global_code = state["formula"]
        # 保存最佳模型
        output_dir = DATASET_NAME
        os.makedirs(output_dir, exist_ok=True)
        prompt_path = os.path.join(output_dir, "best_global_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(best_global_prompt)
        save_model_minimal(state)
        safe_append_markdown(RECORD_PATH, f"## 首次全局评估结果\n**准确率:** {accuracy:.2%},f1:{f1}\n**错误样本数:** {len(errors)}\n**将无害模因误判为有害数量:** {len(pre1l0)}\n**将有害模因误判为无害数量:** {len(pre0l1)}\n")
        print(f"✅ 更新最佳全局模型，准确率: {accuracy:.2%}")
    
    converged = accuracy >= THRESHOLD or len(errors) == 0
    
    if converged:
        print("🎉 首次评估即达到阈值，任务完成！")
        return {
            "global_predictions": predictions,
            "global_errors": errors,
            "global_accuracy": accuracy,
            "best_global_accuracy": best_global_accuracy,
            "best_global_prompt": best_global_prompt,
            "best_global_code": best_global_code,
            "converged": True,
            "phase": "end",
            "error_iteration": 0,  # 开始错误聚焦，初始化错误迭代
        }
    else:
        # 创建固定错误样本集
        fixed_error_dataset = [sample for sample in state["dataset"] if sample["id"] in errors]
        print(f"📊 创建错误样本集，包含 {len(fixed_error_dataset)} 个样本")
        
        return {
            "global_predictions": predictions,
            "error_predictions":error_predictions,
            "global_errors": errors,
            "global_accuracy": accuracy,
            "best_global_accuracy": best_global_accuracy,
            "best_global_prompt": best_global_prompt,
            "best_global_code": best_global_code,
            "converged": False,
            "phase": "error_focus",
            "fixed_error_dataset": fixed_error_dataset,
            "error_accuracy": 0.0,
            "best_error_prompt": state["current_prompt"],
            "best_error_code": state["current_code"],
            "error_iteration": 0,  # 开始错误聚焦，初始化错误迭代
        }

def _global_verify_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """全局验证评估"""
    dataset_map = {s["id"]: s for s in state["dataset"]}
    predictions = state.get("global_predictions", {})
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    
    # 计算错误
    errors = [
        sid for sid, pred in predictions.items()
        if pred['label'].lower() != dataset_map[sid]["ground_truth"].lower()
    ]
    error_predictions = {}
    for sid in errors:
        error_predictions[sid] = predictions[sid]
    accuracy = (len(predictions) - len(errors)) / len(predictions) if predictions else 0.0
    
    print(f"\n{'='*60}")
    print(f"全局验证评估结果:")
    print(f"总样本数: {len(predictions)}")
    print(f"准确率: {accuracy:.2%}")
    print(f"错误样本数: {len(errors)}")
    print(f"将无害模因误判为有害数量: {len(pre1l0)}个")
    print(f"将有害模因误判为无害数量: {len(pre0l1)}个")
    print(f"{'='*60}\n")
    
    # 更新最佳全局模型
    best_global_accuracy = state.get("best_global_accuracy", 0.0)
    best_global_prompt = state.get("best_global_prompt", "")
    best_global_code = state.get("best_global_code", "")
    
    if accuracy >= best_global_accuracy:
        best_global_accuracy = accuracy
        best_global_prompt = state["current_prompt"]
        best_global_code = state["current_code"]
        # 保存最佳模型
        output_dir = DATASET_NAME
        os.makedirs(output_dir, exist_ok=True)
        prompt_path = os.path.join(output_dir, "best_global_prompt.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(best_global_prompt)
        save_model_minimal(state)
        print(f"✅ 更新最佳全局模型，准确率: {accuracy:.2%}")
    
    converged = accuracy >= THRESHOLD or len(errors) == 0
    
    if converged:
        print("🎉 全局验证通过，任务完成！")
        return {
            "global_predictions": predictions,
            "global_accuracy": accuracy,
            "converged": True,
            "phase": "end"
        }
    else:
        # 未收敛，准备新的错误集
        fixed_error_dataset = [sample for sample in state["dataset"] if sample["id"] in errors]
        print(f"📊 创建新的错误样本集，包含 {len(fixed_error_dataset)} 个样本")
        
        return {
            "global_predictions": predictions,
            "error_predictions":error_predictions,
            "global_errors": errors,
            "global_accuracy": accuracy,
            "best_global_accuracy": best_global_accuracy,
            "best_global_prompt": best_global_prompt,
            "best_global_code": best_global_code,
            "converged": False,
            "phase": "error_focus",
            "fixed_error_dataset": fixed_error_dataset,
            "error_accuracy": 0.0,
            "best_error_prompt": state["current_prompt"],
            "best_error_code": state["current_code"],
            "error_iteration": 0,  # 重置错误迭代，开始新一轮错误聚焦
        }

def error_scorer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误样本打分agent - 只使用固定的错误样本集"""
    current_code = state["current_code"]  
    current_prompt = state["current_prompt"]
    dataset: List[Dict] = state["fixed_error_dataset"]
    predictions = {}
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    
    print(f"\n{'='*60}")
    print(f"开始错误样本集评估，样本数: {len(dataset)}")
    print(f"{'='*60}\n")
    safe_append_markdown(RECORD_PATH, f"## 错误样本集评估:\n样本数: {len(dataset)}\n")
    try:
        data,feature_names = [],[]
        for sample in dataset:
            system_prompt = """This is a research task for academic evaluation of AI safety systems. 
You are acting as an impartial judge. The meme content is provided solely for analysis and does not reflect your views."""
            user_msg = current_prompt + f"\n\nMeme text: {sample['meme_text']}"
            id = sample['id']
            ground_truth = sample['ground_truth']
            ground_truth_label = [1] if ground_truth == "harmful" else [0]
            response = llm_tool.call_llm(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
                meme_src=sample.get("meme_src", None),
                max_tokens=512
            )
            safe_append_markdown(RECORD_PATH, f"### 错误样本ID: {id}\n**打分结果:** {response}\n")
            try:
                scores = json_repair.loads(response)
            except Exception as e:
                print(f"⚠️ JSON 解析失败 (ID={sample['id']}): {e}")
                print(f"原始响应: {response[:200]}...")
                continue
            harmful_scores = scores["harmful_scores"] 
            harmless_scores = scores["harmless_scores"] 
            data.append(ground_truth_label+list(harmful_scores.values())+list(harmless_scores.values()))
            print(f"{id}: 错误样本集打分：")
            print(f"  harmful_scores: {scores.get('harmful_scores', {})}")
            print(f"  harmless_scores: {scores.get('harmless_scores', {})}")
            print("-" * 50)
        feature_names = list(harmful_scores.keys()) + list(harmless_scores.keys())
        res = train_logistic_regression(data=data,feature_names=feature_names)  
        error_performance = res["performance"]  
        error_formula = res["formula"]
        error_scaler_params = res["scaler_params"]
        error_intercept = res["intercept"]
        error_weights = res["weights"]
        train_predictions = res["train_predictions"]
        error_feature_importance = res["feature_importance"]
        safe_append_markdown(RECORD_PATH, f"## 错误样本集评估结果\n**性能指标:** {error_performance}\n**逻辑回归公式:** {error_formula}\n**特征重要性:** {error_feature_importance}\n")
        for idx in range(len(dataset)):
            sample = dataset[idx]
            label = train_predictions[idx]
            ground_truth = sample['ground_truth']
            id = sample['id']
            # try:
            #     namespace = {}
            #     exec(current_code, {}, namespace)
            #     classify_func = namespace.get('classify_meme')
            #     label = classify_func(scores)
                
            # except Exception as e:
            #     print(f"代码执行出错 (ID={sample['id']}): {e}")
            #     current_code = code_fix(current_code,str(scores),e)
            #     namespace = {}
            #     exec(current_code, {}, namespace)
            #     label = namespace['classify_meme'](scores)
            # if isinstance(label, str):
            #     label = label.lower()
            # else:
            #     label = "review"
            
            # 记录错误类型
            if label==1 and ground_truth == 'harmless':
                if id not in pre1l0:  # 避免重复
                    pre1l0.append(id)
            if label==0 and ground_truth == 'harmful':
                if id not in pre0l1:  # 避免重复
                    pre0l1.append(id)
            label_str = 'harmful' if label==1 else 'harmless'
            print(f"{id}: 预测结果：")
            print(f"  Predict: {label}")
            print(f"  GroundTruth: {ground_truth}")
            print("-" * 50)
            
            predictions[sample["id"]] = {'label': label_str, "scores": scores}                
    except Exception as e:
        print(f"⚠️ 模型调用异常: {e}")
    
    return {
        "error_predictions": predictions,
        "pre1l0": pre1l0,
        "pre0l1": pre0l1,
        "error_performance":error_performance,
        "error_formula":error_formula,
        "error_scaler_params": error_scaler_params,
        "error_intercept":error_intercept,
        "error_weights":error_weights,
        "error_feature_importance":error_feature_importance
    }

def error_evaluator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误样本评估agent"""
    error_preds = state["error_predictions"]
    error_dataset_map = {s["id"]: s for s in state["fixed_error_dataset"]}
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    
    # 计算错误子集的错误
    error_errors = [
        sid for sid, pred in error_preds.items()
        if pred['label'].lower() != error_dataset_map[sid]["ground_truth"].lower()
    ]
    
    error_performance = state["error_performance"]
    error_accuracy,f1 = error_performance["accuracy"],error_performance["f1"]
    print(f"\n{'='*60}")
    print(f"错误样本集评估结果:")
    print(f"错误样本总数: {len(error_preds)}")
    print(f"错误样本集准确率: {error_accuracy:.2%},f1：{f1}")
    print(f"仍然错误的样本数: {len(error_errors)}")
    print(f"将无害模因误判为有害数量: {len(pre1l0)}个")
    print(f"将有害模因误判为无害数量: {len(pre0l1)}个")
    print(f"{'='*60}\n")
    
    # 更新错误子集最优模型
    best_error_accuracy = state.get("best_error_accuracy", 0.0)
    best_error_prompt = state.get("best_error_prompt", "")
    best_error_code = state.get("best_error_code", "")
    
    if error_accuracy >= best_error_accuracy:
        best_error_accuracy = error_accuracy
        best_error_prompt = state["current_prompt"]
        best_error_code = state["current_code"]
        print(f"✅ 更新错误样本集最佳模型，准确率: {error_accuracy:.2%}")
    else:
        print(f"⚠️ 错误样本集准确率未提升，当前: {error_accuracy:.2%}, 最佳: {best_error_accuracy:.2%}")
    
    # 判断是否达到阈值或最大迭代次数
    iteration = state.get("iteration", 0)  # 全局迭代
    error_iteration = state.get("error_iteration", 0)  # 错误聚焦迭代
    
    if error_accuracy >= error_focus_threshold or len(error_errors) == 0:
        print(f"✅ 错误样本集收敛，准确率: {error_accuracy:.2%} >= 阈值 {error_focus_threshold}")
        print(f"🔍 进入全局验证阶段")
        # 使用错误子集上的最佳模型
        return {
            "current_prompt": best_error_prompt,
            "current_code": best_error_code,
            "error_errors": error_errors,
            "error_accuracy": error_accuracy,
            "best_error_accuracy": best_error_accuracy,
            "best_error_prompt": best_error_prompt,
            "best_error_code": best_error_code,
            "phase": "global_verify",
            "error_iteration": 0,  # 重置错误迭代
        }
    elif iteration >= MAX_ITERATIONS:
        print(f"⚠️ 达到最大迭代次数 {MAX_ITERATIONS}，任务结束")
        return {
            "phase": "end"
        }
    else:
        print(f"🔄 错误样本集未收敛，继续优化")
        return {
            "error_errors": error_errors,
            "error_accuracy": error_accuracy,
            "best_error_accuracy": best_error_accuracy,
            "best_error_prompt": best_error_prompt,
            "best_error_code": best_error_code,
            "phase": "error_focus",
            "error_iteration": error_iteration + 1,  # 增加错误迭代
        }

def error_summarizer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """错误分析agent - 基于固定的错误样本集"""
    current_phase = state.get("phase", "error_focus")
    pre1l0 = state.get("pre1l0", [])
    pre0l1 = state.get("pre0l1", [])
    errors_to_analyze = []
    error_iteration = state.get("error_iteration", 0)
    if current_phase == "error_focus":
        if error_iteration == 0:
            # 第一次错误聚焦：使用全局错误（首次评估后的错误）
            errors_to_analyze = state.get("global_errors", [])
            feature_importance = state.get("feature_importance")
            print(f"第一次错误聚焦：分析全局错误 {len(errors_to_analyze)} 个")
        else:
            # 后续错误聚焦：只分析错误集中仍然出错的样本
            feature_importance = state.get("error_performance")
            errors_to_analyze = state.get("error_errors", [])
            print(f"第{error_iteration+1}次错误聚焦：分析错误集中仍错误的样本 {len(errors_to_analyze)} 个")
    # 如果没有要分析的错误
    if not errors_to_analyze:
        print("✅ 无错误样本需要分析")
        # 返回必要的空数据结构，保持向后兼容
        return {
            "error_summary": "No errors.",
            "pre1l0_summary": "",
            "pre0l1_summary": ""
        }
    # 使用 fixed_error_dataset
    dataset_map = {s["id"]: s for s in state["fixed_error_dataset"]}
    predictions = state.get("error_predictions", {})
    current_prompt = state["current_prompt"]
    current_code = state["current_code"]
    paper_text = state.get('paper_text', '')
    pre1l0_summary = []
    pre0l1_summary = []
    summary = []
    print(f"\n{'='*60}")
    print(f"开始错误分析，需要分析的错误样本数: {len(errors_to_analyze)}")
    print(f"{'='*60}\n")
    random_pre1l0 = random.sample(pre1l0, min(len(pre1l0),3))
    random_pre0l1 = random.sample(pre0l1, min(len(pre0l1),3))
    selected_sids = set(random_pre1l0) | set(random_pre0l1)
    safe_append_markdown(RECORD_PATH, f"## 错误分析:\n需要分析的错误样本数: {len(errors_to_analyze)}\n随机选择的预1l0样本ID: {random_pre1l0}\n随机选择的预0l1样本ID: {random_pre0l1}\n")
    for sid in errors_to_analyze:
        if sid not in predictions or sid not in dataset_map or sid not in selected_sids:
             continue
            
        sample = dataset_map[sid]
        pred_info = predictions[sid]
        
        context = (
            f"[ID: {sid}]\n"
            f"Meme Text: {sample['meme_text']}\n"
            f"Predicted: {pred_info['label']}, Ground_truth: {sample['ground_truth']}\n"
            f"Harmful Scores: {pred_info['scores'].get('harmful_scores', {})}\n"
            f"Harmless Scores: {pred_info['scores'].get('harmless_scores', {})}\n"
            f"Reasoning: {pred_info['scores'].get('reasoning', '')}"
        )
        
        system_prompt = f"""你是一位有害模因检测判别特征标准prompt的修正专家。请结合以下四类信息开展分析：
（1）参考标准（如权威文献或公认准则）;
（2）当前大模型打分使用的模因判别标准prompt；
（3）近期被错误判别的模因样本及其详细的维度打分结果；
（4）当前由数据分析得到的特征重要性排序以及重要性分数：
前提假设：请始终以 Ground Truth 的标注为绝对正确依据。
修正任务要求如下：
#原因分析：用一段话总结当前判别出错的可能原因，需结合上述四类信息进行综合推断。
#维度调整：评估是否需要在“有害”或“无害”判别体系中新增或完善打分维度。维度数量不固定，应根据实际判别需求灵活调整。
#标准优化：针对现有每个判别维度中的具体标准，逐项说明哪些内容需要：
--着重强调（如关键但被弱化的要素），
--补充（这点很重要，如果能增加一些新的维度，可以进一步用来进行分析，所以补充维度也很重要）
#请将你的完整回答以 JSON 格式返回，结构如下：
{{
  "判别出错原因分析": "…",
  "维度调整建议": {{
    ...(增加或完善详细描述)
  }},
  "各维度标准优化建议": {{
    "维度名称1": {{
      "着重强调"..: ,
      "补充": ..,
      "完善": "说明"
    }},
    "维度名称2": {{ ... }},
    ...
  }}
}}
"""
#--消除（如冗余、误导或与 Ground Truth 冲突的表述），
        response = llm_tool.call_llm(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": f"参考标准:{paper_text}\n\n当前大模型打分使用的模因判别标准prompt：{current_prompt}\n\n当前被错误判别打分结果:{context}\n\n,当前由数据分析得到的特征重要性排序以及重要性分数：{feature_importance}请给出你的总结：\n\n"}],
        )
        safe_append_markdown(RECORD_PATH, f"### 错误样本ID: {sid}\n**错误原因分析:** {response}\n")
        if sid in pre1l0:
            pre1l0_summary.append(f"模因id：{sid}\n错误原因分析：{response}")
        if sid in pre0l1:
            pre0l1_summary.append(f"模因id：{sid}\n错误原因分析：{response}")
        summary.append(f"模因id：{sid}\n错误原因分析：{response}")
        print(f"--- 模因id: {sid} ---")
        print(f"错误原因分析: {response[:200]}...")
        print("-" * 50)
    
    return {"error_summary": "\n\n".join(summary),"pre1l0_summary":"\n\n".join(pre1l0_summary),"pre0l1_summary":pre0l1_summary}

def prompt_improver_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """prompt改进agent"""
    pre1l0 = state.get('pre1l0', [])
    pre0l1 = state.get('pre0l1', [])
    pre1l0_memory = state.get("pre1l0_memory","")
    pre0l1_memory = state.get("pre0l1_memory","")
    pre1l0_summary = state.get('pre1l0_summary',"")
    pre0l1_summary = state.get('pre0l1_summary',"")
    old_prompt = state["current_prompt"]
    old_code = state["current_code"]
    error_summary = state["error_summary"]
    

    # 获取错误样本上下文
    pre1l0_context_list = []
    pre0l1_context_list = []
    context_list = []
    dataset_map = {s["id"]: s for s in state["fixed_error_dataset"]}
    predictions = state.get("error_predictions", {})
    feature_importance = ""
    if state["error_iteration"]==0:
        error_errors = state.get("global_errors", [])
        feature_importance = state.get("feature_importance")
    else:
        error_errors = state.get("error_errors", [])
        feature_importance = state.get("error_feature_importance")
    for sid in error_errors:
        if sid in predictions and sid in dataset_map:
            sample = dataset_map[sid]
            pred_info = predictions[sid]
            context = (
                f"[ID: {sid}]\n"
                f"Meme Text: {sample['meme_text']}\n"
                f"Predicted: {pred_info['label']}, Ground_truth: {sample['ground_truth']}\n"
                f"Harmful Scores: {pred_info['scores'].get('harmful_scores', {})}\n"
                f"Harmless Scores: {pred_info['scores'].get('harmless_scores', {})}"
            )
            if sid in pre1l0:
                pre1l0_context_list.append(context)
            if sid in pre0l1:
                pre0l1_context_list.append(context)
            context_list.append(context)
    
    combined_context = "\n\n".join(context_list) if context_list else "No specific errors to analyze."
    pre1l0_context = "\n\n".join(pre1l0_context_list) if pre1l0_context_list else "No specific errors to analyze."
    pre0l1_context = "\n\n".join(pre0l1_context_list) if pre0l1_context_list else "No specific errors to analyze."
    pre1l0_prompt = """你是一个专注于纠正将无害模因误判为有害的模因有害性判别经验记忆系统，旨在持续演进与优化判别知识库。请基于以下输入进行经验更新：已有历史经验（包括过往判别规则、误判案例及对应评分逻辑）和当前专家提出的新建议（可能包含与旧经验一致、冲突或全新场景的见解）。执行以下操作：融合共识，保留新旧一致的有效规则；修正冲突，当新建议与旧经验矛盾时，优先采纳经验证更可靠的判断依据；补充空白，对历史经验未覆盖的模因类型或边界情况，新增判别准则。输出应形成一套自洽、完整且可执行的更新后判别经验，用于指导后续有害/无害判定
注意，你需要根据经验以及新建议进行经验更新，经验格式以json格式保存，主要内容包括：
#原因分析：用一段话总结当前判别出错的可能原因，需结合上述四类信息进行综合推断。
#维度调整：评估是否需要在“有害”或“无害”判别体系中新增、删除或合并打分维度。维度数量不固定，应根据实际判别需求灵活调整。
#标准优化：针对现有每个判别维度中的具体标准，逐项说明哪些内容需要：
--着重强调（如关键但被弱化的要素），
--补充（如缺失的判别情形），
#请将你的完整回答以 JSON 格式返回，结构如下：
{
  "判别出错原因分析": "…",
  "维度调整建议": {
    ...(增加或完善等的详细描述)
  },
  "各维度标准优化建议": {
    "维度名称1": {
      "着重强调": ,
      "补充": ,
      "完善": "说明"
    },
    "维度名称2": { ... },
    ...
  }
}
"""
#--消除（如冗余、误导或与 Ground Truth 冲突的表述），
# --合并（如语义重叠或可泛化的条目）。
#--消除（如冗余、误导或与 Ground Truth 冲突的表述），
    pre0l1_prompt = """你是一个专注于纠正将有害模因误判为无害的模因有害性判别经验记忆系统，旨在持续演进与优化判别知识库。请基于以下输入进行经验更新：已有历史经验（包括过往判别规则、误判案例及对应评分逻辑）和当前专家提出的新建议（可能包含与旧经验一致、冲突或全新场景的见解）。执行以下操作：融合共识，保留新旧一致的有效规则；修正冲突，当新建议与旧经验矛盾时，优先采纳经验证更可靠的判断依据；补充空白，对历史经验未覆盖的模因类型或边界情况，新增判别准则。输出应形成一套自洽、完整且可执行的更新后判别经验，用于指导后续有害/无害判定
注意，你需要根据经验以及新建议进行经验更新，经验格式以json格式保存，主要内容包括：
#原因分析：用一段话总结当前判别出错的可能原因，需结合上述四类信息进行综合推断。
#维度调整：评估是否需要在“有害”或“无害”判别体系中新增、完善打分维度。维度数量不固定，应根据实际判别需求灵活调整。
#标准优化：针对现有每个判别维度中的具体标准，逐项说明哪些内容需要：
--着重强调（如关键但被弱化的要素），
--补充（如缺失的判别情形），
--合并（如语义重叠或可泛化的条目）。
#请将你的完整回答以 JSON 格式返回，结构如下：
{
  "判别出错原因分析": "…",
  "维度调整建议": {
    ...(增加或减少或合并的详细描述)
  },
  "各维度标准优化建议": {
    "维度名称1": {
      "着重强调": ,
      "补充": ,
      "合并建议": "说明"
    },
    "维度名称2": { ... },
    ...
  }
}
"""
    print(f"\n{'='*60}")
    print(f"记忆整合更新")
    print(f"{'='*60}\n")
    if pre1l0_context_list:
        user_msg = (
            f"已有历史经验:\n{pre1l0_memory}\n\n"
            f"各个专家的新错误分析:\n{pre1l0_summary}\n\n"
            f"具体错误样例上下文:\n{pre1l0_context}"
        )
        pre1l0_memory = llm_tool.call_llm(
            system_prompt=pre1l0_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        safe_append_markdown(RECORD_PATH, f"## pre1l0记忆更新\n**输出:**\n{pre1l0_memory}\n")
    if pre0l1_context_list:
        user_msg = (
            f"已有历史经验:\n{pre0l1_memory}\n\n"
            f"各个专家的新错误分析:\n{pre0l1_summary}\n\n"
            f"具体错误样例上下文:\n{pre0l1_context}"
        )
        pre0l1_memory = llm_tool.call_llm(
            system_prompt=pre0l1_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        safe_append_markdown(RECORD_PATH, f"## pre0l1记忆更新\n**输出:**\n{pre0l1_memory}\n")
    print(f"\n{'='*60}")
    print(f"开始prompt改进")
    print(f"{'='*60}\n")
    
    direct = f"注意：在当前错误样本集中，将无害模因误判为有害数量为 {len(pre1l0)}个，将有害模因误判为无害的数量为{len(pre0l1)}个，错误样本集准确率为 {state.get('error_accuracy', 0):.2%}。请据此调整你的判别策略，重点关注降低两类错误的不平衡性。"
    # 第二步：生成新的prompt
    system_prompt = """
You are a prompt engineer specializing in harmful meme detection.  
Your ONLY task is to **rewrite the original evaluation prompt** based on the following aspects.  
a.The revision suggestions from various experts;
-Specifically:
-1. Integrate revision suggestions from domain experts.
-2. If gaps are identified, **add new scoring dimensions** following the existing naming convention:
   - Harmful dimensions: `Hn` (e.g., H4, H5, ...)
   - Non-harmful dimensions: `Nm` (e.g., N4, N5, ...)
-3. For each new dimension, provide:
   - A clear definition
   - Concrete scoring criteria
b.The ranking of importance scores for the scoring features in the previous prompt after data analysis
c.Context of specific error examples
#CRITICAL RULES:
1. You MUST output ONLY the new English prompt text — nothing else.
2. DO NOT evaluate any meme, DO NOT generate JSON, DO NOT simulate scoring.
3. The new prompt must preserve the original output format: 
   {
     "harmful_scores": dict,
     "harmless_scores": dict,
     "reasoning": "string"
   }
4. Incorporate the updated criteria into the instructions.
5. Keep the tone authoritative, clear, and suitable for expert annotators.
Remember: You are writing an instruction for OTHER evaluators — not acting as one.
"""
    system_prompt = system_prompt + direct
    new_prompt = llm_tool.call_llm(
        system_prompt=system_prompt,
        messages=[{"role": "user", 
                   "content": f"""Original prompt:
#####\n{old_prompt}\n#####
Suggestions for rectifying the misjudgment of harmless memes as harmful:
#####\n{pre1l0_memory}\n#####
Suggestions for rectifying the misjudgment of harmful memes as harmless:
#####\n{pre0l1_memory}\n#####
ranking of importance scores:
#####\n{feature_importance}\n#####
Specific error example：
#####\n{combined_context}\n#####
Now, generate the NEW PROMPT (in English) that integrates the updated criteria while preserving the original structure and output format.
OUTPUT ONLY THE NEW PROMPT TEXT. NO EXPLANATION. NO JSON. NO EXAMPLE."""}],
    )
    # para = extract_dict_from_string(new_prompt)
    print(f"🆕 新生成的prompt:")
    print(new_prompt[:500] + "..." if len(new_prompt) > 500 else new_prompt)
    print("\n" + "-"*50 + "\n")
    safe_append_markdown(RECORD_PATH, f"## 新生成的Prompt:\n{new_prompt}\n")
#     # 第三步：生成新的代码
#     system_prompt = f"""
# 你是一位模因判别代码逻辑生成专家，请根据更新后的判别标准与逻辑，编写一个用于从评分结果生成最终判别的函数。
# 要求如下：
# 代码必须完整而且直接可执行，这点很重要；
# 函数名为 def classify_meme(scores)；函数实现应自包含，不调用外部方法或变量，即所有逻辑都写在classify_meme中，不要出现其他方法名与调用关系；
# 输入 scores 为符合原始格式的字典，具体格式：\n\n{para}
# 函数必须返回字符串 'harmless' 或 'harmful'；
# 仅使用 Python 标准库，不得引入任何第三方依赖；
# 仅输出该函数的完整代码，不包含任何注释、解释或其他额外文本。
# """
    
#     new_code = llm_tool.call_llm(
#         system_prompt=system_prompt,
#         messages=[{"role": "user", "content": f"原code:\n{old_code}\n\n更新后的判别标准与逻辑:\n{improvement_summary}\n\n请输出新的classify_meme方法:"}],
#     )
    
#     new_code = extract_code_from_markdown(new_code)
#     print(f"💻 新生成的代码:")
#     print(new_code)
#     print("\n" + "-"*50 + "\n")
    
    return {
        "current_code": state["current_code"],
        "current_prompt": new_prompt,
        "prompt_history": state.get("prompt_history", []) + [{
            'errors': list(state.get("error_errors", [])),
            'error_accuracy': state.get("error_accuracy", 0),
            'error_summary': error_summary,
            "new_prompt": new_prompt,
            "new_code": state["current_code"]
        }],
        "pre1l0": [],  # 重置误判统计
        "pre0l1": [],
        "pre1l0_memory":pre1l0_memory,
        "pre0l1_memory":pre0l1_memory
    }

def increment_iteration(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能增加迭代次数"""
    current_phase = state.get("phase", "global_eval")
    iteration = state.get("iteration", 0)
    error_iteration = state.get("error_iteration", 0)
    
    print(f"\n{'='*60}")
    
    if current_phase == "global_verify":
        # 全局验证后：增加全局迭代
        new_iteration = iteration + 1
        print(f"全局迭代次数: {new_iteration} (增加全局)")
    elif current_phase == "error_focus" and error_iteration == 0:
        # 第一次进入错误聚焦：不增加全局迭代
        print(f"进入错误聚焦，全局迭代保持: {iteration}")
        new_iteration = iteration
    else:
        # 错误聚焦内部：不增加全局迭代
        print(f"错误聚焦内部循环，全局迭代保持: {iteration}")
        new_iteration = iteration
    print(f"错误聚焦迭代: {error_iteration}")
    print(f"{'='*60}\n")
    return {"iteration": new_iteration}